from typing import List

from fastapi import APIRouter, Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from db_wrapper import DB_SESSION
from entity.base import BaseResponse
from core.error_code import ErrorCode
from entity.user import UserLoginRequest, CreateUserRequest, UserInfo, UpdateUserRequest
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
    service = UserService(db, token)
    await service.logoff_user()
    return BaseResponse.success("OK")
