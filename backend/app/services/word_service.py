"""
单词服务
"""
from typing import List, Optional
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import select

from app.models.word import Word, WordCreate


class WordService:
    """单词服务"""
    
    async def search(
        self,
        db: AsyncSession,
        keyword: str,
        limit: int = 10
    ) -> List[Word]:
        """搜索单词"""
        # TODO: 实现搜索逻辑
        # statement = select(Word).where(
        #     Word.word.contains(keyword) | 
        #     Word.kana.contains(keyword) |
        #     Word.meaning.contains(keyword)
        # ).limit(limit)
        # result = await db.exec(statement)
        # return result.all()
        pass
    
    async def get(self, db: AsyncSession, word_id: int) -> Optional[Word]:
        """获取单词详情"""
        # TODO: 实现获取逻辑
        pass
    
    async def get_random(self, db: AsyncSession, count: int = 5) -> List[Word]:
        """获取随机单词"""
        # TODO: 实现随机获取逻辑
        pass
    
    async def get_all(
        self,
        db: AsyncSession,
        page: int = 1,
        limit: int = 20
    ) -> tuple[List[Word], int]:
        """获取所有单词（分页）"""
        # TODO: 实现分页获取逻辑
        pass
    
    async def create(self, db: AsyncSession, word_in: WordCreate) -> Word:
        """创建单词"""
        # TODO: 实现创建逻辑
        pass


word_service = WordService()
