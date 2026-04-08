"""
测试相关模型
- QuizQuestion: SQLite (词典数据库)
- QuizResult: MySQL (用户行为数据库)
"""
from datetime import datetime
from enum import Enum
from typing import Optional, List
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
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class QuizSubmit(SQLModel):
    """测试提交模型"""
    question_id: int
    user_answer: str
    is_correct: bool
