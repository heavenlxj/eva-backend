"""
WeChat related interface router

This router uses the skip_client_verification_for_router decorator,
all interfaces in this router will skip client verification because:
1. WeChat login interface needs to support miniprogram calls
2. WeChat callback interface needs to support WeChat server calls
3. Test interface needs to support external tool calls

If an interface requires client verification, you can add client verification logic to that interface separately.
"""

from fastapi import APIRouter, Request
from fastapi.responses import PlainTextResponse
from loguru import logger
from typing import Dict, Any

from entity.base import BaseResponse
from entity.user import SendTemplateMessageRequest, SendTemplateMessageByUserRequest, SendTemplateMessageByChildRequest, TemplateMessageResponse
from services.weixin import WechatService
from core.middleware import skip_client_verification_for_router
from core.error_code import ErrorCode
from db_wrapper import DB_SESSION

# Create router and mark as skip client verification
wx_router = skip_client_verification_for_router(APIRouter(prefix="/wx", tags=["wechat_function"]))


@wx_router.get("/login")
async def wechat_login(code: str, db: DB_SESSION):
    service = WechatService(db)
    user_session_data = await service.get_user_info(code)
    return BaseResponse.success(user_session_data)

@wx_router.get("/phone")
async def wechat_phone(code: str, db: DB_SESSION):
    service = WechatService(db)
    user_phone_data = await service.get_user_phone(code)
    return BaseResponse.success(user_phone_data)

@wx_router.get("/webhook")
async def wechat_webhook_verify(
    signature: str = None,
    timestamp: str = None,
    nonce: str = None,
    echostr: str = None
):
    """WeChat server verification interface"""
    logger.info(f"Received WeChat verification request - signature: {signature}, timestamp: {timestamp}, nonce: {nonce}")
    
    if not all([signature, timestamp, nonce, echostr]):
        return PlainTextResponse("Incomplete parameters", status_code=400)
    
    if WechatService.verify_signature(signature, timestamp, nonce):
        logger.info("WeChat verification successful")
        return PlainTextResponse(echostr)
    else:
        logger.error("WeChat verification failed")
        return PlainTextResponse("fail", status_code=403)


@wx_router.post("/webhook")
async def wechat_webhook_event(request: Request, db: DB_SESSION):
    """WeChat event push interface"""
    try:
        # Read XML data
        xml_data = await request.body()
        xml_str = xml_data.decode('utf-8')
        
        logger.info(f"Received WeChat push: {xml_str}")
        
        # Parse XML
        event_data = WechatService.parse_xml(xml_str)
        
        msg_type = event_data.get('MsgType')
        event = event_data.get('Event')
        
        logger.info(f"Message type: {msg_type}, event: {event}")
        
        if msg_type == 'event':
            if event == 'subscribe':
                # User follow event
                logger.info(f"User follow event: {event_data}")
                service = WechatService(db)
                result = await service.handle_follow_event(event_data)
                return PlainTextResponse(result)
            elif event == 'unsubscribe':
                # User unfollow event
                logger.info(f"User unfollow event: {event_data}")
                service = WechatService(db)
                result = await service.handle_unfollow_event(event_data)
                return PlainTextResponse(result)
            elif event == 'TEMPLATESENDJOBFINISH':
                # Template message send completion event
                logger.info(f"Template message send completion event: {event_data}")
                msg_id = event_data.get('MsgID')
                status = event_data.get('Status')
                logger.info(f"Template message send completed - MsgID: {msg_id}, Status: {status}")
                return PlainTextResponse("success")
            elif event == 'CLICK':
                # menu click event
                logger.info(f"Menu click event: {event_data}")
                service = WechatService(db)
                result = await service.handle_click_event(event_data)
                return PlainTextResponse(result)
            else:
                # Other events
                logger.info(f"Other event: {event}")
                return PlainTextResponse("success")
        elif msg_type == 'text':
            logger.info(f"Text message received: {event_data}")
            service = WechatService(db)
            result = await service.handle_text_message(event_data)
            return PlainTextResponse(result)
        else:
            # Other message types
            logger.info(f"Other message type: {msg_type}")
            return PlainTextResponse("success")
            
    except Exception as e:
        logger.error(f"Failed to process WeChat push: {e}")
        return PlainTextResponse("fail", status_code=500)


@wx_router.post("/template")
async def send_template_message(
    request: SendTemplateMessageRequest,
    db: DB_SESSION
):
    """Send template message interface"""
    logger.info(f"Send template message interface - service_openid: {request.service_openid}, template_id: {request.template_id}, data: {request.data}, url: {request.url}, miniprogram: {request.miniprogram}")
    try:
        service = WechatService(db)
        
        data_dict = {key: item.model_dump() for key, item in request.data.items()}
        miniprogram_dict = request.miniprogram.model_dump() if request.miniprogram else None
        
        success = await service.send_template_message(
            request.service_openid, 
            request.template_id, 
            data_dict, 
            request.url, 
            miniprogram_dict
        )
        
        if success:
            return BaseResponse.success(None)
        else:
            return BaseResponse.fail(ErrorCode.TEMPLATE_MESSAGE_SEND_FAILED)
            
    except Exception as e:
        logger.error(f"Failed to send template message: {e}")
        return BaseResponse.fail(ErrorCode.TEMPLATE_MESSAGE_SERVICE_ERROR)


@wx_router.post("/template/user")
async def send_template_message_by_user(
    request: SendTemplateMessageByUserRequest,
    db: DB_SESSION
):
    """Send template message via user_id interface (recommended)"""
    try:
        service = WechatService(db)
        
        data_dict = {key: item.model_dump() for key, item in request.data.items()}
        miniprogram_dict = request.miniprogram.model_dump() if request.miniprogram else None
        
        success = await service.send_template_message_by_user_id(
            request.user_id, 
            request.template_id, 
            data_dict, 
            request.url, 
            miniprogram_dict
        )
        
        if success:
            return BaseResponse.success(None)
        else:
            return BaseResponse.fail(ErrorCode.TEMPLATE_MESSAGE_USER_NOT_FOUND)
            
    except Exception as e:
        logger.error(f"Failed to send template message via user_id: {e}")
        return BaseResponse.fail(ErrorCode.TEMPLATE_MESSAGE_SERVICE_ERROR)


# @wx_router.post("/template/child")
# async def send_template_message_by_child(
#     request: SendTemplateMessageByChildRequest,
#     db: DB_SESSION
# ):
#     """Send template message via child_id interface"""
#     try:
#         service = WechatService(db)
        
#         data_dict = {key: item.model_dump() for key, item in request.data.items()}
#         miniprogram_dict = request.miniprogram.model_dump() if request.miniprogram else None
        
#         success = await service.send_template_message_by_child_id(
#             request.child_id, 
#             request.template_id, 
#             data_dict, 
#             request.url, 
#             miniprogram_dict
#         )
        
#         if success:
#             return BaseResponse.success(None)
#         else:
#             return BaseResponse.fail(ErrorCode.TEMPLATE_MESSAGE_CHILD_USER_NOT_FOUND)
            
#     except Exception as e:
#         logger.error(f"Failed to send template message via child_id: {e}")
#         return BaseResponse.fail(ErrorCode.TEMPLATE_MESSAGE_SERVICE_ERROR)


@wx_router.get("/get-openid-by-user/{user_id}")
async def get_service_openid_by_user(user_id: str, db: DB_SESSION):
    """Get service account openid via user_id"""
    try:
        logger.info(f"Get service account openid via user_id - user_id: {user_id}")
        service = WechatService(db)
        service_openid = await service.get_service_openid_by_user_id_via_unionid(user_id)
        
        if service_openid:
            return {"code": 0, "message": "Get successful", "data": {"service_openid": service_openid}}
        else:
            return {"code": 1, "message": "No corresponding service account openid found", "data": None}
            
    except Exception as e:
        logger.error(f"Failed to get service account openid: {e}")
        return {"code": 1, "message": f"Get failed: {str(e)}", "data": None}


@wx_router.get("/get-user-by-openid/{service_openid}")
async def get_user_by_service_openid(service_openid: str, db: DB_SESSION):
    """Get user_id via service account openid"""
    try:
        service = WechatService(db)
        user_id = await service.get_user_id_by_service_openid(service_openid)
        
        if user_id:
            return {"code": 0, "message": "Get successful", "data": {"user_id": user_id}}
        else:
            return {"code": 1, "message": "No corresponding user found", "data": None}
            
    except Exception as e:
        logger.error(f"Failed to get user: {e}")
        return {"code": 1, "message": f"Get failed: {str(e)}", "data": None}


@wx_router.get("/get-openid-by-unionid/{unionid}")
async def get_service_openid_by_unionid(unionid: str, db: DB_SESSION):
    """Get service account openid via unionid"""
    try:
        service = WechatService(db)
        service_openid = await service.get_service_openid_by_unionid(unionid)
        
        if service_openid:
            return {"code": 0, "message": "Get successful", "data": {"service_openid": service_openid}}
        else:
            return {"code": 1, "message": "No corresponding service account openid found", "data": None}
            
    except Exception as e:
        logger.error(f"Failed to get service account openid: {e}")
        return {"code": 1, "message": f"Get failed: {str(e)}", "data": None}

