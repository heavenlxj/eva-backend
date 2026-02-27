#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @File    : userid_unionid_mapping.py

from datetime import datetime, timezone, timedelta
from typing import Optional
from sqlalchemy import select
from db_wrapper import DB_SESSION
from repositories.model.userid_unionid_mapping import UseridUnionidMapping


class UseridUnionidMappingRepository:

    def __init__(self, db: DB_SESSION):
        self.session = db

    async def create(self, user_id: str, unionid: str) -> UseridUnionidMapping:
        """创建用户ID与UnionID的映射关系"""
        mapping = UseridUnionidMapping(
            user_id=user_id,
            unionid=unionid
        )
        # 如果已在事务中，直接添加；否则开启新事务
        try:
            if hasattr(self.session, 'in_transaction') and self.session.in_transaction():
                self.session.add(mapping)
                await self.session.flush()
            else:
                async with self.session.begin():
                    self.session.add(mapping)
        except (AttributeError, Exception):
            # 如果无法检查事务状态，尝试直接添加并 flush
            self.session.add(mapping)
            await self.session.flush()
        return mapping

    async def get_by_user_id(self, user_id: str) -> Optional[UseridUnionidMapping]:
        """通过用户ID获取映射关系"""
        stmt = select(UseridUnionidMapping).where(
            UseridUnionidMapping.user_id == user_id,
            UseridUnionidMapping.deleted_at.is_(None)
        )
        # 只读查询不需要开启事务，如果已在事务中则直接执行
        query = await self.session.execute(stmt)
        return query.scalars().first()

    async def get_by_unionid(self, unionid: str) -> Optional[UseridUnionidMapping]:
        """通过UnionID获取映射关系"""
        stmt = select(UseridUnionidMapping).where(
            UseridUnionidMapping.unionid == unionid,
            UseridUnionidMapping.deleted_at.is_(None)
        )
        # 只读查询不需要开启事务，如果已在事务中则直接执行
        query = await self.session.execute(stmt)
        return query.scalars().first()

    async def update_unionid(self, user_id: str, unionid: str) -> Optional[UseridUnionidMapping]:
        """更新用户的UnionID"""
        stmt = select(UseridUnionidMapping).where(
            UseridUnionidMapping.user_id == user_id,
            UseridUnionidMapping.deleted_at.is_(None)
        )
        
        # 如果已在事务中，直接执行；否则开启新事务
        try:
            if hasattr(self.session, 'in_transaction') and self.session.in_transaction():
                result = await self.session.execute(stmt)
                mapping = result.scalar_one_or_none()
                if mapping:
                    mapping.unionid = unionid
                    await self.session.flush()
                    return mapping
            else:
                async with self.session.begin():
                    result = await self.session.execute(stmt)
                    mapping = result.scalar_one_or_none()
                    if mapping:
                        mapping.unionid = unionid
                        return mapping
        except (AttributeError, Exception):
            # 如果无法检查事务状态，尝试直接执行
            result = await self.session.execute(stmt)
            mapping = result.scalar_one_or_none()
            if mapping:
                mapping.unionid = unionid
                await self.session.flush()
                return mapping
        
        return None

    async def soft_delete(self, id: int) -> None:
        """软删除映射关系"""
        stmt = select(UseridUnionidMapping).where(UseridUnionidMapping.id == id)
        async with self.session.begin():
            result = await self.session.execute(stmt)
            mapping = result.scalar_one_or_none()
            if mapping:
                beijing_tz = timezone(timedelta(hours=8))
                mapping.deleted_at = datetime.now(beijing_tz)

    async def delete(self, id: int) -> None:
        """删除映射关系"""
        stmt = select(UseridUnionidMapping).where(UseridUnionidMapping.id == id)
        async with self.session.begin():
            result = await self.session.execute(stmt)
            mapping = result.scalar_one_or_none()
            if mapping:
                await self.session.delete(mapping)
