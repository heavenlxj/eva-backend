#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @File    : weixin.py

import hashlib
import hmac
import json
import aiohttp
import asyncio
import requests
import time
import xml.etree.ElementTree as ET
from typing import Dict, Any, Optional
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession
from core.config.settings import settings
from repositories.userid_unionid_mapping import UseridUnionidMappingRepository
from repositories.wechat_service_user import WechatServiceUserRepository
from repositories.user_source import UserSourceRepository
from entity.weixin import WechatMiniLink, WechatErrorCode, ContentSecurityScene, ContentSecuritySuggest, ContentSecurityLabel, WechatContentSecurityResult
from package.redis.client import new_asyncio_redis_client


class WechatService:

    _service_access_token = None
    _service_token_expires_at = 0
    
    _miniprogram_access_token = None
    _miniprogram_token_expires_at = 0

    def __init__(self, db: AsyncSession):
        self.db = db
        self.wechat_repo = WechatServiceUserRepository(db)
        self.user_source_repo = UserSourceRepository(db)
        self.mapping_repo = UseridUnionidMappingRepository(db)

    @staticmethod
    def get_current_app_config():
        """获取当前配置的APPID和SECRET"""
        return settings.wechat.APPID, settings.wechat.SECRET

    @staticmethod
    def get_app_config(app_id):
        """根据app_id获取对应的secret"""
        miniprogram_settings = {
            settings.wechat.APPID: settings.wechat.SECRET
        }
        return miniprogram_settings.get(app_id)

    @staticmethod
    async def get_user_info(code: str, app_id: str = None):
        """Get user info with dynamic app_id support"""
        # 如果没有提供app_id，使用默认配置
        if not app_id:
            app_id = settings.wechat.APPID
            app_secret = settings.wechat.SECRET
        else:
            app_secret = WechatService.get_app_config(app_id)
            if not app_secret:
                logger.error(f"未找到app_id对应的secret: {app_id}")
                return None
        
        request_data = {
            'appid': app_id,
            'secret': app_secret,
            'grant_type': 'authorization_code',
            'js_code': code
        }

        async with aiohttp.ClientSession() as sess:
            async with sess.get("https://api.weixin.qq.com/sns/jscode2session", params=request_data) as response:
                text = await response.text()
                data = json.loads(text)
                logger.info("code2session resp: %s", data)
                if data.get('openid') is not None:
                    return data.get('openid')

        return None

    @staticmethod
    async def get_user_info_with_unionid(code: str, app_id: str = None):
        """Get user info including unionid with dynamic app_id support"""
        # 如果没有提供app_id，使用默认配置
        if not app_id:
            app_id = settings.wechat.APPID
            app_secret = settings.wechat.SECRET
        else:
            # 从app_config中获取对应的app_secret
            app_secret = WechatService.get_app_config(app_id)
            if not app_secret:
                logger.error(f"未找到app_id对应的secret: {app_id}")
                return None
        
        request_data = {
            'appid': app_id,
            'secret': app_secret,
            'grant_type': 'authorization_code',
            'js_code': code
        }

        async with aiohttp.ClientSession() as sess:
            async with sess.get("https://api.weixin.qq.com/sns/jscode2session", params=request_data) as response:
                text = await response.text()
                data = json.loads(text)
                logger.info(f"get_user_info_with_unionid resp: {data}")
                return data
        


    @staticmethod
    async def test_unionid_available(code: str) -> bool:
        """Test if unionid is available (check if open platform is enabled)"""
        appid, secret = WechatService.get_current_app_config()
        url = f"https://api.weixin.qq.com/sns/jscode2session?appid={appid}&secret={secret}&js_code={code}&grant_type=authorization_code"
        
        response = requests.get(url)
        data = response.json()
        
        # If unionid is returned, it means open platform is enabled
        return 'unionid' in data


    async def get_user_phone(self, code: str, app_id: str = None):
        """
        获取用户手机号（小程序）
        
        根据微信官方文档：https://developers.weixin.qq.com/miniprogram/dev/server/API/user-info/phone-number/api_getphonenumber.html
        
        Args:
            code: 手机号获取凭证，通过 wx.getPhoneNumber 获取
            app_id: 小程序 appid，如果为 None 则使用当前配置的 appid
            
        Returns:
            包含 phone_info 的字典，格式：
            {
                "errcode": 0,
                "errmsg": "ok",
                "phone_info": {
                    "phoneNumber": "用户绑定的手机号",
                    "purePhoneNumber": "没有区号的手机号",
                    "countryCode": "区号",
                    "watermark": {
                        "timestamp": 时间戳,
                        "appid": "小程序appid"
                    }
                }
            }
        """
        try:
            # 获取小程序配置
            if app_id:
                app_secret = WechatService.get_app_config(app_id)
                if not app_secret:
                    logger.error(f"未找到 app_id={app_id} 对应的 secret")
                    return {"errcode": -1, "errmsg": f"未找到 app_id={app_id} 对应的配置"}
            else:
                appid, app_secret = WechatService.get_current_app_config()
                app_id = appid
            
            # 获取小程序的 access_token
            access_token = await self._get_miniprogram_access_token(app_id, app_secret)
            
            # 调用获取手机号接口
            url = f"https://api.weixin.qq.com/wxa/business/getuserphonenumber?access_token={access_token}"
            payload = {"code": code}
            
            async with aiohttp.ClientSession() as sess:
                async with sess.post(url, json=payload) as response:
                    data = await response.json()
                    
                    if data.get("errcode") == 0:
                        logger.info(f"成功获取用户手机号: appid={app_id}")
                        return data
                    else:
                        errcode = data.get("errcode", -1)
                        errmsg = data.get("errmsg", "未知错误")
                        logger.error(f"获取用户手机号失败: errcode={errcode}, errmsg={errmsg}, appid={app_id}")
                        return data
                        
        except Exception as e:
            logger.error(f"获取用户手机号异常: {str(e)}, code={code}")
            return {"errcode": -1, "errmsg": f"获取手机号异常: {str(e)}"}

    @staticmethod
    def verify_signature(signature: str, timestamp: str, nonce: str) -> bool:
        """Verify WeChat signature"""
        token = settings.wechat.SERVICE_TOKEN
        # Sort token, timestamp, nonce in dictionary order
        temp_arr = [token, timestamp, nonce]
        temp_arr.sort()
        # Concatenate three parameter strings and perform sha1 encryption
        temp_str = ''.join(temp_arr)
        sha1 = hashlib.sha1()
        sha1.update(temp_str.encode('utf-8'))
        hash_code = sha1.hexdigest()
        # Developer can compare the encrypted string with signature to identify the request source
        return hash_code == signature

    @staticmethod
    async def get_access_token() -> str:
        """Get service account access_token"""
        if WechatService._service_access_token and time.time() < WechatService._service_token_expires_at - 300:
            return WechatService._service_access_token

        logger.info("Initiating service_access_token refresh via stable_token")

        url = "https://api.weixin.qq.com/cgi-bin/stable_token"
        payload = {
            "grant_type": "client_credential",
            "appid": settings.wechat.SERVICE_APPID,
            "secret": settings.wechat.SERVICE_SECRET,
            "force_refresh": False
        }

        async with aiohttp.ClientSession() as sess:
            async with sess.post(url, json=payload) as resp:
                data = await resp.json()

                if "access_token" not in data:
                    logger.error(f"Access_token acquisition failed: {data}")
                    raise Exception(f"Access_token acquisition failed: {data}")

                WechatService._service_access_token = data["access_token"]
                WechatService._service_token_expires_at = time.time() + data["expires_in"]
                logger.info(f"Stable token refreshed successfully. Expires in: {data['expires_in']}s")

                # Async menu refresh
                asyncio.create_task(WechatService._safe_create_menu(data["access_token"]))
                return WechatService._service_access_token

    @staticmethod
    async def _safe_create_menu(token: str):
        """Asynchronous menu creation """
        try:
            async with aiohttp.ClientSession() as sess:
                # 使用动态菜单配置
                menu_config = WechatMiniLink.get_menu_config()
                # Manually serialize and specify ensure_ascii=False to handle non-ASCII characters
                json_data = json.dumps(menu_config, ensure_ascii=False)
                async with sess.post(
                    f"https://api.weixin.qq.com/cgi-bin/menu/create?access_token={token}",
                    data=json_data.encode('utf-8'),
                    headers={'Content-Type': 'application/json; charset=utf-8'},
                    timeout=10
                ) as response:
                    result = await response.json()
                    if result.get('errcode') == 0:
                        logger.info("Background menu created successfully")
                    else:
                        logger.warning(f"Background menu creation failed: {result}")
        except Exception as e:
            logger.error(f"Background menu creation exception: {str(e)}")

    @staticmethod
    def parse_xml(xml_data: str) -> Dict[str, Any]:
        """Parse WeChat XML data"""
        root = ET.fromstring(xml_data)
        result = {}
        for child in root:
            result[child.tag] = child.text
        return result

    async def handle_follow_event(self, event_data: Dict[str, Any]) -> str:
        """Handle follow event"""
        service_openid = event_data.get('FromUserName')
        event_key = event_data.get('EventKey', '')  # 获取EventKey，格式：qrscene_xxx
        
        logger.info(f"User follow event - service openid: {service_openid}, event_key: {event_key}")
        
        # Save to database
        await self.save_service_openid(service_openid)
        
        # Try to get service account user's unionid
        await self.try_get_service_user_unionid(service_openid)
        
        logger.info(f"User follow event - service openid: {service_openid} processed")
        
        # 解析设备信息（如果有关注来源的二维码）
        device_info = None
        if event_key and event_key.startswith('qrscene_'):
            # 提取scene参数（去掉qrscene_前缀）
            scene = event_key.replace('qrscene_', '')
            logger.info(f"User followed via QR code with scene: {scene}")
            
            # 解析scene参数获取设备信息（格式：deviceType_version）
            # 注意：FULL_DUPLEX和HALF_DUPLEX包含下划线，需要特殊处理
            # scene格式：FULL_DUPLEX_v1 或 HALF_DUPLEX_v1
            device_info = None
            if scene.startswith('FULL_DUPLEX_'):
                # FULL_DUPLEX_v1 -> 提取版本号
                version = scene.replace('FULL_DUPLEX_', '', 1) if len(scene) > 12 else 'v1'
                device_info = {
                    "deviceType": "FULL_DUPLEX",
                    "version": version
                }
            elif scene.startswith('HALF_DUPLEX_'):
                # HALF_DUPLEX_v1 -> 提取版本号
                version = scene.replace('HALF_DUPLEX_', '', 1) if len(scene) > 12 else 'v1'
                device_info = {
                    "deviceType": "HALF_DUPLEX",
                    "version": version
                }
            else:
                # 兼容旧格式（如果还有的话）
                parts = scene.split('_')
                if len(parts) >= 3:
                    # 尝试解析 FULL, DUPLEX, version 格式
                    if parts[0] == 'FULL' and parts[1] == 'DUPLEX':
                        device_info = {
                            "deviceType": "FULL_DUPLEX",
                            "version": parts[2] if len(parts) > 2 else 'v1'
                        }
                    elif parts[0] == 'HALF' and parts[1] == 'DUPLEX':
                        device_info = {
                            "deviceType": "HALF_DUPLEX",
                            "version": parts[2] if len(parts) > 2 else 'v1'
                        }
            
            if device_info:
                logger.info(f"Device info from scene: {device_info}")
        
        # 统一发送欢迎消息（如果有设备信息，会在小程序链接中带上）
        await self.send_welcome_message(service_openid, device_info=device_info)
        
        return "success"

    async def handle_unfollow_event(self, event_data: Dict[str, Any]) -> str:
        """Handle unfollow event"""
        service_openid = event_data.get('FromUserName')
        logger.info(f"User unfollow event - service openid: {service_openid}")
        try:
            await self.wechat_repo.soft_delete_by_service_openid(service_openid)
            logger.info(f"Successfully soft-deleted service openid: {service_openid}")
        except Exception as e:
            logger.error(f"Failed to soft-delete service openid: {e}")
            # Even if db operation fails, we should return success to WeChat server
        return "success"

    async def save_service_openid(self, service_openid: str, unionid: Optional[str] = None):
        """
        Save service account openid to database
        使用 SELECT FOR UPDATE 在一个事务中完成检查和创建，防止并发重复创建
        """
        from repositories.model.wechat_service_user import WechatServiceUser
        
        try:
            # 在一个事务中完成检查和创建，使用 SELECT FOR UPDATE 防止并发问题
            async with self.db.begin():
                # 使用 SELECT FOR UPDATE 锁定可能存在的记录
                existing_user = await self.wechat_repo.get_by_service_openid_with_lock(service_openid)
                
                if existing_user:
                    # 如果存在，更新 unionid（如果需要）
                    if unionid and not existing_user.unionid:
                        existing_user.unionid = unionid
                    logger.info(f"Service openid already exists: {service_openid} (id: {existing_user.id})")
                    return existing_user
                
                # 不存在，创建新记录（在同一事务中）
                wechat_service_user = WechatServiceUser(
                    service_openid=service_openid,
                    unionid=unionid
                )
                self.db.add(wechat_service_user)
                await self.db.flush()  # 刷新以获取生成的 id
                logger.info(f"Successfully saved service openid: {service_openid} (id: {wechat_service_user.id})")
                return wechat_service_user
            
        except Exception as e:
            logger.error(f"Failed to save openid: {e}")
            raise

    async def try_get_service_user_unionid(self, service_openid: str):
        """Try to get service account user's unionid"""
        try:
            # Get user info via service account access_token
            access_token = await WechatService.get_access_token()
            url = f"https://api.weixin.qq.com/cgi-bin/user/info?access_token={access_token}&openid={service_openid}&lang=zh_CN"
            
            response = requests.get(url)
            result = response.json()
            logger.info(f"Get service user unionid resp: {result}")
            
            if result.get('unionid'):
                unionid = result.get('unionid')
                logger.info(f"Got service user unionid: {service_openid} -> {unionid}")
                
                # Update unionid in database
                await self.wechat_repo.update_unionid(service_openid, unionid)
            else:
                logger.error(f"Failed to get service user unionid: {result}")
                
        except Exception as e:
            logger.error(f"Failed to get service user info: {e}")

    async def get_service_openid_by_user_id_via_unionid(self, user_id: str) -> Optional[str]:
        """Get service account openid via user_id and unionid (recommended method)"""
        try:
            # 1. 通过userid_unionid_mapping表获取用户的unionid
            mapping = await self.mapping_repo.get_by_user_id(user_id)
            if not mapping or not mapping.unionid:
                logger.info(f"User has no unionid in mapping table: {user_id}")
                return None
            
            # 2. 通过unionid获取service account openid
            wechat_user = await self.wechat_repo.get_by_unionid(mapping.unionid)
            if wechat_user:
                logger.info(f"Found service openid via unionid: {user_id} -> {wechat_user.service_openid}")
                return wechat_user.service_openid
            else:
                logger.info(f"No corresponding service account user found: unionid={mapping.unionid}")
                return None
                
        except Exception as e:
            logger.error(f"Failed to query service openid via unionid: {e}")
            return None

    async def get_user_id_by_service_openid(self, service_openid: str) -> Optional[str]:
        """Get user_id via service account openid"""
        try:
            wechat_user = await self.wechat_repo.get_by_service_openid(service_openid)
            return wechat_user.user_id if wechat_user else None
            
        except Exception as e:
            logger.error(f"Failed to query user_id: {e}")
            return None

    async def get_service_openid_by_unionid(self, unionid: str) -> Optional[str]:
        """Get service account openid via unionid"""
        try:
            wechat_user = await self.wechat_repo.get_by_unionid(unionid)
            return wechat_user.service_openid if wechat_user else None
            
        except Exception as e:
            logger.error(f"Failed to query openid: {e}")
            return None

    async def send_welcome_message(self, service_openid: str, device_info: Optional[Dict[str, str]] = None):
        """Send welcome message
        
        Args:
            service_openid: 用户服务号openid
            device_info: 可选的设备信息，格式：{"deviceType": "fullDuplex", "version": "v1"}
        """
        try:
            access_token = await WechatService.get_access_token()

            url = f"https://api.weixin.qq.com/cgi-bin/message/custom/send?access_token={access_token}"
            
            headers = {'Content-Type': 'application/json; charset=utf-8'}
            data = {
                "touser": service_openid,
                "msgtype": "text",
                "text": {
                    "content": self._generate_welcome_content(device_info=device_info)
                }
            }
            response = requests.post(url, headers=headers, data=bytes(json.dumps(data, ensure_ascii=False), encoding='utf-8'))
            result = response.json()
            
            if result.get('errcode') == 0:
                logger.info(f"Welcome message sent successfully: {service_openid}, device_info: {device_info}")
            else:
                logger.error(f"Failed to send welcome message: {result}")
                
        except Exception as e:
            logger.error(f"Failed to send welcome message: {e}")


    @staticmethod
    async def generate_wechat_qrcode_with_scene(scene_str: str, is_permanent: bool = False) -> str:
        """
        生成带scene参数的服务号二维码
        
        Args:
            scene_str: 场景值字符串（最大64字符），例如 "fullDuplex_v1"
            is_permanent: 是否生成永久二维码，默认False（临时二维码，30天有效期）
        
        Returns:
            二维码图片URL
        """
        try:
            # 验证scene_str长度
            if len(scene_str) > 64:
                raise ValueError("scene_str长度不能超过64字符")
            
            # 获取access_token
            access_token = await WechatService.get_access_token()
            
            # 选择二维码类型
            action_name = "QR_LIMIT_STR_SCENE" if is_permanent else "QR_STR_SCENE"
            
            # 构建请求参数
            request_data = {
                "action_name": action_name,
                "action_info": {
                    "scene": {
                        "scene_str": scene_str
                    }
                }
            }
            
            # 如果是临时二维码，设置有效期（最长30天）
            if not is_permanent:
                request_data["expire_seconds"] = 2592000  # 30天
            
            # 调用微信接口生成二维码
            url = f"https://api.weixin.qq.com/cgi-bin/qrcode/create?access_token={access_token}"
            response = requests.post(url, json=request_data)
            result = response.json()
            
            if result.get('errcode') and result.get('errcode') != 0:
                error_msg = result.get('errmsg', '未知错误')
                logger.error(f"生成二维码失败: {error_msg}")
                raise Exception(f"生成二维码失败: {error_msg}")
            
            ticket = result.get('ticket')
            if not ticket:
                raise Exception("未获取到二维码ticket")
            
            # 生成二维码图片URL（ticket需要URL编码）
            from urllib.parse import quote
            encoded_ticket = quote(ticket)
            qr_code_url = f"https://mp.weixin.qq.com/cgi-bin/showqrcode?ticket={encoded_ticket}"
            
            logger.info(f"二维码生成成功: scene={scene_str}, url={qr_code_url}")
            return qr_code_url
            
        except Exception as e:
            logger.error(f"生成服务号二维码失败: {e}", exc_info=True)
            raise

    def _generate_message_hash(self, service_openid: str, template_id: str, data: Dict[str, Any], url: Optional[str] = None, miniprogram: Optional[Dict] = None) -> str:
        """Generate a unique hash for the message to detect duplicates"""
        # 构建消息的唯一标识：openid + template_id + data内容 + url/miniprogram
        message_content = {
            "openid": service_openid,
            "template_id": template_id,
            "data": data,
            "url": url,
            "miniprogram": miniprogram
        }
        # 使用 JSON 序列化并生成 MD5 哈希
        message_str = json.dumps(message_content, sort_keys=True, ensure_ascii=False)
        return hashlib.md5(message_str.encode('utf-8')).hexdigest()
    
    async def _check_duplicate_message(self, message_hash: str, service_openid: str) -> bool:
        """Check if the same message was sent recently (within 60 seconds)"""
        try:
            redis_key = f"wechat:template_msg:{service_openid}:{message_hash}"
            async with new_asyncio_redis_client() as redis_client:
                exists = await redis_client.exists(redis_key)
                if exists:
                    return True  # 消息已存在，表示最近发送过
                # 设置60秒过期时间
                await redis_client.setex(redis_key, 60, "1")
                return False  # 消息不存在，可以发送
        except Exception as e:
            logger.warning(f"Failed to check duplicate message in Redis: {e}, will proceed with sending")
            return False  # Redis 出错时允许发送，避免影响正常功能
    
    async def send_template_message(self, service_openid: str, template_id: str, data: Dict[str, Any], url: Optional[str] = None, miniprogram: Optional[Dict] = None):
        """Send template message
        
        Args:
            service_openid: Recipient openid
            template_id: Template ID
            data: Template data
            url: Click to jump to web page link (optional)
            miniprogram: Jump to miniprogram info (optional)
                {
                    "appid": "miniprogram appid",
                    "pagepath": "pages/index/index"
                }
        """
        try:
            # 生成消息哈希并检查是否重复
            message_hash = self._generate_message_hash(service_openid, template_id, data, url, miniprogram)
            is_duplicate = await self._check_duplicate_message(message_hash, service_openid)
            
            if is_duplicate:
                logger.warning(
                    f"Skipping duplicate template message to avoid rate limiting: "
                    f"service_openid={service_openid}, template_id={template_id}, "
                    f"message_hash={message_hash[:8]}..."
                )
                return False  # 返回 False 表示未发送（因为重复）
            
            access_token = await WechatService.get_access_token()
            api_url = f"https://api.weixin.qq.com/cgi-bin/message/template/send?access_token={access_token}"
            
            message = {
                "touser": service_openid,
                "template_id": template_id,
                "data": data
            }
            
            # If miniprogram jump info is provided
            if miniprogram:
                message["miniprogram"] = miniprogram
            # If web page link is provided
            elif url:
                message["url"] = url
            
            response = requests.post(api_url, json=message)
            result = response.json()
            
            if result.get('errcode') == 0:
                logger.info(f"Template message sent successfully: {service_openid}")
                return True
            else:
                errcode = result.get('errcode')
                errmsg = result.get('errmsg', '')
                
                # 处理40258错误码（二级限流）
                if errcode == WechatErrorCode.RATE_LIMIT_SECOND_LEVEL:
                    logger.warning(
                        f"Template message rate limited ({WechatErrorCode.RATE_LIMIT_SECOND_LEVEL}): service_openid={service_openid}, "
                        f"template_id={template_id}, errmsg={errmsg}. "
                        f"This should be prevented by duplicate check, message_hash={message_hash[:8]}..."
                    )
                elif errcode == WechatErrorCode.USER_REFUSE_MESSAGE:
                    logger.warning(f"User refused to accept template message: {service_openid}, errmsg: {errmsg}")
                elif errcode == WechatErrorCode.REQUIRE_SUBSCRIBE:
                    logger.warning(
                        f"User not subscribed to official account ({WechatErrorCode.REQUIRE_SUBSCRIBE}): "
                        f"service_openid={service_openid}, template_id={template_id}, errmsg={errmsg}"
                    )
                else:
                    logger.error(f"Failed to send template message: {result}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to send template message: {e}")
            return False

    async def send_template_message_by_user_id(self, user_id: str, template_id: str, data: Dict[str, Any], url: Optional[str] = None, miniprogram: Optional[Dict] = None):
        """Send template message via user_id (recommended)
        
        Args:
            user_id: User ID
            template_id: Template ID
            data: Template data
            url: Click to jump to web page link (optional)
            miniprogram: Jump to miniprogram info (optional)
                {
                    "appid": "miniprogram appid",
                    "pagepath": "pages/index/index"
                }
        """
        try:
            # Get service account openid via user_id
            service_openid = await self.get_service_openid_by_user_id_via_unionid(user_id)
            if not service_openid:
                logger.warning(f"No corresponding service openid found for user: {user_id}")
                return False
            
            # Send template message
            return await self.send_template_message(service_openid, template_id, data, url, miniprogram)
            
        except Exception as e:
            logger.error(f"Failed to send template message via user_id: {e}")
            return False

    # async def send_template_message_by_child_id(self, child_id: str, template_id: str, data: Dict[str, Any], url: Optional[str] = None, miniprogram: Optional[Dict] = None):
    #     """Send template message via child_id

    #     Args:
    #         child_id: Child ID
    #         template_id: Template ID
    #         data: Template data
    #         url: Click to jump to web page link (optional)
    #         miniprogram: Jump to miniprogram info (optional)
    #             {
    #                 "appid": "miniprogram appid",
    #                 "pagepath": "pages/index/index"
    #             }
    #     """
    #     try:
    #         # Get user_id via child_id from whale API
    #         user_children = await self.user_child_repo.get_with_child_id(child_id)
    #         if not user_children:
    #             logger.warning(f"No corresponding user_id found for child: {child_id}")
    #             return False

    #         # Try to send template message to all users associated with this child
    #         success_count = 0
    #         total_count = len(user_children)

    #         for user_child in user_children:
    #             try:
    #                 result = await self.send_template_message_by_user_id(user_child.user_id, template_id, data, url, miniprogram)
    #                 if result:
    #                     success_count += 1
    #                     logger.info(f"Successfully sent template message to user {user_child.user_id} for child {child_id}")
    #                 else:
    #                     logger.warning(f"Failed to send template message to user {user_child.user_id} for child {child_id}")
    #             except Exception as e:
    #                 logger.error(f"Error sending template message to user {user_child.user_id} for child {child_id}: {e}")

    #         logger.info(f"Template message sending completed for child {child_id}: {success_count}/{total_count} successful")
    #         return success_count > 0  # Return True if at least one message was sent successfully

    #     except Exception as e:
    #         logger.error(f"Failed to send template message via child_id: {e}")
    #         return False

    def _generate_welcome_content(self, device_info: Optional[Dict[str, str]] = None) -> str:
        """生成欢迎消息内容
        
        Args:
            device_info: 可选的设备信息，格式：{"deviceType": "fullDuplex", "version": "v1"}
        """
        content = "👋 亲爱的家长，欢迎使用可豆陪陪！\n"
        current_appid, _ = WechatService.get_current_app_config()
        for config in WechatMiniLink.FIRST_MINI_LINK:
            full_query = config['query']
            
            # 如果是"进入小程序"链接且有设备信息，在query中加上设备信息参数
            if config['url_text'] == '进入小程序' and device_info:
                device_params = f"deviceType={device_info.get('deviceType', '')}&version={device_info.get('version', 'v1')}"
                if full_query:
                    full_query = f"{full_query}&{device_params}"
                else:
                    full_query = device_params
            
            # 构建小程序路径，如果有query参数则加上
            if full_query:
                miniprogram_path = f"{config['path']}?{full_query}"
            else:
                miniprogram_path = config['path']
            
            content += f"{config['desc']}" \
                       f"<a href=\"https://kidopally.cn/zh/manual\" data-miniprogram-appid={current_appid} " \
                       f"data-miniprogram-path=\"{miniprogram_path}\">{config['url_text']}</a>\n"
        return content.strip()


    async def handle_click_event(self, event_data: Dict[str, Any]) -> str:
        event_key = event_data.get('EventKey')
        service_openid = event_data.get('FromUserName')

        reply_config = next(
            (c for c in WechatMiniLink.AUTO_REPLY_CONFIG if c["key"] == event_key),
            None
        )

        if reply_config:
            await self._send_event_response(service_openid, reply_config)

        return "success"

    async def _send_event_response(self, openid: str, config: Dict):
        try:
            access_token = await self.get_access_token()
            async with aiohttp.ClientSession() as session:
                await session.post(
                    f"https://api.weixin.qq.com/cgi-bin/message/custom/send?access_token={access_token}",
                    data=json.dumps({
                        "touser": openid,
                        "msgtype": config["type"],
                        "text": {"content": config["content"]}
                    }, ensure_ascii=False).encode('utf-8'),
                    headers={'Content-Type': 'application/json; charset=utf-8'}
                )
        except Exception as e:
            logger.error(f"Failed to send event response: {e}")

    async def handle_text_message(self, message_data: Dict[str, Any]) -> str:
        """Handle user text messages and return auto reply"""
        from_user = message_data.get('FromUserName')
        content = message_data.get('Content', '')
        
        logger.info(f"Received text message from {from_user}: {content}")
        await self.send_auto_reply_message(from_user)
        
        return "success"

    async def send_auto_reply_message(self, service_openid: str):
        """Send auto reply message"""
        try:
            access_token = await WechatService.get_access_token()
            url = f"https://api.weixin.qq.com/cgi-bin/message/custom/send?access_token={access_token}"
            
            data = {
                "touser": service_openid,
                "msgtype": "text",
                "text": {"content": self._generate_auto_reply_content()}
            }
            
            response = requests.post(
                url, 
                headers={'Content-Type': 'application/json; charset=utf-8'},
                data=bytes(json.dumps(data, ensure_ascii=False), encoding='utf-8')
            )
            result = response.json()
            
            if result.get('errcode') == 0:
                logger.info(f"Auto reply message sent successfully: {service_openid}")
            else:
                logger.error(f"Failed to send auto reply message: {result}")
                
        except Exception as e:
            logger.error(f"Failed to send auto reply message: {e}")

    def _generate_auto_reply_content(self) -> str:
        """Generate auto reply content"""
        return WechatMiniLink.GENERAL_AUTO_REPLY
        
    async def check_content_security(
        self, 
        user_id: str, 
        content: str, 
        scene: int = ContentSecurityScene.COMMENT,
        title: Optional[str] = None,
        nickname: Optional[str] = None,
        signature: Optional[str] = None,
        source: str = "mini_program"
    ) -> WechatContentSecurityResult:
        try:
            if settings.wechat.DISABLE_WECHAT_CONTENT_SECURITY_CHECK:
                logger.warning("WeChat content security check is disabled")
                return WechatContentSecurityResult(
                    safe=True,
                    suggest=ContentSecuritySuggest.PASS,
                    label=ContentSecurityLabel.NORMAL,
                    detail=[],
                    trace_id=""
                )
            
            user_source = await self.user_source_repo.get_with_user_id(user_id=user_id, source=source)
            if not user_source or not user_source.openid:
                logger.error(f"User openid not found: {user_id}")
                raise Exception(f"User openid not found: {user_id}")
            
            openid = user_source.openid
            logger.info(f"Content security check - user_id: {user_id}, openid: {openid}, content length: {len(content)}")
            app_id, app_secret = WechatService.get_current_app_config()
            access_token = await self._get_miniprogram_access_token(app_id, app_secret)

            url = f"https://api.weixin.qq.com/wxa/msg_sec_check?access_token={access_token}"
            
            payload = {
                "openid": openid,
                "scene": scene,
                "version": 2,
                "content": content[:2500]
            }
            
            if title:
                payload["title"] = title
            if nickname:
                payload["nickname"] = nickname
            if signature and scene == ContentSecurityScene.PROFILE:
                payload["signature"] = signature
            
            async with aiohttp.ClientSession() as sess:
                json_data = json.dumps(payload, ensure_ascii=False)
                async with sess.post(
                    url,
                    data=json_data.encode('utf-8'),
                    headers={'Content-Type': 'application/json; charset=utf-8'}
                ) as response:
                    result = await response.json()
                    logger.info(f"Content security check result: {result}")
                    
                    if result.get('errcode') == 0:
                        suggest = result.get('result', {}).get('suggest', 'review')
                        label = result.get('result', {}).get('label', 21000)
                        detail = result.get('detail', [])
                        trace_id = result.get('trace_id', '')
                        
                        return WechatContentSecurityResult(
                            safe=suggest == ContentSecuritySuggest.PASS,
                            suggest=suggest,
                            label=label,
                            detail=detail,
                            trace_id=trace_id
                        )
                    else:
                        logger.error(f"Content security check API error: {result}")
                        raise Exception(f"Content security check failed: {result.get('errmsg', 'Unknown error')}")
                        
        except Exception as e:
            logger.error(f"Content security check failed: {e}")
            raise

    async def _get_miniprogram_access_token(self, app_id: str, app_secret: str) -> str:
        if WechatService._miniprogram_access_token and time.time() < WechatService._miniprogram_token_expires_at - 300:
            logger.debug(f"Using cached miniprogram access_token, expires in {int(WechatService._miniprogram_token_expires_at - time.time())}s")
            return WechatService._miniprogram_access_token
        
        logger.info(f"Refreshing miniprogram access_token for appid: {app_id} via stable_token")
        
        # 使用稳定版 access_token 接口（推荐）
        # 参考文档：https://developers.weixin.qq.com/miniprogram/dev/api-backend/open-api/access-token/getStableAccessToken.html
        url = "https://api.weixin.qq.com/cgi-bin/stable_token"
        payload = {
            "grant_type": "client_credential",
            "appid": app_id,
            "secret": app_secret,
            "force_refresh": False  # 不强制刷新，使用缓存的 token
        }
        
        async with aiohttp.ClientSession() as sess:
            async with sess.post(url, json=payload) as response:
                data = await response.json()
                
                if "access_token" not in data:
                    errcode = data.get('errcode', -1)
                    errmsg = data.get('errmsg', '未知错误')
                    logger.error(f"Failed to get miniprogram access_token: errcode={errcode}, errmsg={errmsg}")
                    raise Exception(f"Failed to get miniprogram access_token: errcode={errcode}, errmsg={errmsg}")
                
                WechatService._miniprogram_access_token = data["access_token"]
                WechatService._miniprogram_token_expires_at = time.time() + data.get("expires_in", 7200)
                
                logger.info(f"Miniprogram access_token refreshed successfully via stable_token. Expires in: {data.get('expires_in', 7200)}s")
                
                return WechatService._miniprogram_access_token

