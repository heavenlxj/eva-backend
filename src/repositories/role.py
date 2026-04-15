from typing import Optional, Sequence
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from repositories.model.role import Role


class RoleRepository:

    def __init__(self, db: AsyncSession):
        self.session = db

    async def get_all_active(self) -> Sequence[Role]:
        stmt = select(Role).where(
            and_(
                Role.is_active == True,
                Role.deleted_at.is_(None)
            )
        )
        query = await self.session.execute(stmt)
        return query.scalars().all()

    async def get_by_role_id(self, role_id: str) -> Optional[Role]:
        stmt = select(Role).where(
            and_(
                Role.role_id == role_id,
                Role.is_active == True,
                Role.deleted_at.is_(None)
            )
        )
        query = await self.session.execute(stmt)
        return query.scalars().first()
