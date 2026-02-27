#!/usr/bin/env python
# -*- coding: utf-8 -*-

from datetime import datetime

from sqlalchemy import String, Text, Boolean, TIMESTAMP, func
from sqlalchemy.orm import Mapped, mapped_column

from db_wrapper import Base


class MiniprogramConfig(Base):
    __tablename__ = "miniprogram_config"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    key: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    value: Mapped[str] = mapped_column(Text, nullable=False)
    version: Mapped[str] = mapped_column(String(32), nullable=False, default="latest")
    description: Mapped[str | None] = mapped_column(String(255))
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime | None] = mapped_column(TIMESTAMP, server_default=func.now())
    updated_at: Mapped[datetime | None] = mapped_column(
        TIMESTAMP, server_default=func.now(), onupdate=func.now()
    )
    deleted_at: Mapped[datetime | None] = mapped_column(TIMESTAMP, nullable=True)

