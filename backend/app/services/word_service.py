"""
单词服务
"""
from collections import defaultdict
from typing import List, Optional

from sqlalchemy import func, or_
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import select

from app.models.word import Word, WordCreate, WordRead, WordTag


class WordService:
    """单词服务"""

    async def _load_tags_map(
        self,
        db: AsyncSession,
        word_ids: List[int]
    ) -> dict[int, List[str]]:
        """批量加载单词标签"""
        if not word_ids:
            return {}

        statement = select(WordTag).where(WordTag.word_id.in_(word_ids))
        result = await db.exec(statement)
        tags = result.all()

        tags_map: dict[int, List[str]] = defaultdict(list)
        for tag in tags:
            tags_map[tag.word_id].append(tag.tag)
        return tags_map

    def _to_word_read(self, word: Word, tags: List[str]) -> WordRead:
        """转换为 API 返回模型"""
        return WordRead(
            id=word.id or 0,
            word=word.word,
            kana=word.kana,
            japanese_meaning=word.japanese_meaning,
            chinese_meaning=word.chinese_meaning,
            example=word.example,
            part_of_speech=word.part_of_speech,
            audio_url=word.audio_url,
            tags=tags,
        )
    
    async def search(
        self,
        db: AsyncSession,
        keyword: str,
        limit: int = 10
    ) -> List[WordRead]:
        """搜索单词"""
        normalized_keyword = keyword.strip()
        if not normalized_keyword:
            return []

        statement = (
            select(Word)
            .where(
                or_(
                    Word.word.contains(normalized_keyword),
                    Word.kana.contains(normalized_keyword),
                    Word.japanese_meaning.contains(normalized_keyword),
                    Word.chinese_meaning.contains(normalized_keyword),
                )
            )
            .order_by(Word.id.asc())
            .limit(limit)
        )
        result = await db.exec(statement)
        words = result.all()

        tags_map = await self._load_tags_map(
            db,
            [word.id for word in words if word.id is not None],
        )
        return [self._to_word_read(word, tags_map.get(word.id or 0, [])) for word in words]
    
    async def get(self, db: AsyncSession, word_id: int) -> Optional[WordRead]:
        """获取单词详情"""
        statement = select(Word).where(Word.id == word_id)
        result = await db.exec(statement)
        word = result.first()
        if not word:
            return None

        tags_map = await self._load_tags_map(db, [word_id])
        return self._to_word_read(word, tags_map.get(word_id, []))
    
    async def get_random(self, db: AsyncSession, count: int = 5) -> List[WordRead]:
        """获取随机单词"""
        statement = select(Word).order_by(func.random()).limit(count)
        result = await db.exec(statement)
        words = result.all()

        tags_map = await self._load_tags_map(
            db,
            [word.id for word in words if word.id is not None],
        )
        return [self._to_word_read(word, tags_map.get(word.id or 0, [])) for word in words]
    
    async def get_all(
        self,
        db: AsyncSession,
        page: int = 1,
        limit: int = 20
    ) -> tuple[List[WordRead], int]:
        """获取所有单词（分页）"""
        offset = (page - 1) * limit

        count_statement = select(func.count()).select_from(Word)
        total_result = await db.exec(count_statement)
        total = total_result.one()

        statement = (
            select(Word)
            .order_by(Word.id.asc())
            .offset(offset)
            .limit(limit)
        )
        result = await db.exec(statement)
        words = result.all()

        tags_map = await self._load_tags_map(
            db,
            [word.id for word in words if word.id is not None],
        )
        return (
            [self._to_word_read(word, tags_map.get(word.id or 0, [])) for word in words],
            total,
        )
    
    async def create(self, db: AsyncSession, word_in: WordCreate) -> WordRead:
        """创建单词"""
        word = Word(
            word=word_in.word,
            kana=word_in.kana,
            japanese_meaning=word_in.japanese_meaning,
            chinese_meaning=word_in.chinese_meaning,
            example=word_in.example,
            part_of_speech=word_in.part_of_speech,
            audio_url=word_in.audio_url,
        )
        db.add(word)
        await db.commit()
        await db.refresh(word)

        if word_in.tags and word.id is not None:
            for tag in word_in.tags:
                db.add(WordTag(word_id=word.id, tag=tag))
            await db.commit()

        created = await self.get(db, word.id or 0)
        if not created:
            raise ValueError("创建单词失败")
        return created


word_service = WordService()
