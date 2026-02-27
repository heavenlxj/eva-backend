#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @File    : device_router.py
from sys import prefix

from fastapi import APIRouter, Path, Body
from loguru import logger
from core.config.settings import settings
from auth import AuthUser
from db_wrapper import DB_SESSION
from entity.base import BaseResponse
from entity.devices import (
    UnbindDeviceRequest,
    AddDeviceRequest,
    UpdateDeviceRequest
)
from services.device import DeviceService

device_router = APIRouter(prefix="/device", tags=["device manage"])


@device_router.post("")
async def add_device(
    db: DB_SESSION,
    token: AuthUser,
    device_info: AddDeviceRequest,
):
    service = DeviceService(token, db=db)
    await service.create(device_info=device_info)
    return BaseResponse.success(None)


@device_router.put("/{device_id}")
async def update_device(
    db: DB_SESSION,
    token: AuthUser,
    device_id: str = Path(title="device id"),
    device_info: UpdateDeviceRequest = Body(...),
):
    service = DeviceService(token, db=db)
    result = await service.update(device_id=device_id, device_info=device_info)
    return BaseResponse.success(result)


@device_router.get("/{device_id}")
async def get_device_info(
    db: DB_SESSION,
    token: AuthUser,
    device_id: str = Path(title="device id"),
):
    service = DeviceService(token, db=db)
    result = await service.get_device_info(device_id)
    return BaseResponse.success(result)


@device_router.post("/unbind")
async def unbind_device(
    db: DB_SESSION,
    token: AuthUser,
    unbind_info: UnbindDeviceRequest,
):
    service = DeviceService(token, db=db)
    await service.unbind_device(unbind_info)
    return BaseResponse.success(None)

