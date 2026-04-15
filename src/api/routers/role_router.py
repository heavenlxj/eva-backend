from fastapi import APIRouter
from loguru import logger
from auth import AuthUser
from db_wrapper import DB_SESSION
from entity.base import BaseResponse
from entity.role import BindRoleRequest
from services.role import RoleService

role_router = APIRouter(prefix="/roles", tags=["role manage"])


@role_router.get("")
async def get_roles(db: DB_SESSION, token: AuthUser):
    """获取所有可用角色"""
    service = RoleService(db, token)
    roles = await service.get_all_roles()
    return BaseResponse.success(roles)


@role_router.get("/binding")
async def get_current_binding(db: DB_SESSION, token: AuthUser):
    """获取用户当前绑定的角色"""
    service = RoleService(db, token)
    binding = await service.get_current_binding()
    return BaseResponse.success(binding)


@role_router.post("/bindRole")
async def bind_role(db: DB_SESSION, token: AuthUser, request: BindRoleRequest):
    """绑定角色（如已绑定其他角色会自动切换：软删除旧绑定 + 创建新绑定）"""
    service = RoleService(db, token)
    try:
        result = await service.bind_role(request)
        return BaseResponse.success(result)
    except ValueError as e:
        logger.error(f"绑定角色失败: {e}")
        return BaseResponse.error_with_msg(message=str(e))
    except Exception as e:
        logger.error(f"绑定角色异常: {e}")
        return BaseResponse.error_with_msg(message="绑定角色失败")
