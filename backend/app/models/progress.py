"""
学习进度模型 (MySQL - 用户行为数据库)
"""
from datetime import datetime, timedelta
from enum import Enum
from typing import Optional
from sqlmodel import SQLModel, Field


class ProgressStatus(str, Enum):
    """学习状态"""
    UNKNOWN = "unknown"
    FUZZY = "fuzzy"
    KNOWN = "known"


class WordProgressBase(SQLModel):
    """单词学习进度基础模型"""
    user_id: int = Field(foreign_key="users.id", index=True)
    word_id: int = Field(index=True)  # 引用 SQLite 中的 word.id
    status: ProgressStatus = ProgressStatus.UNKNOWN
    interval: float = 0.02
    ease: float = 2.5
    review_count: int = 0
    lapse_count: int = 0
    correct_count: int = 0
    next_review: datetime = Field(default_factory=lambda: datetime.utcnow() + timedelta(days=0.02), index=True)


class WordProgress(WordProgressBase, table=True):
    """单词学习进度数据库模型 (存储在 MySQL)"""
    __tablename__ = "word_progress"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    last_review: datetime = Field(default_factory=datetime.utcnow)
    created_at: datetime = Field(default_factory=datetime.utcnow)


class WordProgressCreate(SQLModel):
    """学习进度创建模型"""
    word_id: int
    status: ProgressStatus
    is_correct: bool = True


class WordProgressRead(WordProgressBase):
    """学习进度读取模型"""
    id: int
    last_review: datetime
    created_at: datetime
