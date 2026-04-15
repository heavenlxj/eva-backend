from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession
from entity.login import TokenData
from entity.role import RoleInfo, BindRoleRequest, UserRoleBindingInfo
from repositories.role import RoleRepository
from repositories.user_role_map import UserRoleMapRepository


class RoleService:

    def __init__(self, db: AsyncSession, token: TokenData = None):
        self.db = db
        self.token = token
        self.role_repo = RoleRepository(db)
        self.user_role_map_repo = UserRoleMapRepository(db)

    async def get_all_roles(self) -> list[RoleInfo]:
        roles = await self.role_repo.get_all_active()
        return [RoleInfo.model_validate(r) for r in roles]

    async def get_current_binding(self) -> UserRoleBindingInfo | None:
        user_id = self.token.user_id
        mapping = await self.user_role_map_repo.get_active_by_user(user_id)
        if not mapping:
            return None

        role = await self.role_repo.get_by_role_id(mapping.role_id)
        return UserRoleBindingInfo(
            role_id=mapping.role_id,
            role_name=role.name if role else None,
            device_id=mapping.device_id,
            created_at=mapping.created_at
        )

    async def bind_role(self, request: BindRoleRequest) -> dict:
        user_id = self.token.user_id

        role = await self.role_repo.get_by_role_id(request.role_id)
        if not role:
            raise ValueError(f"角色不存在: {request.role_id}")

        current = await self.user_role_map_repo.get_active_by_user(user_id)
        if current and current.role_id == request.role_id:
            logger.info(f"用户 {user_id} 已绑定角色 {request.role_id}")
            return {"message": "已绑定该角色", "role_id": request.role_id, "switched": False}

        old_role_id = None
        if current:
            old_role_id = await self.user_role_map_repo.soft_delete_active(user_id)
            logger.info(f"用户 {user_id} 解绑旧角色 {old_role_id}")

        await self.user_role_map_repo.create(user_id, request.role_id, request.device_id)
        logger.info(f"用户 {user_id} 绑定新角色 {request.role_id}")

        return {
            "message": "角色绑定成功" if not old_role_id else "角色切换成功",
            "role_id": request.role_id,
            "old_role_id": old_role_id,
            "switched": old_role_id is not None
        }
