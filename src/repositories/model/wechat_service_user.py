#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @File    : wechat_service_user.py

from datetime import datetime
from sqlalchemy import Integer, String, TIMESTAMP, func
from sqlalchemy.orm import Mapped, mapped_column

from db_wrapper import Base


class WechatServiceUser(Base):
    __tablename__ = "wechat_service_users"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id: Mapped[str | None] = mapped_column(String(32), nullable=True, index=True)  # Links to users table user_id
    service_openid: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    unionid: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(TIMESTAMP, server_default=func.now(), onupdate=func.now())
    deleted_at: Mapped[datetime | None] = mapped_column(TIMESTAMP) 