from datetime import datetime, timezone, timedelta
from typing import Optional, Sequence
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from repositories.model.user_role_map import UserRoleMap


class UserRoleMapRepository:

    def __init__(self, db: AsyncSession):
        self.session = db

    async def create(self, user_id: str, role_id: str) -> UserRoleMap:
        mapping = UserRoleMap(
            user_id=user_id,
            role_id=role_id,
        )
        self.session.add(mapping)
        await self.session.commit()
        await self.session.refresh(mapping)
        return mapping

    async def get_active_by_user(self, user_id: str) -> Optional[UserRoleMap]:
        stmt = select(UserRoleMap).where(
            and_(
                UserRoleMap.user_id == user_id,
                UserRoleMap.is_active == True,
                UserRoleMap.deleted_at.is_(None)
            )
        )
        query = await self.session.execute(stmt)
        return query.scalars().first()

    async def get_by_user_and_role(self, user_id: str, role_id: str) -> Optional[UserRoleMap]:
        stmt = select(UserRoleMap).where(
            and_(
                UserRoleMap.user_id == user_id,
                UserRoleMap.role_id == role_id,
                UserRoleMap.deleted_at.is_(None)
            )
        )
        query = await self.session.execute(stmt)
        return query.scalars().first()

    async def soft_delete(self, user_id: str, role_id: str) -> bool:
        mapping = await self.get_by_user_and_role(user_id, role_id)
        if not mapping:
            return False

        beijing_tz = timezone(timedelta(hours=8))
        mapping.deleted_at = datetime.now(beijing_tz)
        mapping.is_active = False
        self.session.add(mapping)
        await self.session.commit()
        return True

    async def soft_delete_active(self, user_id: str) -> Optional[str]:
        """软删除用户当前激活的角色绑定，返回被删除的 role_id"""
        current = await self.get_active_by_user(user_id)
        if not current:
            return None

        beijing_tz = timezone(timedelta(hours=8))
        old_role_id = current.role_id
        current.deleted_at = datetime.now(beijing_tz)
        current.is_active = False
        self.session.add(current)
        await self.session.commit()
        return old_role_id
