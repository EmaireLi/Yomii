"""
收藏和搜索历史模型 (MySQL - 用户行为数据库)
"""
from datetime import datetime
from typing import Optional
from sqlmodel import SQLModel, Field


class FavoriteBase(SQLModel):
    """收藏基础模型"""
    user_id: int = Field(foreign_key="users.id", index=True)
    word_id: int = Field(index=True)  # 引用 SQLite 中的 words.id


class Favorite(FavoriteBase, table=True):
    """收藏数据库模型 (存储在 MySQL)"""
    __tablename__ = "favorites"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)


class FavoriteCreate(SQLModel):
    """收藏创建模型"""
    word_id: int


class FavoriteRead(FavoriteBase):
    """收藏读取模型"""
    id: int
    created_at: datetime


class SearchHistoryBase(SQLModel):
    """搜索历史基础模型"""
    user_id: int = Field(foreign_key="users.id", index=True)
    keyword: str
    result_count: int = 0


class SearchHistory(SearchHistoryBase, table=True):
    """搜索历史数据库模型 (存储在 MySQL)"""
    __tablename__ = "search_history"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)


class SearchHistoryCreate(SQLModel):
    """搜索历史创建模型"""
    keyword: str
    result_count: int = 0


class SearchHistoryRead(SearchHistoryBase):
    """搜索历史读取模型"""
    id: int
    created_at: datetime
