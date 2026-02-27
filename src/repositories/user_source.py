#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @File    : user_source.py


from datetime import datetime, timezone, timedelta
from sqlalchemy import select
from db_wrapper import DB_SESSION
from repositories.model.user_source import UserSource


class UserSourceRepository:

    def __init__(self, db: DB_SESSION):
        self.session = db

    async def create(self, user_id: str, openid: str, source: str, unionid: str = None) -> UserSource:
        user_source = UserSource(
            user_id=user_id,
            openid=openid,
            source=source,
            union_id=unionid
        )
        # 如果已在事务中，直接添加；否则开启新事务
        try:
            if hasattr(self.session, 'in_transaction') and self.session.in_transaction():
                self.session.add(user_source)
                await self.session.flush()
            else:
                async with self.session.begin():
                    self.session.add(user_source)
        except (AttributeError, Exception):
            # 如果无法检查事务状态，尝试直接添加并 flush
            self.session.add(user_source)
            await self.session.flush()
        return user_source


    async def get_with_open_id(self, openid: str, source: str) -> UserSource:
        stmt = select(UserSource).where(
            UserSource.openid == openid, 
            UserSource.source == source
        )
        # 只读查询不需要开启事务，如果已在事务中则直接执行
        query = await self.session.execute(stmt)
        return query.scalars().first()

    async def get_with_user_id(self, user_id: str, source: str) -> UserSource:
        """通过 user_id 获取用户来源信息"""
        stmt = select(UserSource).where(
            UserSource.user_id == user_id, 
            UserSource.source == source,
            UserSource.deleted_at.is_(None)
        )
        async with self.session.begin():
            query = await self.session.execute(stmt)
        return query.scalars().first()

    async def soft_delete(self, id: int) -> None:
        """软删除用户来源信息"""
        stmt = select(UserSource).where(UserSource.id == id)
        async with self.session.begin():
            result = await self.session.execute(stmt)
            user_source = result.scalar_one_or_none()
            if user_source:
                beijing_tz = timezone(timedelta(hours=8))
                user_source.deleted_at = datetime.now(beijing_tz)

    async def update_unionid(self, id: int, unionid: str) -> None:
        """更新unionid"""
        stmt = select(UserSource).where(UserSource.id == id)
        # 如果已在事务中，直接执行；否则开启新事务
        try:
            if hasattr(self.session, 'in_transaction') and self.session.in_transaction():
                result = await self.session.execute(stmt)
                user_source = result.scalar_one_or_none()
                if user_source:
                    user_source.union_id = unionid
                    await self.session.flush()
            else:
                async with self.session.begin():
                    result = await self.session.execute(stmt)
                    user_source = result.scalar_one_or_none()
                    if user_source:
                        user_source.union_id = unionid
        except (AttributeError, Exception):
            # 如果无法检查事务状态，尝试直接执行
            result = await self.session.execute(stmt)
            user_source = result.scalar_one_or_none()
            if user_source:
                user_source.union_id = unionid
                await self.session.flush()

    async def get_by_unionid(self, unionid: str, source: str) -> UserSource:
        """通过unionid获取用户来源信息"""
        stmt = select(UserSource).where(
            UserSource.union_id == unionid,
            UserSource.source == source,
            UserSource.deleted_at.is_(None)
        )
        # 只读查询不需要开启事务，如果已在事务中则直接执行
        query = await self.session.execute(stmt)
        return query.scalars().first()

    async def delete(self, id: int) -> None:
        """删除用户来源信息"""
        stmt = select(UserSource).where(UserSource.id == id)
        async with self.session.begin():
            result = await self.session.execute(stmt)
            user_source = result.scalar_one_or_none()
            if user_source:
                await self.session.delete(user_source)

