#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @File    : devices.py
from os import wait3
from typing import List, Sequence
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from repositories.model.device_info import DeviceInfo


class DeviceRepository:

    def __init__(self, db: AsyncSession):
        self.session = db

    async def create(
        self,
        device_id: str,
        device_name: str,
        mode: int = 1,
    ):
        device = DeviceInfo(
            device_id=device_id,
            device_name=device_name,
            mode=mode,
        )
        self.session.add(device)
        await self.session.commit()
        await self.session.refresh(device)
        return device

    async def get(self, device_id: str) -> DeviceInfo:
        stmt = select(DeviceInfo).where(DeviceInfo.device_id == device_id)
        query = await self.session.execute(stmt)
        return query.scalars().first()


    async def batch_get(self, device_ids: List[str]) -> Sequence[DeviceInfo]:
        stmt = select(DeviceInfo).where(DeviceInfo.device_id.in_(device_ids))
        query = await self.session.execute(stmt)
        return query.scalars().all()

    async def update(
        self,
        device_id: str,
        device_name: str = None,
        mode: int = None,
    ) -> DeviceInfo:
        device = await self.get(device_id)
        if not device:
            raise ValueError(f"Device not found: {device_id}")
        
        if device_name is not None:
            device.device_name = device_name
        if mode is not None:
            device.mode = mode
        
        self.session.add(device)
        await self.session.commit()
        await self.session.refresh(device)
        return device
