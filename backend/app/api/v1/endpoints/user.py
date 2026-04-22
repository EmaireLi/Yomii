"""
用户相关 API
"""
from typing import Annotated, List

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import or_
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.deps import DictDB, UserDB, get_current_active_user
from app.models.favorite import Favorite, SearchHistory
from app.models.progress import WordProgress, WordProgressCreate
from app.models.user import User
from app.models.word import Word, WordTag
from app.services.stats_service import study_stats_service

router = APIRouter()


def _serialize_word(word: Word, tags_map: dict[int, list[str]]) -> dict:
    return {
        "id": word.id,
        "word": word.word,
        "kana": word.kana,
        "japanese_meaning": word.japanese_meaning,
        "chinese_meaning": word.chinese_meaning,
        "example": word.example,
        "part_of_speech": word.part_of_speech,
        "audio_url": word.audio_url,
        "tags": tags_map.get(word.id or 0, []),
    }


def _deduplicate_word_ids(word_ids: list[int]) -> list[int]:
    seen: set[int] = set()
    deduped: list[int] = []
    for word_id in word_ids:
        if word_id in seen:
            continue
        seen.add(word_id)
        deduped.append(word_id)
    return deduped


async def _load_tags_map(dict_db: AsyncSession, word_ids: list[int]) -> dict[int, list[str]]:
    if not word_ids:
        return {}
    tag_statement = select(WordTag).where(WordTag.word_id.in_(word_ids))
    tag_result = await dict_db.exec(tag_statement)
    tags = tag_result.all()
    tags_map: dict[int, list[str]] = {}
    for tag in tags:
        tags_map.setdefault(tag.word_id, []).append(tag.tag)
    return tags_map


async def _resolve_favorite_words(
    dict_db: AsyncSession,
    ordered_word_ids: list[int],
    keyword: str = "",
    page: int = 1,
    limit: int = 10,
) -> tuple[list[dict], int]:
    if not ordered_word_ids:
        return [], 0

    normalized_keyword = keyword.strip()
    word_statement = select(Word).where(Word.id.in_(ordered_word_ids))
    if normalized_keyword:
        word_statement = word_statement.where(
            or_(
                Word.word.contains(normalized_keyword),
                Word.kana.contains(normalized_keyword),
                Word.chinese_meaning.contains(normalized_keyword),
                Word.japanese_meaning.contains(normalized_keyword),
            )
        )
    word_result = await dict_db.exec(word_statement)
    words = word_result.all()
    words_by_id = {word.id: word for word in words if word.id is not None}

    matched_word_ids = [word_id for word_id in ordered_word_ids if word_id in words_by_id]
    total = len(matched_word_ids)
    if total == 0:
        return [], 0

    safe_page = max(1, page)
    safe_limit = max(1, limit)
    offset = (safe_page - 1) * safe_limit
    paged_word_ids = matched_word_ids[offset: offset + safe_limit]

    tags_map = await _load_tags_map(dict_db, paged_word_ids)
    payload = [_serialize_word(words_by_id[word_id], tags_map) for word_id in paged_word_ids]
    return payload, total


@router.get("/stats", response_model=dict)
async def get_study_stats(
    db: UserDB,
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> dict:
    """获取学习统计 (从 MySQL 用户数据库)"""
    if current_user.id is None:
        return {
            "totalWordsLearned": 0,
            "totalWordsRecited": 0,
            "todayLearned": 0,
            "todayRecited": 0,
            "currentStreak": 0,
            "longestStreak": 0,
            "lastStudyDate": 0,
        }

    stats, is_created = await study_stats_service.get_or_create(db, current_user.id)
    if is_created:
        await db.commit()
        await db.refresh(stats)
    return study_stats_service.to_response(stats)


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
    current_user: Annotated[User, Depends(get_current_active_user)],
    limit: int = Query(10, ge=1, le=100)
) -> List[dict]:
    """获取搜索历史 (从 MySQL 用户数据库)"""
    statement = (
        select(SearchHistory)
        .where(SearchHistory.user_id == current_user.id)
        .order_by(SearchHistory.created_at.desc())
        .limit(limit)
    )
    result = await db.exec(statement)
    records = result.all()

    return [
        {
            "id": record.id,
            "keyword": record.keyword,
            "resultCount": record.result_count,
            "createdAt": int(record.created_at.timestamp() * 1000),
        }
        for record in records
    ]


@router.get("/favorites", response_model=List[dict])
async def get_favorites(
    db: UserDB,
    dict_db: DictDB,
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> List[dict]:
    """获取收藏列表 (从 MySQL 用户数据库)"""
    statement = (
        select(Favorite)
        .where(Favorite.user_id == current_user.id)
        .order_by(Favorite.created_at.desc(), Favorite.id.desc())
    )
    result = await db.exec(statement)
    favorites = result.all()
    if not favorites:
        return []

    ordered_word_ids = _deduplicate_word_ids([favorite.word_id for favorite in favorites])
    words, _ = await _resolve_favorite_words(
        dict_db=dict_db,
        ordered_word_ids=ordered_word_ids,
        page=1,
        limit=max(1, len(ordered_word_ids)),
    )
    return words


@router.get("/favorites/search", response_model=dict)
async def search_favorites(
    db: UserDB,
    dict_db: DictDB,
    current_user: Annotated[User, Depends(get_current_active_user)],
    q: str = Query("", description="搜索关键词"),
    page: int = Query(1, ge=1, description="页码"),
    limit: int = Query(10, ge=1, le=100, description="每页数量"),
) -> dict:
    """
    搜索收藏词汇（默认按收藏时间倒序，最新收藏在前）
    """
    statement = (
        select(Favorite)
        .where(Favorite.user_id == current_user.id)
        .order_by(Favorite.created_at.desc(), Favorite.id.desc())
    )
    result = await db.exec(statement)
    favorites = result.all()
    ordered_word_ids = _deduplicate_word_ids([favorite.word_id for favorite in favorites])

    words, total = await _resolve_favorite_words(
        dict_db=dict_db,
        ordered_word_ids=ordered_word_ids,
        keyword=q,
        page=page,
        limit=limit,
    )
    return {"words": words, "total": total, "page": page, "limit": limit}


@router.post("/favorites/{word_id}", response_model=dict)
async def add_to_favorites(
    db: UserDB,
    dict_db: DictDB,
    current_user: Annotated[User, Depends(get_current_active_user)],
    word_id: str,
) -> dict:
    """添加到收藏夹 (保存到 MySQL 用户数据库)"""
    if current_user.id is None:
        raise HTTPException(status_code=401, detail="未登录")

    if not word_id.isdigit():
        raise HTTPException(status_code=400, detail="无效的单词ID")
    normalized_word_id = int(word_id)

    word_statement = select(Word).where(Word.id == normalized_word_id)
    word_result = await dict_db.exec(word_statement)
    if word_result.first() is None:
        raise HTTPException(status_code=404, detail="单词不存在")

    existed_statement = select(Favorite).where(
        Favorite.user_id == current_user.id,
        Favorite.word_id == normalized_word_id,
    )
    existed_result = await db.exec(existed_statement)
    if existed_result.first() is not None:
        return {"success": True}

    db.add(Favorite(user_id=current_user.id, word_id=normalized_word_id))
    await db.commit()
    return {"success": True}


@router.delete("/favorites/{word_id}", response_model=dict)
async def remove_from_favorites(
    db: UserDB,
    current_user: Annotated[User, Depends(get_current_active_user)],
    word_id: str,
) -> dict:
    """从收藏夹移除 (从 MySQL 用户数据库删除)"""
    if current_user.id is None:
        raise HTTPException(status_code=401, detail="未登录")
    if not word_id.isdigit():
        raise HTTPException(status_code=400, detail="无效的单词ID")

    normalized_word_id = int(word_id)
    statement = select(Favorite).where(
        Favorite.user_id == current_user.id,
        Favorite.word_id == normalized_word_id,
    )
    result = await db.exec(statement)
    favorite = result.first()
    if favorite is None:
        return {"success": True}

    await db.delete(favorite)
    await db.commit()
    return {"success": True}
