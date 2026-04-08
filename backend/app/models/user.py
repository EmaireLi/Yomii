"""
用户模型 (MySQL - 用户行为数据库)
"""
from datetime import datetime
from typing import Optional
from sqlmodel import SQLModel, Field


class UserBase(SQLModel):
    """用户基础模型"""
    email: Optional[str] = Field(default=None, unique=True, index=True)
    phone: Optional[str] = Field(default=None, unique=True, index=True)
    username: str = Field(unique=True, index=True)
    is_active: bool = True
    is_superuser: bool = False


class User(UserBase, table=True):
    """用户数据库模型 (存储在 MySQL)"""
    __tablename__ = "users"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    hashed_password: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class UserCreate(SQLModel):
    """用户创建模型"""
    email: Optional[str] = None
    phone: Optional[str] = None
    username: str
    password: str


class UserUpdate(SQLModel):
    """用户更新模型"""
    email: Optional[str] = None
    phone: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None


class UserInDB(UserBase):
    """数据库中的用户（带 ID）"""
    id: int
    created_at: datetime
    updated_at: datetime
