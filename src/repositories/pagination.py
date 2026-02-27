from sqlalchemy import func, select
from sqlalchemy.sql.selectable import Select
from sqlalchemy.ext.asyncio import AsyncSession

from entity.pagination import Page


async def paginate(session: AsyncSession, stmt: Select, page: int, page_size: int):
    async with session.begin():
        count = await session.execute(select(func.count()).select_from(stmt.subquery()))
        result = await session.execute(
            stmt.limit(page_size).offset((page - 1) * page_size)
        )
    items = result.scalars().all()
    total = count.scalars().first()
    return Page(items=items, total=total, page=page, page_size=page_size)


async def paginate_with_label(session: AsyncSession, stmt: Select, page: int, page_size: int):
    async with session.begin():
        count = await session.execute(select(func.count()).select_from(stmt.subquery()))
        result = await session.execute(
            stmt.limit().offset((page - 1) * page_size)
        )
    items = result.mappings().all()
    total = count.scalars().first()
    return Page(items=items, total=total, page=page, page_sizec=page_size)
