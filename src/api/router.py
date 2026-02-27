#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @File    : router.py

from fastapi import APIRouter
from api.routers.user_router import user_router
from api.routers.wx_router import wx_router
from api.routers.device_router import device_router
from api.routers.data_report_router import api_router as data_report_router
from api.routers.app_config_router import router as app_config_router

api_router = APIRouter(prefix="/app/api")

api_router.include_router(user_router)
api_router.include_router(wx_router)
api_router.include_router(device_router)
api_router.include_router(data_report_router)
api_router.include_router(app_config_router)

# 导出main_router以供app.py使用
__all__ = ["api_router", "main_router"]

