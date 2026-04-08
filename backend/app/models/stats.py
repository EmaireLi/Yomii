"""
学习统计模型 (MySQL - 用户行为数据库)
"""
from datetime import datetime, date
from typing import Optional
from sqlmodel import SQLModel, Field


class StudyStatsBase(SQLModel):
    """学习统计基础模型"""
    total_words_learned: int = 0
    total_words_recited: int = 0
    today_learned: int = 0
    today_recited: int = 0
    current_streak: int = 0
    longest_streak: int = 0
    last_study_date: Optional[date] = None


class StudyStats(StudyStatsBase, table=True):
    """学习统计数据库模型 (存储在 MySQL)"""
    __tablename__ = "study_stats"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id", unique=True, index=True)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class StudyStatsUpdate(SQLModel):
    """学习统计更新模型"""
    total_words_learned: Optional[int] = None
    total_words_recited: Optional[int] = None
    today_learned: Optional[int] = None
    today_recited: Optional[int] = None
    current_streak: Optional[int] = None
    longest_streak: Optional[int] = None
    last_study_date: Optional[date] = None


class StudyStatsRead(StudyStatsBase):
    """学习统计读取模型"""
    id: int
    user_id: int
    updated_at: datetime
