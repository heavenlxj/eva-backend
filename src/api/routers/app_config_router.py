from auth import AuthUser
from core.config.settings import settings
from entity.base import BaseResponse
from fastapi import APIRouter, Depends, Query
from typing import Optional

from services.app_config import AppConfigService

router = APIRouter(prefix="/app_configs", tags=["小程序配置"])


@router.get("/")
async def get_config_by_key(
    token: AuthUser,
    key: str = Query(..., description="key"),
    version: Optional[str] = Query(None, description="vesion, optional"),
):
    """
    根据key获取配置, 支持带版本和不带版本
    """
    base_url = settings.external.WHALE_URL
    config_service = AppConfigService(base_url)
    result = await config_service.get_config_by_key(key, version)
    resp = BaseResponse.success(result)
    return resp