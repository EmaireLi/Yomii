"""
单词模型 (SQLite - 词典数据库)
"""
from datetime import datetime
from typing import Optional, List
from sqlmodel import SQLModel, Field, Relationship


class WordBase(SQLModel):
    """单词基础模型"""
    word: str = Field(index=True)
    kana: str
    japanese_meaning: str
    chinese_meaning: str = ""
    example: str
    part_of_speech: Optional[str] = None
    audio_url: Optional[str] = None


class Word(WordBase, table=True):
    """单词数据库模型 (存储在 SQLite)"""
    __tablename__ = "words"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    # 关联标签
    tags: List["WordTag"] = Relationship(back_populates="word")


class WordTag(SQLModel, table=True):
    """单词标签关联表 (存储在 SQLite)"""
    __tablename__ = "word_tags"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    word_id: int = Field(foreign_key="words.id")
    tag: str = Field(index=True)
    
    word: Optional[Word] = Relationship(back_populates="tags")


class WordCreate(WordBase):
    """单词创建模型"""
    tags: Optional[List[str]] = None


class WordRead(WordBase):
    """单词读取模型"""
    id: int
    tags: List[str] = Field(default_factory=list)
