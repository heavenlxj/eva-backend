#!/usr/bin/env python
# -*- coding: utf-8 -*-

from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from repositories.model.miniprogram_config import MiniprogramConfig


class MiniprogramConfigRepository:
    """Repository for miniprogram configuration."""

    def __init__(self, db: AsyncSession):
        self.session = db

    async def get_active_by_key(self, key: str) -> Optional[MiniprogramConfig]:
        """Fetch active configuration by key."""
        stmt = (
            select(MiniprogramConfig)
            .where(
                MiniprogramConfig.key == key,
                MiniprogramConfig.is_active.is_(True),
                MiniprogramConfig.deleted_at.is_(None),
            )
            .order_by(MiniprogramConfig.updated_at.desc())
            .limit(1)
        )

        # 不使用 begin()，让外层管理事务，避免嵌套事务错误
        result = await self.session.execute(stmt)
        return result.scalars().first()

