"""
复习调度 API
"""
from __future__ import annotations

from datetime import datetime
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlmodel import select

from app.core.deps import DictDB, UserDB, get_current_active_user
from app.models.progress import WordProgress
from app.models.user import User
from app.models.word import Word, WordRead, WordTag
from app.services.review_service import (
    apply_review,
    create_initial_progress,
    to_review_progress_payload,
    weighted_sample_progress,
)

router = APIRouter()


class ReviewSubmit(BaseModel):
    rating: Literal["again", "hard", "good"]


async def _load_tags_map(dict_db: DictDB, word_ids: list[int]) -> dict[int, list[str]]:
    if not word_ids:
        return {}
    statement = select(WordTag).where(WordTag.word_id.in_(word_ids))
    result = await dict_db.exec(statement)
    tags = result.all()
    tags_map: dict[int, list[str]] = {}
    for tag in tags:
        tags_map.setdefault(tag.word_id, []).append(tag.tag)
    return tags_map


async def _fetch_words_by_ids(dict_db: DictDB, word_ids: list[int]) -> dict[int, WordRead]:
    if not word_ids:
        return {}
    statement = select(Word).where(Word.id.in_(word_ids))
    result = await dict_db.exec(statement)
    words = result.all()
    tags_map = await _load_tags_map(dict_db, word_ids)

    payload: dict[int, WordRead] = {}
    for word in words:
        if word.id is None:
            continue
        payload[word.id] = WordRead(
            id=word.id,
            word=word.word,
            kana=word.kana,
            japanese_meaning=word.japanese_meaning,
            chinese_meaning=word.chinese_meaning,
            example=word.example,
            part_of_speech=word.part_of_speech,
            audio_url=word.audio_url,
            tags=tags_map.get(word.id, []),
        )
    return payload


def _merge_word_and_progress_items(
    rows: list[WordProgress],
    words_by_id: dict[int, WordRead],
) -> list[dict]:
    items: list[dict] = []
    for row in rows:
        word_payload = words_by_id.get(row.word_id)
        if word_payload is None:
            continue
        items.append(
            {
                "word": word_payload.model_dump(),
                "progress": to_review_progress_payload(row),
            }
        )
    return items


@router.post("/{word_id}", response_model=dict)
async def submit_review_feedback(
    word_id: str,
    submit: ReviewSubmit,
    user_db: UserDB,
    dict_db: DictDB,
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> dict:
    """提交单词复习反馈（again / hard / good）"""
    try:
        parsed_word_id = int(word_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="word_id 必须是数字") from exc

    word_result = await dict_db.exec(select(Word).where(Word.id == parsed_word_id))
    word = word_result.first()
    if word is None:
        raise HTTPException(status_code=404, detail="单词不存在")

    progress_statement = select(WordProgress).where(
        WordProgress.user_id == current_user.id,
        WordProgress.word_id == parsed_word_id,
    )
    progress_result = await user_db.exec(progress_statement)
    progress = progress_result.first()

    now = datetime.utcnow()
    if progress is None:
        progress = create_initial_progress(current_user.id or 0, parsed_word_id, now=now)
    apply_review(progress, submit.rating, now=now)
    user_db.add(progress)
    await user_db.commit()
    await user_db.refresh(progress)

    tags_map = await _load_tags_map(dict_db, [parsed_word_id])
    word_payload = WordRead(
        id=word.id or 0,
        word=word.word,
        kana=word.kana,
        japanese_meaning=word.japanese_meaning,
        chinese_meaning=word.chinese_meaning,
        example=word.example,
        part_of_speech=word.part_of_speech,
        audio_url=word.audio_url,
        tags=tags_map.get(parsed_word_id, []),
    )
    return {
        "success": True,
        "rating": submit.rating,
        "word": word_payload.model_dump(),
        "progress": to_review_progress_payload(progress),
    }


@router.get("/today", response_model=dict)
async def get_today_review_words(
    user_db: UserDB,
    dict_db: DictDB,
    current_user: Annotated[User, Depends(get_current_active_user)],
    limit: int = Query(100, ge=1, le=500),
) -> dict:
    """获取今日到期复习任务（next_review <= now）"""
    now = datetime.utcnow()
    statement = (
        select(WordProgress)
        .where(
            WordProgress.user_id == current_user.id,
            WordProgress.next_review <= now,
        )
        .order_by(WordProgress.next_review.asc(), WordProgress.word_id.asc())
        .limit(limit)
    )
    result = await user_db.exec(statement)
    rows = result.all()
    words_by_id = await _fetch_words_by_ids(dict_db, [row.word_id for row in rows])

    return {
        "items": _merge_word_and_progress_items(rows, words_by_id),
        "count": len(rows),
        "limit": limit,
        "timestamp": int(now.timestamp() * 1000),
    }


@router.get("/random", response_model=dict)
async def get_random_review_words(
    user_db: UserDB,
    dict_db: DictDB,
    current_user: Annotated[User, Depends(get_current_active_user)],
    limit: int = Query(20, ge=1, le=200),
) -> dict:
    """强化练习（按权重随机抽取）"""
    statement = select(WordProgress).where(WordProgress.user_id == current_user.id)
    result = await user_db.exec(statement)
    rows = result.all()
    sampled_rows = weighted_sample_progress(rows, limit=limit)
    words_by_id = await _fetch_words_by_ids(dict_db, [row.word_id for row in sampled_rows])

    return {
        "items": _merge_word_and_progress_items(sampled_rows, words_by_id),
        "count": len(sampled_rows),
        "limit": limit,
    }
