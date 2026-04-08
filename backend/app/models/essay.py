"""
作文模型 (MySQL - 用户行为数据库)
"""
from datetime import datetime
from typing import Optional
from sqlmodel import SQLModel, Field


class EssayBase(SQLModel):
    """作文基础模型"""
    title: str
    content: str
    topic: str
    word_count: int


class Essay(EssayBase, table=True):
    """作文数据库模型 (存储在 MySQL)"""
    __tablename__ = "essays"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id", index=True)
    submit_time: datetime = Field(default_factory=datetime.utcnow)


class EssayScoreBase(SQLModel):
    """作文评分基础模型"""
    essay_id: int = Field(foreign_key="essays.id", index=True)
    overall_score: int
    grammar_score: int
    vocabulary_score: int
    fluency_score: int
    coherence_score: int
    comments: str
    ai_evaluated: bool = False


class EssayScore(EssayScoreBase, table=True):
    """作文评分数据库模型 (存储在 MySQL)"""
    __tablename__ = "essay_scores"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    evaluation_time: datetime = Field(default_factory=datetime.utcnow)


class EssayCreate(EssayBase):
    """作文创建模型"""
    pass


class EssayRead(EssayBase):
    """作文读取模型"""
    id: int
    submit_time: datetime
    score: Optional[EssayScoreBase] = None


class EssayScoreRead(EssayScoreBase):
    """作文评分读取模型"""
    id: int
    evaluation_time: datetime
