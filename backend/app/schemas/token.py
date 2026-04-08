"""
Token Schemas
"""
from pydantic import BaseModel
from typing import Optional


class Token(BaseModel):
    """访问令牌响应"""
    access_token: str
    token_type: str = "bearer"


class TokenPayload(BaseModel):
    """令牌载荷"""
    sub: Optional[str] = None
