#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @File    : devices.py

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field, ConfigDict, UUID4, field_serializer, field_validator


class UnbindType(Enum):
    Agent = "agent"
    Device = "device"


class DeviceInfo(BaseModel):
    device_id: str = Field(description="device uuid")
    device_name: Optional[str] = Field(description="device name", default=None)
    mode: int = Field(description="通信模式：1-半双工，2-全双工", default=1)
    created_at: Optional[datetime] = Field(description="创建时间", default=None)

    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
        arbitrary_types_allowed=True
    )

    @field_serializer('created_at')
    def serialize_created_at(self, value: Optional[datetime], _info) -> Optional[str]:
        """将 datetime 序列化为 ISO 格式字符串"""
        if value is None:
            return None
        return value.isoformat()


class UnbindDeviceRequest(BaseModel):
    type: UnbindType = Field(description="unbind device info")
    child_id: str = Field(description="child uuid")
    unbind_id: str = Field(description="device or agent uuid")


class AddDeviceRequest(BaseModel):
    device_id: str = Field(description="device id")
    device_name: str = Field(description="device name", default=None)
    mode: Optional[int] = Field(description="通信模式：1-半双工，2-全双工", default=1)

    @field_validator("mode", mode="before")
    @classmethod
    def normalize_mode(cls, value):
        """将空字符串转换为 None，以便使用默认值"""
        if value in (None, "", b"", []):
            return None
        if isinstance(value, str):
            stripped = value.strip()
            if stripped == "":
                return None
            if stripped.isdigit():
                return int(stripped)
        if isinstance(value, (int, float)):
            return int(value)
        return value


class UpdateDeviceRequest(BaseModel):
    device_name: Optional[str] = Field(description="device name", default=None)
    mode: Optional[int] = Field(description="通信模式：1-半双工，2-全双工", default=None)

class DeviceTokenBindRequest(BaseModel):
    device_id: str = Field(description="device id")
    token: str = Field(description="token")

class DeviceTokenDeleteRequest(BaseModel):
    device_id: str = Field(description="device id")
    token: str = Field(description="token")

class NetworkBindRequest(BaseModel):
    device_id: str
    ip: str
    bssid: str

class NetworkSoftDeleteRequest(BaseModel):
    device_id: str