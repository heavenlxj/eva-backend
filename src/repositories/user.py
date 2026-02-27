#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @File    : user.py

from datetime import datetime, timezone, timedelta
from typing import Sequence, List
from sqlalchemy import select
from db_wrapper import DB_SESSION
from entity.user import UpdateUserRequest
from repositories.model.user import User
from fastapi import HTTPException

class UserRepository:

    def __init__(self, db: DB_SESSION):
        self.session = db

    async def create(
        self,
        user_id: str,
        phone: str = None,
        nickname: str = None,
        avatar_url: str = None,
        birthday: str = None,
        email: str = None,
    ) -> User:
        user = User(
            user_id=user_id,
            nickname=nickname,
            avatar_url=avatar_url,
            birthday=birthday,
            phone=phone,
            email=email,
        )
        # 如果已在事务中，直接添加；否则开启新事务
        try:
            if hasattr(self.session, 'in_transaction') and self.session.in_transaction():
                self.session.add(user)
                await self.session.flush()
            else:
                async with self.session.begin():
                    self.session.add(user)
        except (AttributeError, Exception):
            # 如果无法检查事务状态，尝试直接添加并 flush
            self.session.add(user)
            await self.session.flush()
        return user

    async def get(self, user_id: str) -> User:
        """获取用户信息，排除已删除的"""
        stmt = select(User).where(
            User.user_id == user_id,
            User.deleted_at.is_(None)
        )
        query = await self.session.execute(stmt)
        return query.scalars().first()

    async def batch_get(self, user_ids: List[str]) -> Sequence[User]:
        stmt = select(User).where(User.user_id.in_(user_ids))
        query = await self.session.execute(stmt)
        return query.scalars().all()

    async def update(self, user_id: str, update_data: UpdateUserRequest) -> User:
        stmt = select(User).where(User.user_id == user_id)
        
        async with self.session.begin():
            result = await self.session.execute(stmt)
            user = result.scalar_one_or_none()

            if not user:
                raise HTTPException(status_code=404, detail="User not found")

            update_dict = update_data.model_dump(exclude_unset=True)
            for key, value in update_dict.items():
                setattr(user, key, value)

        try:
            await self.session.refresh(user)
            return user
        except Exception as e:
            await self.session.rollback()
            raise HTTPException(status_code=500, detail=str(e))

    async def get_by_phone(self, phone: str) -> User:
        """通过手机号获取用户"""
        stmt = select(User).where(
            User.phone == phone,
            User.deleted_at.is_(None)
        )
        # 只读查询不需要开启事务，直接执行即可
        query = await self.session.execute(stmt)
        return query.scalars().first()

    async def soft_delete(self, id: int) -> None:
        """软删除用户"""
        stmt = select(User).where(User.id == id)
        async with self.session.begin():
            result = await self.session.execute(stmt)
            user = result.scalar_one_or_none()
            if user:
                beijing_tz = timezone(timedelta(hours=8))
                user.deleted_at = datetime.now(beijing_tz)
