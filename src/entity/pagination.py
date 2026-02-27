from typing import Generic, TypeVar

from fastapi import Query
from pydantic import BaseModel, ConfigDict

T = TypeVar("T")


class PageParams(BaseModel):
    page: int = Query(1, ge=1, description="页码")
    page_size: int = Query(50, ge=1, le=200, description="页大小")


class Page(BaseModel, Generic[T]):
    model_config = ConfigDict(arbitrary_types_allowed=True, from_attributes=True)

    items: list[T]
    total: int
    page: int
    page_size: int
