#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @File    : payment.py

import uuid
import logging
import os
from pathlib import Path
from typing import Optional
from loguru import logger
from wechatpayv3 import WeChatPay, WeChatPayType
from core.config.settings import settings
from repositories.order import OrderRepository
from repositories.model.order import Order
from repositories.user_source import UserSourceRepository
from services.virtual_currency import VirtualCurrencyService

# 初始化微信支付客户端
_wxpay_client: Optional[WeChatPay] = None


def _resolve_path(path: str) -> str:
    """解析文件路径，如果是相对路径则基于项目根目录解析"""
    if os.path.isabs(path):
        return path
    
    # 获取项目根目录（假设项目根目录在 src 的上一级）
    current_file = Path(__file__).resolve()
    # src/services/payment.py -> 项目根目录
    project_root = current_file.parent.parent.parent
    resolved_path = (project_root / path).resolve()
    return str(resolved_path)


def get_wxpay_client(require_cert: bool = False) -> WeChatPay:
    """
    获取微信支付客户端（单例）
    
    Args:
        require_cert: 是否需要平台证书（处理回调时需要，创建订单时不需要）
    """
    global _wxpay_client
    
    # 如果已经初始化，直接返回（单例模式）
    # 注意：如果之前初始化时没有证书，现在需要证书，可能需要重新初始化
    # 但为了保持单例，我们假设一旦初始化成功就可以使用
    if _wxpay_client is not None:
        return _wxpay_client
    
    # 读取私钥
    private_key_path = settings.wechat_pay.PRIVATE_KEY_PATH
    resolved_private_key_path = _resolve_path(private_key_path)
    resolved_public_key_path = _resolve_path(settings.wechat_pay.PUBLIC_KEY_PATH)

    logger.info(f"resolved_private_key_path: {resolved_private_key_path}")
    logger.info(f"resolved_public_key_path: {resolved_public_key_path}")
    
    try:
        with open(resolved_private_key_path, 'r') as f:
                private_key = f.read()
    except Exception as e:
        error_msg = f"读取微信支付私钥文件失败: {resolved_private_key_path}, 错误: {str(e)}"
        logger.error(error_msg)
        raise

    try:
        with open(resolved_public_key_path, 'r') as f:
            public_key = f.read()
    except Exception as e:
        error_msg = f"读取微信支付公钥文件失败: {resolved_public_key_path}, 错误: {str(e)}"
        logger.error(error_msg)
        raise
    
    # 解析证书目录路径
    cert_dir = None
    if settings.wechat_pay.CERT_DIR:
        cert_dir = _resolve_path(settings.wechat_pay.CERT_DIR)
        # 确保证书目录存在
        os.makedirs(cert_dir, exist_ok=True)
    
    try:
        # 尝试初始化客户端，SDK 会自动下载证书（如果证书目录为空）
        _wxpay_client = WeChatPay(
            wechatpay_type=WeChatPayType.NATIVE,
            mchid=settings.wechat_pay.MCHID,
            private_key=private_key,
            cert_serial_no=settings.wechat_pay.CERT_SERIAL_NO,
            apiv3_key=settings.wechat_pay.APIV3_KEY,
            appid=settings.wechat.APPID,
            notify_url=settings.wechat_pay.NOTIFY_URL,
            cert_dir=cert_dir,
            logger=logging.getLogger("wechatpay"),
            partner_mode=settings.wechat_pay.PARTNER_MODE,
            proxy=None,
            public_key=public_key,
            public_key_id=settings.wechat_pay.PUBLICK_KEY_ID
        )
        logger.info(f"微信支付客户端初始化成功，证书目录: {cert_dir}")
    except Exception as e:
        error_msg = str(e)
        logger.error(f"微信支付客户端初始化失败: {error_msg}")
        raise
 

    
    return _wxpay_client


class PaymentService:
    def __init__(self, db):
        self.db = db
        self.order_repo = OrderRepository(db)
        self.user_source_repo = UserSourceRepository(db)
        self.virtual_currency_service = VirtualCurrencyService(db)

    async def create_order(
        self, 
        user_id: str, 
        amount: int, 
        pay_type: str, 
        payer: Optional[str] = None,
        payment_method: str = "wechat_pay",
        is_recharge: bool = False
    ) -> dict:
        """创建支付订单"""
        logger.info(f"开始创建订单: user_id={user_id}, amount={amount}, pay_type={pay_type}, "
                    f"payer={payer}, payment_method={payment_method}, is_recharge={is_recharge}")

        # 生成订单号
        order_id = uuid.uuid1().hex
        logger.info(f"生成订单号: {order_id}")
        
        # 根据支付类型确定 WeChatPayType
        if pay_type == "wechat_h5":
            wxpay_type = WeChatPayType.H5
            base_description = "小程序H5支付"
        elif pay_type == 'jsapi':
            wxpay_type = WeChatPayType.JSAPI
            base_description = "小程序JSAPI支付"
        else:
            wxpay_type = WeChatPayType.NATIVE
            base_description = "小程序Native支付"
        
        # 根据是否为充值订单，设置不同的订单描述
        if is_recharge:
            description = f"充值虚拟币 {amount / 10:.1f} 代币"
        else:
            description = base_description
        
        # 准备支付者信息（JSAPI需要）
        payer_dict = None
        if pay_type == 'jsapi':
            # 如果没有传递 openid，尝试从 user_source 表中获取
            if not payer:
                user_source = await self.user_source_repo.get_with_user_id(user_id, 'mini_program')
                if user_source and user_source.openid:
                    payer = user_source.openid
                    logger.info(f"从 user_source 获取 openid: {payer}")
            
            if payer:
                payer_dict = {'openid': payer}
            else:
                logger.warning(f"JSAPI 支付需要 openid，但未找到用户 {user_id} 的 openid")
                raise ValueError("JSAPI 支付需要 openid，请确保用户已登录小程序")
        
        # 如果是虚拟币支付，直接创建订单并扣减虚拟币
        if payment_method == "virtual_currency":
            logger.info(f"使用虚拟币支付: order_id={order_id}, user_id={user_id}")
            return await self._create_virtual_currency_order(
                user_id=user_id,
                amount=amount,
                order_id=order_id,
                is_recharge=is_recharge
            )
        
        # 微信支付：调用微信支付接口（创建订单不需要证书）
        logger.info(f"调用微信支付接口: order_id={order_id}, description={description}, amount={amount}")
        wxpay = get_wxpay_client(require_cert=False)
        code, message = wxpay.pay(
            description=description,
            out_trade_no=order_id,
            amount={'total': amount},
            pay_type=wxpay_type,
            payer=payer_dict
        )
        #记录微信接口返回结果
        logger.info(f"微信支付接口返回: code={code}, message={message}, order_id={order_id}")
        
        # 创建订单记录
        order_type = "recharge" if is_recharge else "product"
        order = Order(
            order_id=order_id,
            user_id=user_id,
            amount=amount,
            currency="CNY",
            status='created',
            message=str(message) if message else None,
            pay_type=pay_type,
            payment_method=payment_method,
            order_type=order_type
        )
        created_order = await self.order_repo.create(order)
        logger.info(f"订单记录创建成功: order_id={order_id}, status={order.status},order_type={order_type}")
        
        return {
            "code": code,
            "message": message,
            "order": created_order
        }
    
    async def _create_virtual_currency_order(
        self,
        user_id: str,
        amount: int,
        order_id: str,
        is_recharge: bool = False
    ) -> dict:
        """
        使用虚拟币创建订单
        :param user_id: 用户ID
        :param amount: 订单金额（分）
        :param order_id: 订单号
        :param is_recharge: 是否为充值订单（虚拟币支付不支持充值）
        :return: 订单信息
        """
        if is_recharge:
            raise ValueError("虚拟币不能用于充值，请使用微信支付")
        
        # 计算需要的虚拟币数量：
        virtual_currency_amount = amount
        
        # 消费虚拟币（会检查余额并扣减）
        transaction = await self.virtual_currency_service.consume(
            user_id=user_id,
            amount=virtual_currency_amount,
            order_id=order_id,
            description=f"使用虚拟币购买商品，虚拟币金额：{virtual_currency_amount} 代币"
        )
        
        # 创建订单记录（状态直接为 paid）
        order = Order(
            order_id=order_id,
            user_id=user_id,
            amount=amount,
            currency="CNY",
            status='paid',  # 虚拟币支付无需等待回调，直接为已支付
            message=None,
            pay_type=None,
            payment_method="virtual_currency",
            order_type="product",  # 虚拟币支付只能用于购买商品，不能用于充值
            virtual_currency_amount=virtual_currency_amount
        )
        created_order = await self.order_repo.create(order)
        
        logger.info(f"虚拟币支付订单创建成功: {order_id}, 使用虚拟币: {virtual_currency_amount} 代币")
        
        return {
            "code": 0,
            "message": "支付成功",
            "order": created_order
        }

    async def sign_payment(self, app_id: str, time_stamp: str, nonce: str, package: str) -> str:
        """对支付参数进行签名（不需要证书）"""
        wxpay = get_wxpay_client(require_cert=False)
        sign_data = [app_id, time_stamp, nonce, package]
        return wxpay.sign(sign_data)

    async def handle_payment_notify(self, headers: dict, body: bytes) -> dict:
        """处理微信支付回调（需要证书）"""
        # 处理回调时必须要有证书，SDK 会自动下载
        wxpay = get_wxpay_client(require_cert=True)
        result = wxpay.callback(headers, body)
        logger.info(f"微信支付回调结果: {result}")
        
        if result and result.get('event_type') == 'TRANSACTION.SUCCESS':
            resp = result.get('resource')
            out_trade_no = resp.get('out_trade_no')
            transaction_id = resp.get('transaction_id')
            amount_total = resp.get('amount').get('total')
            
          
            order = await self.order_repo.get_by_order_id_with_lock(out_trade_no)
            if order is None:
                logger.error(f"订单不存在: {out_trade_no}")
                return {
                    "code": "FAILED",
                    "message": "订单不存在"
                }
            
        
            if order.status == 'paid':
                logger.warning(f"订单已处理，跳过: {out_trade_no}")
                return {
                    "code": "SUCCESS",
                    "message": "订单已处理",
                    "order_id": out_trade_no
                }
            
            # 使用事务处理订单状态更新和虚拟币充值
            try:
                # 判断是否为充值订单（使用 order_type 字段）
                is_recharge_order = (
                    order.order_type == 'recharge' and
                    order.payment_method == 'wechat_pay' and
                    order.virtual_currency_amount is None
                )
                
                # 更新订单状态
                await self.order_repo.update_status(
                    order_id=out_trade_no,
                    status='paid',
                    transaction_id=transaction_id
                )
                logger.info(f"订单状态更新为已支付: {out_trade_no}")
                
                # 如果是充值订单，进行虚拟币充值（参考 api-server-fc 的 update_credit 逻辑）
                if is_recharge_order:
                    # 充值虚拟币：1人民币 = 10代币
                    await self.virtual_currency_service.recharge(
                        user_id=order.user_id,
                        amount_cny=order.amount,
                        order_id=out_trade_no,
                        description=f"微信支付充值 {order.amount / 10:.1f} 代币"
                    )
                    logger.info(f"虚拟币充值成功: 订单 {out_trade_no}, 用户 {order.user_id}, 金额 {order.amount} 分")
                else:
                    logger.info(f"订单 {out_trade_no} 不是充值订单，跳过虚拟币充值")
                
                logger.info(f"订单支付成功: {out_trade_no}, 交易号: {transaction_id}, 金额: {amount_total}")
                
                return {
                    "code": "SUCCESS",
                    "message": "支付成功",
                    "order_id": out_trade_no,
                    "transaction_id": transaction_id
                }
            except Exception as e:
                # 如果充值失败，记录错误但不影响订单状态（因为支付已成功）
                logger.error(f"处理订单 {out_trade_no} 失败: {str(e)}")
                # 订单状态已更新，但虚拟币充值可能失败，需要人工处理
                return {
                    "code": "SUCCESS",
                    "message": "订单状态已更新，但虚拟币充值可能失败",
                    "order_id": out_trade_no,
                    "error": str(e)
                }
        else:
            logger.error(f"支付回调验证失败: {result}")
            return {
                "code": "FAILED",
                "message": "支付回调验证失败"
            }

    async def get_order(self, order_id: str) -> Optional[Order]:
        """查询订单"""
        return await self.order_repo.get_by_order_id(order_id)

    async def get_order_list(
        self,
        user_id: Optional[str] = None,
        status: Optional[str] = None,
        order_type: Optional[str] = None,
        payment_method: Optional[str] = None,
        page: int = 1,
        page_size: int = 50,
        sort_by: Optional[str] = None,
        order: Optional[str] = None,
    ):
        """
        获取订单列表（支持分页）
        
        Args:
            user_id: 用户ID（可选）
            status: 订单状态（可选）
            order_type: 订单类型（可选）
            payment_method: 支付方式（可选）
            page: 页码
            page_size: 每页大小
            sort_by: 排序字段（可选）
            order: 排序方向（可选，asc/desc）
        """
        return await self.order_repo.get_order_list(
            user_id=user_id,
            status=status,
            order_type=order_type,
            payment_method=payment_method,
            page=page,
            page_size=page_size,
            sort_by=sort_by,
            order=order,
        )
