#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @File    : user_device_map.py

from datetime import datetime, timezone, timedelta
from typing import Optional, Sequence
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from repositories.model.user_device_map import UserDeviceMap


class UserDeviceMapRepository:

    def __init__(self, db: AsyncSession):
        self.session = db

    async def create(self, user_id: str, device_id: str) -> UserDeviceMap:
        """创建用户设备绑定关系"""
        mapping = UserDeviceMap(
            user_id=user_id,
            device_id=device_id
        )
        self.session.add(mapping)
        await self.session.commit()
        await self.session.refresh(mapping)
        return mapping

    async def get(self, user_id: str, device_id: str) -> Optional[UserDeviceMap]:
        """获取用户设备绑定关系"""
        stmt = select(UserDeviceMap).where(
            and_(
                UserDeviceMap.user_id == user_id,
                UserDeviceMap.device_id == device_id,
                UserDeviceMap.deleted_at.is_(None)
            )
        )
        query = await self.session.execute(stmt)
        return query.scalars().first()

    async def get_by_user_id(self, user_id: str) -> Sequence[UserDeviceMap]:
        """获取用户的所有设备绑定关系"""
        stmt = select(UserDeviceMap).where(
            and_(
                UserDeviceMap.user_id == user_id,
                UserDeviceMap.deleted_at.is_(None)
            )
        )
        query = await self.session.execute(stmt)
        return query.scalars().all()

    async def get_by_device_id(self, device_id: str) -> Optional[UserDeviceMap]:
        """根据设备ID获取绑定关系"""
        stmt = select(UserDeviceMap).where(
            and_(
                UserDeviceMap.device_id == device_id,
                UserDeviceMap.deleted_at.is_(None)
            )
        )
        query = await self.session.execute(stmt)
        return query.scalars().first()

    async def soft_delete(self, user_id: str, device_id: str) -> bool:
        """软删除用户设备绑定关系"""
        mapping = await self.get(user_id, device_id)
        if not mapping:
            return False
        
        beijing_tz = timezone(timedelta(hours=8))
        mapping.deleted_at = datetime.now(beijing_tz)
        self.session.add(mapping)
        await self.session.commit()
        return True

    async def delete_by_device_id(self, device_id: str) -> bool:
        """根据设备ID删除所有绑定关系（软删除）"""
        stmt = select(UserDeviceMap).where(
            and_(
                UserDeviceMap.device_id == device_id,
                UserDeviceMap.deleted_at.is_(None)
            )
        )
        query = await self.session.execute(stmt)
        mappings = query.scalars().all()
        
        if not mappings:
            return False
        
        beijing_tz = timezone(timedelta(hours=8))
        for mapping in mappings:
            mapping.deleted_at = datetime.now(beijing_tz)
            self.session.add(mapping)
        
        await self.session.commit()
        return True

