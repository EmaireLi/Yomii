"""
作文模型 (MySQL - 用户行为数据库)
"""
from datetime import datetime
from typing import Optional

from sqlalchemy import Column, Text
from sqlmodel import Field, SQLModel


class EssayBase(SQLModel):
    """作文基础模型"""

    title: str
    content: str
    topic: str
    word_count: int
    target_level: str = "N3"


class Essay(EssayBase, table=True):
    """作文数据库模型 (存储在 MySQL)"""

    __tablename__ = "essays"

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id", index=True)
    status: str = Field(default="pending", index=True)
    submit_time: datetime = Field(default_factory=datetime.utcnow)
    evaluation_requested_at: Optional[datetime] = None
    evaluation_completed_at: Optional[datetime] = None
    last_error: str = Field(default="", sa_column=Column(Text, nullable=False))


class EssayScoreBase(SQLModel):
    """作文评分基础模型"""

    essay_id: int = Field(foreign_key="essays.id", index=True)
    overall_score: int = 0
    task_completion_score: int = 0
    grammar_score: int = 0
    vocabulary_score: int = 0
    coherence_score: int = 0
    naturalness_score: int = 0
    jlpt_fit_score: int = 0
    level_estimate: str = "N5"
    summary: str = ""
    comments: str = ""
    ai_evaluated: bool = False
    model_version: str = ""


class EssayScore(EssayScoreBase, table=True):
    """作文评分数据库模型 (存储在 MySQL)"""

    __tablename__ = "essay_scores"

    id: Optional[int] = Field(default=None, primary_key=True)
    evaluation_time: datetime = Field(default_factory=datetime.utcnow)


class EssayRevisionBase(SQLModel):
    """作文修改建议基础模型"""

    essay_id: int = Field(foreign_key="essays.id", index=True)
    issues_json: str = Field(default="[]", sa_column=Column(Text, nullable=False))
    sentence_suggestions_json: str = Field(default="[]", sa_column=Column(Text, nullable=False))
    full_revision: str = Field(default="", sa_column=Column(Text, nullable=False))
    revision_notes: str = Field(default="", sa_column=Column(Text, nullable=False))
    model_version: str = ""


class EssayRevision(EssayRevisionBase, table=True):
    """作文修改建议数据库模型"""

    __tablename__ = "essay_revisions"

    id: Optional[int] = Field(default=None, primary_key=True)
    generated_at: datetime = Field(default_factory=datetime.utcnow)


class EssayJobBase(SQLModel):
    """作文评测任务基础模型"""

    essay_id: int = Field(foreign_key="essays.id", index=True)
    status: str = Field(default="pending", index=True)
    error_message: str = Field(default="", sa_column=Column(Text, nullable=False))
    score_model_version: str = ""
    revision_model_version: str = ""


class EssayJob(EssayJobBase, table=True):
    """作文评测任务数据库模型"""

    __tablename__ = "essay_jobs"

    id: Optional[int] = Field(default=None, primary_key=True)
    started_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None


class EssayCreate(EssayBase):
    """作文创建模型"""


class EssayRead(EssayBase):
    """作文读取模型"""

    id: int
    submit_time: datetime
    status: str


class EssayScoreRead(EssayScoreBase):
    """作文评分读取模型"""

    id: int
    evaluation_time: datetime


class EssayRevisionRead(EssayRevisionBase):
    """作文修改建议读取模型"""

    id: int
    generated_at: datetime


class EssayJobRead(EssayJobBase):
    """作文任务读取模型"""

    id: int
    started_at: datetime
    completed_at: Optional[datetime]
