"""
用户相关 API
"""
from datetime import datetime
from typing import Annotated, List

from fastapi import APIRouter, Depends, Query, HTTPException
from sqlmodel import delete, select
from sqlalchemy.orm import selectinload
from sqlalchemy import func

from app.core.deps import UserDB, DictDB, get_current_active_user
from app.models.favorite import SearchHistory, Favorite
from app.models.progress import WordProgress, WordProgressCreate
from app.models.user import User
from app.models.word import Word
from app.services.review_service import (
    apply_review,
    create_initial_progress,
    status_to_rating,
    to_review_progress_payload,
)
from app.services.stats_service import study_stats_service

router = APIRouter()


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
    db: UserDB,
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> List[dict]:
    """获取学习进度 (从 MySQL 用户数据库)"""
    statement = (
        select(WordProgress)
        .where(WordProgress.user_id == current_user.id)
        .order_by(WordProgress.last_review.desc())
    )
    result = await db.exec(statement)
    records = result.all()

    payload: list[dict] = []
    for record in records:
        item = to_review_progress_payload(record)
        item["lastReviewedAt"] = item["lastReview"]
        payload.append(item)
    return payload


@router.post("/progress/{word_id}", response_model=dict)
async def update_word_progress(
    db: UserDB,
    word_id: str,
    progress_in: WordProgressCreate,
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> dict:
    """
    更新单词学习进度 (保存到 MySQL 用户数据库)
    
    - **word_id**: 单词 ID (来自 SQLite 词典)
    - **status**: 学习状态 (unknown/fuzzy/known)
    - **is_correct**: 是否答对
    """
    try:
        parsed_word_id = int(word_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="word_id 必须是数字") from exc

    now = datetime.utcnow()
    statement = select(WordProgress).where(
        (WordProgress.user_id == current_user.id) & (WordProgress.word_id == parsed_word_id)
    )
    result = await db.exec(statement)
    progress = result.first()

    if progress is None:
        progress = create_initial_progress(current_user.id or 0, parsed_word_id, now=now)

    rating = status_to_rating(progress_in.status, progress_in.is_correct)
    apply_review(progress, rating, now=now)
    db.add(progress)

    await db.commit()
    await db.refresh(progress)
    response_payload = to_review_progress_payload(progress)
    response_payload["lastReviewedAt"] = response_payload["lastReview"]
    return response_payload


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


@router.delete("/search-history", response_model=dict)
async def delete_search_history(
    db: UserDB,
    current_user: Annotated[User, Depends(get_current_active_user)],
    keyword: str | None = Query(None, description="删除指定关键词；不传则清空全部"),
) -> dict:
    """删除搜索历史 (从 MySQL 用户数据库删除)"""
    if current_user.id is None:
        raise HTTPException(status_code=401, detail="未授权")

    statement = delete(SearchHistory).where(SearchHistory.user_id == current_user.id)
    normalized_keyword = keyword.strip() if isinstance(keyword, str) else ""
    if normalized_keyword:
        statement = statement.where(SearchHistory.keyword == normalized_keyword)

    result = await db.exec(statement)
    await db.commit()

    return {
        "success": True,
        "deletedCount": int(result.rowcount or 0),
        "message": "删除成功",
    }


@router.get("/favorites", response_model=dict)
async def get_favorites(
    user_db: UserDB,
    dict_db: DictDB,
    current_user: Annotated[User, Depends(get_current_active_user)],
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100)
) -> dict:
    """获取用户的收藏列表 (从 MySQL 用户数据库)"""
    if current_user.id is None:
        return {"words": [], "total": 0, "page": page, "limit": limit}

    # 获取总数
    count_statement = select(func.count()).select_from(Favorite).where(Favorite.user_id == current_user.id)
    count_result = await user_db.exec(count_statement)
    total = count_result.one()

    offset = (page - 1) * limit

    # 只查询当前页的收藏词 ID（按收藏时间倒序）
    page_favorites_statement = (
        select(Favorite.word_id)
        .where(Favorite.user_id == current_user.id)
        .order_by(Favorite.id.desc())
        .offset(offset)
        .limit(limit)
    )
    page_favorites_result = await user_db.exec(page_favorites_statement)
    page_word_ids = page_favorites_result.all()
    
    if not page_word_ids:
        return {"words": [], "total": total, "page": page, "limit": limit}

    # 读取当前页单词详情，并按收藏顺序组装返回
    word_statement = (
        select(Word)
        .where(Word.id.in_(page_word_ids))
        .options(selectinload(Word.tags))
    )
    word_result = await dict_db.exec(word_statement)
    words = word_result.all()
    words_by_id = {word.id: word for word in words if word.id is not None}

    # 返回收藏的单词信息（按收藏时间倒序）
    result_list = []
    for word_id in page_word_ids:
        word = words_by_id.get(word_id)
        if word is None:
            continue
        tags = [tag.tag for tag in word.tags] if word.tags else []
        
        result_list.append({
            "id": word.id,
            "word": word.word,
            "kana": word.kana,
            "japaneseMeaning": word.japanese_meaning,
            "chineseMeaning": word.chinese_meaning,
            "example": word.example,
            "partOfSpeech": word.part_of_speech,
            "audioUrl": word.audio_url,
            "tags": tags,
        })
    
    return {"words": result_list, "total": total, "page": page, "limit": limit}


@router.post("/favorites/{word_id}", response_model=dict)
async def add_to_favorites(
    user_db: UserDB,
    current_user: Annotated[User, Depends(get_current_active_user)],
    word_id: int
) -> dict:
    """添加到收藏夹 (保存到 MySQL 用户数据库)"""
    if current_user.id is None:
        raise HTTPException(status_code=401, detail="未授权")

    # 检查是否已收藏
    statement = select(Favorite).where(
        (Favorite.user_id == current_user.id) & (Favorite.word_id == word_id)
    )
    result = await user_db.exec(statement)
    existing = result.first()

    if existing:
        return {"success": True, "message": "已收藏"}

    # 添加到收藏夹
    favorite = Favorite(user_id=current_user.id, word_id=word_id)
    user_db.add(favorite)
    await user_db.commit()
    await user_db.refresh(favorite)

    return {"success": True, "message": "收藏成功"}


@router.delete("/favorites/{word_id}", response_model=dict)
async def remove_from_favorites(
    user_db: UserDB,
    current_user: Annotated[User, Depends(get_current_active_user)],
    word_id: int
) -> dict:
    """从收藏夹移除 (从 MySQL 用户数据库删除)"""
    if current_user.id is None:
        raise HTTPException(status_code=401, detail="未授权")

    # 删除收藏记录
    statement = select(Favorite).where(
        (Favorite.user_id == current_user.id) & (Favorite.word_id == word_id)
    )
    result = await user_db.exec(statement)
    favorite = result.first()

    if favorite:
        await user_db.delete(favorite)
        await user_db.commit()
        return {"success": True, "message": "已取消收藏"}

    return {"success": True, "message": "收藏记录不存在"}
