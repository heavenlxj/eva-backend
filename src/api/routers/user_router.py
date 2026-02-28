from typing import List

from fastapi import APIRouter, Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from db_wrapper import DB_SESSION
from entity.base import BaseResponse
from core.error_code import ErrorCode
from entity.user import UserLoginRequest, CreateUserRequest, UserInfo, UpdateUserRequest, BindDeviceRequest, UnbindDeviceRequest
from services.user import UserService, InternalUserService
from auth import AuthUser, refresh_token



user_router = APIRouter(prefix="/users", tags=["auth"])
bearer_scheme = HTTPBearer()
@user_router.post("/login")
async def user_login(login_request: UserLoginRequest, db: DB_SESSION):
    service = UserService(db)
    result = await service.user_login(login_request)
    if not result:
        return BaseResponse.error(None, ErrorCode.WX_AUTH_INVALID)
    return BaseResponse.success(result)

@user_router.post("/auth/refresh-token")
async def auth_refresh_token(
    token: HTTPAuthorizationCredentials = Depends(bearer_scheme),
):
    refreshed_token = await refresh_token(token)
    return BaseResponse.success(refreshed_token)


@user_router.put("/", response_model=BaseResponse[UserInfo])
async def update_user(
    db: DB_SESSION,
    token: AuthUser,
    user_info: UpdateUserRequest
):
    service = UserService(db, token)
    user = await service.update_user(user_info)
    return BaseResponse[UserInfo](data=user)


@user_router.post("/", response_model=BaseResponse[UserInfo])
async def create_user(db: DB_SESSION, user_info: CreateUserRequest):
    service = InternalUserService(db)
    user = await service.create_user(user_info=user_info)
    return BaseResponse[UserInfo](data=user)

@user_router.get("/")
async def get_user(
        db: DB_SESSION,
        token: AuthUser
):
    service = UserService(db, token)
    user = await service.get_user()
    return BaseResponse.success(user)


@user_router.post("/logoff")
async def logoff_user(
    db: DB_SESSION,
    token: AuthUser,
):
    # TODO: 实现注销逻辑
    return BaseResponse.success("OK")


@user_router.post("/devices/bind")
async def bind_device(
    db: DB_SESSION,
    token: AuthUser,
    request: BindDeviceRequest
):
    """绑定设备到当前用户"""
    service = UserService(db, token)
    try:
        success = await service.bind_device(request.device_id)
        if success:
            return BaseResponse.success({"message": "设备绑定成功"})
        else:
            return BaseResponse.error(None, ErrorCode.WX_AUTH_INVALID)
    except Exception as e:
        from loguru import logger
        logger.error(f"绑定设备失败: {e}")
        return BaseResponse.error(None, ErrorCode.WX_AUTH_INVALID)


@user_router.post("/devices/unbind")
async def unbind_device(
    db: DB_SESSION,
    token: AuthUser,
    request: UnbindDeviceRequest
):
    """解绑设备"""
    service = UserService(db, token)
    try:
        success = await service.unbind_device(request.device_id)
        if success:
            return BaseResponse.success({"message": "设备解绑成功"})
        else:
            return BaseResponse.error(None, ErrorCode.WX_AUTH_INVALID)
    except Exception as e:
        from loguru import logger
        logger.error(f"解绑设备失败: {e}")
        return BaseResponse.error(None, ErrorCode.WX_AUTH_INVALID)


@user_router.get("/devices")
async def get_user_devices(
    db: DB_SESSION,
    token: AuthUser
):
    """获取用户的所有设备"""
    service = UserService(db, token)
    devices = await service.get_user_devices()
    return BaseResponse.success(devices)


@user_router.get("/devices/{device_id}/user")
async def get_device_user(
    db: DB_SESSION,
    token: AuthUser,
    device_id: str
):
    """获取设备绑定的用户"""
    service = UserService(db, token)
    user_info = await service.get_device_user(device_id)
    if user_info:
        return BaseResponse.success(user_info)
    else:
        return BaseResponse.success(None)  # 设备未绑定返回 null，而不是错误
