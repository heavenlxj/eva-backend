#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @File    : wechat_service_user.py

from datetime import datetime, timezone, timedelta
from typing import Optional, List
from sqlalchemy import select, desc
from db_wrapper import DB_SESSION
from repositories.model.wechat_service_user import WechatServiceUser


class WechatServiceUserRepository:

    def __init__(self, db: DB_SESSION):
        self.session = db

    async def create(self, service_openid: str, user_id: Optional[str] = None, unionid: Optional[str] = None) -> WechatServiceUser:
        """Create service account user record"""
        wechat_service_user = WechatServiceUser(
            service_openid=service_openid,
            user_id=user_id,
            unionid=unionid
        )
        async with self.session.begin():
            self.session.add(wechat_service_user)
        return wechat_service_user

    async def get_by_service_openid(self, service_openid: str) -> Optional[WechatServiceUser]:
        """Get user by service account openid"""
        stmt = select(WechatServiceUser).where(
            WechatServiceUser.service_openid == service_openid,
            WechatServiceUser.deleted_at.is_(None)
        )
        async with self.session.begin():
            query = await self.session.execute(stmt)
        return query.scalars().first()

    async def get_by_service_openid_with_lock(self, service_openid: str) -> Optional[WechatServiceUser]:
        """
        Get user by service account openid with SELECT FOR UPDATE lock
        用于在事务中锁定记录，防止并发创建
        注意：此方法不在内部创建事务，需要在外部事务中调用
        """
        stmt = select(WechatServiceUser).where(
            WechatServiceUser.service_openid == service_openid,
            WechatServiceUser.deleted_at.is_(None)
        ).with_for_update()
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def get_by_unionid(self, unionid: str) -> Optional[WechatServiceUser]:
        """Get user by unionid"""
        stmt = select(WechatServiceUser).where(
            WechatServiceUser.unionid == unionid,
            WechatServiceUser.deleted_at.is_(None)
        )
        async with self.session.begin():
            query = await self.session.execute(stmt)
        return query.scalars().first()

    async def get_by_user_id(self, user_id: str) -> Optional[WechatServiceUser]:
        """Get user by user_id"""
        stmt = select(WechatServiceUser).where(
            WechatServiceUser.user_id == user_id,
            WechatServiceUser.deleted_at.is_(None)
        )
        async with self.session.begin():
            query = await self.session.execute(stmt)
        return query.scalars().first()

    async def update_unionid(self, service_openid: str, unionid: str) -> Optional[WechatServiceUser]:
        """
        Update unionid
        如果有多条记录，保留最后一条（id 最大的），软删除其他重复的记录
        """
        stmt = select(WechatServiceUser).where(
            WechatServiceUser.service_openid == service_openid,
            WechatServiceUser.deleted_at.is_(None)
        ).order_by(desc(WechatServiceUser.id))
        
        async with self.session.begin():
            result = await self.session.execute(stmt)
            users = result.scalars().all()
            
            if not users:
                return None
            
            # 如果只有一条记录，直接更新
            if len(users) == 1:
                users[0].unionid = unionid
                return users[0]
            
            # 如果有多条记录，保留最后一条（id 最大的），软删除其他的
            beijing_tz = timezone(timedelta(hours=8))
            latest_user = users[0]  # 已经按 id 降序排列，第一条就是最新的
            latest_user.unionid = unionid
            
            # 软删除其他重复的记录
            for old_user in users[1:]:
                old_user.deleted_at = datetime.now(beijing_tz)
            
            return latest_user

    async def soft_delete_by_service_openid(self, service_openid: str) -> Optional[WechatServiceUser]:
        """Soft delete user by service account openid"""
        stmt = select(WechatServiceUser).where(
            WechatServiceUser.service_openid == service_openid,
            WechatServiceUser.deleted_at.is_(None)
        )
        async with self.session.begin():
            result = await self.session.execute(stmt)
            user = result.scalar_one_or_none()
            if user:
                beijing_tz = timezone(timedelta(hours=8))
                user.deleted_at = datetime.now(beijing_tz)
                return user
        return None

    async def soft_delete(self, id: int) -> None:
        """Soft delete service account user"""
        stmt = select(WechatServiceUser).where(WechatServiceUser.id == id)
        async with self.session.begin():
            result = await self.session.execute(stmt)
            wechat_service_user = result.scalar_one_or_none()
            if wechat_service_user:
                beijing_tz = timezone(timedelta(hours=8))
                wechat_service_user.deleted_at = datetime.now(beijing_tz)

    async def get_all_active(self) -> List[WechatServiceUser]:
        """Get all active service account users"""
        stmt = select(WechatServiceUser).where(
            WechatServiceUser.deleted_at.is_(None)
        )
        async with self.session.begin():
            query = await self.session.execute(stmt)
        return query.scalars().all() 