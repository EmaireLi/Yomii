"""
通用响应 Schemas
"""
from pydantic import BaseModel
from typing import Generic, TypeVar, Optional, List

T = TypeVar("T")


class ResponseBase(BaseModel, Generic[T]):
    """通用响应基础模型"""
    success: bool = True
    message: str = "操作成功"
    data: Optional[T] = None


class PaginatedResponse(BaseModel, Generic[T]):
    """分页响应模型"""
    items: List[T]
    total: int
    page: int
    page_size: int
    pages: int


class ErrorResponse(BaseModel):
    """错误响应模型"""
    success: bool = False
    message: str
    detail: Optional[str] = None
