"""
测试相关模型
- QuizQuestion: SQLite (词典数据库)
- QuizSession/QuizResult: MySQL (用户行为数据库)
"""
from datetime import datetime
from enum import Enum
from typing import Optional
from sqlmodel import SQLModel, Field


class QuestionType(str, Enum):
    """题目类型"""
    MULTIPLE_CHOICE = "multiple-choice"
    FILL_BLANK = "fill-blank"
    LISTENING = "listening"


class QuizQuestionBase(SQLModel):
    """测试题目基础模型"""
    type: QuestionType
    question: str
    word_id: int = Field(foreign_key="words.id")
    options: str  # JSON 字符串存储选项列表
    correct_answer: str
    explanation: str


class QuizQuestion(QuizQuestionBase, table=True):
    """测试题目数据库模型 (存储在 SQLite)"""
    __tablename__ = "quiz_questions"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    difficulty: str = "medium"
    created_at: datetime = Field(default_factory=datetime.utcnow)


class QuizResultBase(SQLModel):
    """测试结果基础模型"""
    user_id: int = Field(foreign_key="users.id", index=True)
    question_id: int = Field(index=True)  # 引用 SQLite 中的 quiz_questions.id
    user_answer: str
    is_correct: bool


class QuizResult(QuizResultBase, table=True):
    """测试结果数据库模型 (存储在 MySQL)"""
    __tablename__ = "quiz_results"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    session_id: Optional[int] = Field(default=None, foreign_key="quiz_sessions.id", index=True)
    difficulty: str = Field(default="medium", index=True)
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class QuizSubmit(SQLModel):
    """测试提交模型"""
    question_id: int
    user_answer: str
    is_correct: bool


class QuizAnswerItem(SQLModel):
    """一次测试中的单题答题记录"""
    question_id: int
    user_answer: str
    is_correct: bool


class QuizSessionBase(SQLModel):
    """测试会话基础模型"""
    user_id: int = Field(foreign_key="users.id", index=True)
    difficulty: str = Field(default="medium", index=True)
    total_questions: int = Field(default=0, ge=0)
    correct_answers: int = Field(default=0, ge=0)
    accuracy: float = Field(default=0.0, ge=0.0, le=1.0)
    duration_seconds: int = Field(default=0, ge=0)
    ability_score: float = Field(default=0.0, ge=0.0, le=100.0)
    report_level: str = Field(default="入门")
    report_summary: str = Field(default="")
    trend_delta: float = Field(default=0.0)


class QuizSession(QuizSessionBase, table=True):
    """测试会话记录（历史记录主表）"""
    __tablename__ = "quiz_sessions"

    id: Optional[int] = Field(default=None, primary_key=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)


class QuizSessionSubmit(SQLModel):
    """提交整场测试结果"""
    difficulty: str = Field(default="medium")
    total_questions: int = Field(ge=1, le=100)
    correct_answers: int = Field(ge=0, le=100)
    duration_seconds: int = Field(default=0, ge=0)
    answers: list[QuizAnswerItem] = Field(default_factory=list)
