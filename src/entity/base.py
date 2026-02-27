
from abc import ABC
from typing import Generic, Optional, TypeVar, Any
from pydantic import BaseModel, Field
from fastapi import status
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from entity.pagination import Page
from core.error_code import ErrorCode

T = TypeVar("T")

class BaseResponse(BaseModel, Generic[T]):
    code: int = 0
    message: str = "OK"
    data: Optional[T] = Field(default=None)

    @classmethod
    def success(cls, data: Any):
        encoded_data = jsonable_encoder(cls(code=0, data=data, message='OK').model_dump())
        return JSONResponse(content=encoded_data, status_code=status.HTTP_200_OK)

    @classmethod
    def fail(cls, error_code: ErrorCode=ErrorCode.INTERNAL_SERVER_ERROR):
        return JSONResponse(content=cls(data={}, code=error_code.id, message=error_code.msg).model_dump(), status_code=status.HTTP_200_OK)

    @classmethod
    def error(cls, data: Any, error_code: ErrorCode):
        return JSONResponse(content=cls(data=data, code=error_code.id, message=error_code.msg).model_dump(), status_code=status.HTTP_200_OK)

    @classmethod
    def error_with_msg(cls, data: Any=None, message: str="Internal Server Error"    ):
        return JSONResponse(content=cls(data=data, code=-1, message=message).model_dump(), status_code=status.HTTP_200_OK)

    @classmethod
    def error_with_status(cls, error_code: ErrorCode, status_code: int):
        return JSONResponse(content=cls(data={}, code=error_code.id, message=error_code.msg).model_dump(), status_code=status_code)


class PageResponse(BaseModel, Generic[T]):
    code: int = 0
    message: str = "Success"
    data: Page[T]
