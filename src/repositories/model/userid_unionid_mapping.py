#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @File    : userid_unionid_mapping.py

from datetime import datetime
from sqlalchemy import Integer, String, TIMESTAMP, func
from sqlalchemy.orm import Mapped, mapped_column

from db_wrapper import Base


class UseridUnionidMapping(Base):
    __tablename__ = "user_unionid_mapping"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    unionid: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(TIMESTAMP, server_default=func.now(), onupdate=func.now())
    deleted_at: Mapped[datetime | None] = mapped_column(TIMESTAMP)
