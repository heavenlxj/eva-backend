#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @File    : device.py
import json

from sqlalchemy.ext.asyncio import AsyncSession
from entity.devices import UnbindDeviceRequest, UnbindType, AddDeviceRequest, UpdateDeviceRequest, DeviceInfo
from entity.login import TokenData
from repositories.devices import DeviceRepository
from package.redis.cache import AsyncRedisCache
from loguru import logger


class DeviceService:

    def __init__(self, token: TokenData, db: AsyncSession = None, base_url: str = None):
        self.token = token
        if db:
            self.device_repo = DeviceRepository(db)

    async def create(self, device_info: AddDeviceRequest):
        existing_device = await self.device_repo.get(device_info.device_id)
        if existing_device:
            logger.info(
                f"Device already exists, device_id: {device_info.device_id}, device_name: {existing_device.device_name}"
            )
            return existing_device

        mode = device_info.mode if device_info.mode is not None else 1
        logger.info(
            f"Create new device, device_id: {device_info.device_id}, device_name: {device_info.device_name}, mode: {mode}"
        )
        device = await self.device_repo.create(
            device_id=device_info.device_id,
            device_name=device_info.device_name,
            mode=mode,
        )
        return device

    async def update(self, device_id: str, device_info: UpdateDeviceRequest):
        # 检查设备是否存在
        existing_device = await self.device_repo.get(device_id)
        if not existing_device:
            logger.warning(
                f"Device not found, skip update: device_id={device_id}"
            )
            return None
        
        logger.info(
            f"Update device, device_id: {device_id}, device_name: {device_info.device_name}, mode: {device_info.mode}"
        )
        device = await self.device_repo.update(
            device_id=device_id,
            device_name=device_info.device_name,
            mode=device_info.mode,
        )
        return device

    async def get_device_info(self, device_id: str):
        device = await self.device_repo.get(device_id)
        if not device:
            return None
        device_info = DeviceInfo.model_validate(device)
        return device_info

    async def get_device_state(self, device_id: str):
        return await self.whale.get_device_state_async(device_id)


