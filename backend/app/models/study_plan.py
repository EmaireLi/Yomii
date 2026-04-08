"""
学习计划模型 (MySQL - 用户行为数据库)
"""
from datetime import datetime
from typing import Optional, List
from sqlmodel import SQLModel, Field


class StudyPlanBase(SQLModel):
    """学习计划基础模型"""
    name: str
    daily_goal: int = 10
    review_ratio: float = 0.5
    is_active: bool = False


class StudyPlan(StudyPlanBase, table=True):
    """学习计划数据库模型 (存储在 MySQL)"""
    __tablename__ = "study_plans"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id", index=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class LearningSessionBase(SQLModel):
    """学习轮次基础模型"""
    plan_id: int = Field(foreign_key="study_plans.id", index=True)
    date: str  # YYYY-MM-DD 格式
    learned_words: str  # JSON 字符串存储单词ID列表
    reviewed_words: str  # JSON 字符串存储单词ID列表
    known_count: int = 0
    fuzzy_count: int = 0
    unknown_count: int = 0


class LearningSession(LearningSessionBase, table=True):
    """学习轮次数据库模型 (存储在 MySQL)"""
    __tablename__ = "learning_sessions"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    completed_at: Optional[datetime] = None


class StudyPlanCreate(SQLModel):
    """学习计划创建模型"""
    name: str
    daily_goal: int = 10
    review_ratio: float = 0.5


class StudyPlanUpdate(SQLModel):
    """学习计划更新模型"""
    name: Optional[str] = None
    daily_goal: Optional[int] = None
    review_ratio: Optional[float] = None
    is_active: Optional[bool] = None


class LearningSessionCreate(SQLModel):
    """学习轮次创建模型"""
    date: str
    learned_words: List[str]
    reviewed_words: List[str]
    known_count: int
    fuzzy_count: int
    unknown_count: int
