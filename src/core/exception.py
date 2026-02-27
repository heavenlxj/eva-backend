#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @File    : exception.py

from fastapi import HTTPException


class PlatformException(HTTPException):
    def __init__(
        self, 
        code: int, 
        message: str, 
        data: any = None,
        status_code: int = 500,
        headers: dict = None
    ) -> None:
        self.detail = {
            "code": code,
            "data": data,
            "message": message
        }
        super().__init__(
            status_code=status_code,
            detail=self.detail,
            headers=headers
        )
