"""
用户相关 API
"""
from typing import List

from fastapi import APIRouter

from app.core.deps import UserDB
from app.models.progress import WordProgress, WordProgressCreate
from app.models.word import Word

router = APIRouter()


@router.get("/stats", response_model=dict)
async def get_study_stats(
    db: UserDB
) -> dict:
    """获取学习统计 (从 MySQL 用户数据库)"""
    # TODO: 实现统计逻辑
    return {
        "totalWordsLearned": 0,
        "totalWordsRecited": 0,
        "todayLearned": 0,
        "todayRecited": 0,
        "currentStreak": 0,
        "longestStreak": 0,
        "lastStudyDate": 0
    }


@router.get("/progress", response_model=List[dict])
async def get_user_progress(
    db: UserDB
) -> List[dict]:
    """获取学习进度 (从 MySQL 用户数据库)"""
    # TODO: 实现获取进度逻辑
    return []


@router.post("/progress/{word_id}", response_model=dict)
async def update_word_progress(
    db: UserDB,
    word_id: str,
    progress_in: WordProgressCreate
) -> dict:
    """
    更新单词学习进度 (保存到 MySQL 用户数据库)
    
    - **word_id**: 单词 ID (来自 SQLite 词典)
    - **status**: 学习状态 (unknown/fuzzy/known)
    - **is_correct**: 是否答对
    """
    # TODO: 实现更新进度逻辑
    return {
        "wordId": word_id,
        "status": progress_in.status,
        "reviewCount": 1,
        "correctCount": 1 if progress_in.is_correct else 0,
        "lastReviewedAt": 0
    }


@router.get("/search-history", response_model=List[dict])
async def get_search_history(
    db: UserDB,
    limit: int = 10
) -> List[dict]:
    """获取搜索历史 (从 MySQL 用户数据库)"""
    # TODO: 实现搜索历史逻辑
    return []


@router.get("/favorites", response_model=List[dict])
async def get_favorites(
    db: UserDB
) -> List[dict]:
    """获取收藏列表 (从 MySQL 用户数据库)"""
    # TODO: 实现收藏列表逻辑
    return []


@router.post("/favorites/{word_id}", response_model=dict)
async def add_to_favorites(
    db: UserDB,
    word_id: str
) -> dict:
    """添加到收藏夹 (保存到 MySQL 用户数据库)"""
    # TODO: 实现添加收藏逻辑
    return {"success": True}


@router.delete("/favorites/{word_id}", response_model=dict)
async def remove_from_favorites(
    db: UserDB,
    word_id: str
) -> dict:
    """从收藏夹移除 (从 MySQL 用户数据库删除)"""
    # TODO: 实现移除收藏逻辑
    return {"success": True}
