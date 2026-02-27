#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @File    : device_info.py

from datetime import datetime
from sqlalchemy import Integer, String, TIMESTAMP, func
from sqlalchemy.orm import Mapped, mapped_column

from db_wrapper import Base


class DeviceInfo(Base):

    __tablename__ = "device_info"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    device_id: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    device_name: Mapped[str] = mapped_column(String(64))
    mode: Mapped[int] = mapped_column(Integer, nullable=False, default=1, comment="通信模式：1-半双工，2-全双工")
    created_at: Mapped[datetime | None] = mapped_column(TIMESTAMP, server_default=func.now())
    updated_at: Mapped[datetime | None] = mapped_column(TIMESTAMP, server_default=func.now(), onupdate=func.now())
    deleted_at: Mapped[datetime | None] = mapped_column(TIMESTAMP)
