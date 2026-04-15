"""
学习计划相关 API
"""
from datetime import date, datetime
import json
from typing import Annotated, Any, List

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func
from sqlmodel import select

from app.core.deps import DictDB, UserDB, get_current_active_user
from app.models.progress import ProgressStatus, WordProgress
from app.models.study_plan import (
    LearningSession,
    LearningSessionCreate,
    StudyPlan,
    StudyPlanCreate,
    StudyPlanUpdate,
)
from app.models.user import User
from app.models.word import Word, WordRead, WordTag
from app.services.stats_service import study_stats_service

router = APIRouter()


DICTIONARY_TAG_MAP: dict[str, str] = {
    "jlpt1": "N1",
    "jlpt2": "N2",
    "jlpt3": "N3",
}


def _to_timestamp_ms(dt: datetime | None) -> int:
    if dt is None:
        return 0
    return int(dt.timestamp() * 1000)


def _to_study_plan_response(plan: StudyPlan) -> dict[str, Any]:
    return {
        "id": str(plan.id),
        "name": plan.name,
        "dailyGoal": plan.daily_goal,
        "reviewRatio": plan.review_ratio,
        "dictionaryId": plan.dictionary_id,
        "isActive": plan.is_active,
        "createdAt": _to_timestamp_ms(plan.created_at),
        "updatedAt": _to_timestamp_ms(plan.updated_at),
    }


def _parse_word_ids(raw_ids: list[str]) -> list[int]:
    word_ids: list[int] = []
    for raw_id in raw_ids:
        try:
            word_ids.append(int(raw_id))
        except (TypeError, ValueError):
            continue
    return word_ids


def _parse_json_word_ids(raw: str) -> list[str]:
    try:
        value = json.loads(raw)
        if isinstance(value, list):
            return [str(v) for v in value]
        return []
    except (TypeError, ValueError):
        return []


def _parse_session_date(raw_date: str) -> date:
    try:
        return datetime.strptime(raw_date, "%Y-%m-%d").date()
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="date 必须是 YYYY-MM-DD 格式") from exc


def _to_session_response(session: LearningSession) -> dict[str, Any]:
    return {
        "id": str(session.id),
        "planId": str(session.plan_id),
        "date": session.date,
        "learnedWords": _parse_json_word_ids(session.learned_words),
        "reviewedWords": _parse_json_word_ids(session.reviewed_words),
        "sessionStats": {
            "knownCount": session.known_count,
            "fuzzyCount": session.fuzzy_count,
            "unknownCount": session.unknown_count,
        },
        "completedAt": _to_timestamp_ms(session.completed_at) if session.completed_at else None,
    }


def _to_word_read(word: Word, tags: list[str]) -> WordRead:
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


async def _load_tags_map(dict_db: DictDB, word_ids: list[int]) -> dict[int, list[str]]:
    if not word_ids:
        return {}

    tag_statement = select(WordTag).where(WordTag.word_id.in_(word_ids))
    tag_result = await dict_db.exec(tag_statement)
    tags = tag_result.all()

    tags_map: dict[int, list[str]] = {}
    for tag in tags:
        tags_map.setdefault(tag.word_id, []).append(tag.tag)
    return tags_map


async def _fetch_words_by_ids(dict_db: DictDB, word_ids: list[int]) -> list[WordRead]:
    if not word_ids:
        return []

    statement = select(Word).where(Word.id.in_(word_ids))
    result = await dict_db.exec(statement)
    words = result.all()
    words_by_id = {word.id: word for word in words if word.id is not None}

    ordered_word_ids = [word_id for word_id in word_ids if word_id in words_by_id]
    tags_map = await _load_tags_map(dict_db, ordered_word_ids)
    return [
        _to_word_read(words_by_id[word_id], tags_map.get(word_id, []))
        for word_id in ordered_word_ids
    ]


async def _pick_random_words(
    dict_db: DictDB,
    limit: int,
    dictionary_id: str,
    exclude_ids: set[int] | None = None,
) -> list[WordRead]:
    if limit <= 0:
        return []

    excluded = exclude_ids or set()
    jlpt_tag = DICTIONARY_TAG_MAP.get(dictionary_id)

    async def query_words(only_jlpt_tag: bool) -> list[Word]:
        statement = select(Word)
        if only_jlpt_tag and jlpt_tag:
            statement = statement.join(WordTag, WordTag.word_id == Word.id).where(WordTag.tag == jlpt_tag)
        if excluded:
            statement = statement.where(~Word.id.in_(excluded))
        statement = statement.order_by(func.random()).limit(limit)
        result = await dict_db.exec(statement)
        return result.all()

    words = await query_words(only_jlpt_tag=True)
    if len(words) < limit and jlpt_tag:
        extra_words = await query_words(only_jlpt_tag=False)
        existing_ids = {word.id for word in words}
        for word in extra_words:
            if word.id not in existing_ids:
                words.append(word)
                existing_ids.add(word.id)
            if len(words) >= limit:
                break

    ordered_ids = [word.id for word in words if word.id is not None][:limit]
    return await _fetch_words_by_ids(dict_db, ordered_ids)


async def _ensure_default_plan(user_db: UserDB, current_user: User) -> StudyPlan:
    statement = (
        select(StudyPlan)
        .where(StudyPlan.user_id == current_user.id)
        .order_by(StudyPlan.updated_at.desc())
    )
    result = await user_db.exec(statement)
    plans = result.all()

    if not plans:
        default_plan = StudyPlan(
            user_id=current_user.id,
            name="默认学习计划",
            daily_goal=10,
            review_ratio=0.5,
            dictionary_id="common",
            is_active=True,
        )
        user_db.add(default_plan)
        await user_db.commit()
        await user_db.refresh(default_plan)
        return default_plan

    active_plan = next((plan for plan in plans if plan.is_active), None)
    if active_plan is not None:
        return active_plan

    first_plan = plans[0]
    first_plan.is_active = True
    first_plan.updated_at = datetime.utcnow()
    user_db.add(first_plan)
    await user_db.commit()
    await user_db.refresh(first_plan)
    return first_plan


async def _resolve_user_plan(user_db: UserDB, current_user: User, plan_id: str) -> StudyPlan:
    plan: StudyPlan | None = None
    if plan_id.isdigit():
        statement = select(StudyPlan).where(
            StudyPlan.id == int(plan_id),
            StudyPlan.user_id == current_user.id,
        )
        result = await user_db.exec(statement)
        plan = result.first()
    else:
        # 兼容旧前端缓存（非数字 plan_id）
        plan = await _ensure_default_plan(user_db, current_user)

    if plan is None:
        raise HTTPException(status_code=404, detail="学习计划不存在")
    return plan


@router.get("/", response_model=List[dict])
async def get_study_plans(
    db: UserDB,
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> List[dict]:
    """获取用户学习计划列表"""
    statement = (
        select(StudyPlan)
        .where(StudyPlan.user_id == current_user.id)
        .order_by(StudyPlan.updated_at.desc())
    )
    result = await db.exec(statement)
    plans = result.all()
    if not plans:
        plans = [await _ensure_default_plan(db, current_user)]
    return [_to_study_plan_response(plan) for plan in plans]


@router.get("/current", response_model=dict)
async def get_current_study_plan(
    db: UserDB,
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> dict:
    """获取当前活跃学习计划"""
    plan = await _ensure_default_plan(db, current_user)
    return _to_study_plan_response(plan)


@router.post("/", response_model=dict)
async def create_study_plan(
    db: UserDB,
    current_user: Annotated[User, Depends(get_current_active_user)],
    plan_in: StudyPlanCreate,
) -> dict:
    """创建学习计划"""
    statement = select(StudyPlan).where(StudyPlan.user_id == current_user.id)
    result = await db.exec(statement)
    has_plan = result.first() is not None

    new_plan = StudyPlan(
        user_id=current_user.id,
        name=plan_in.name,
        daily_goal=plan_in.daily_goal,
        review_ratio=plan_in.review_ratio,
        dictionary_id=plan_in.dictionary_id,
        is_active=not has_plan,
    )
    db.add(new_plan)
    await db.commit()
    await db.refresh(new_plan)
    return _to_study_plan_response(new_plan)


@router.put("/{plan_id}", response_model=dict)
async def update_study_plan(
    db: UserDB,
    current_user: Annotated[User, Depends(get_current_active_user)],
    plan_id: str,
    plan_update: StudyPlanUpdate,
) -> dict:
    """更新学习计划"""
    plan = await _resolve_user_plan(db, current_user, plan_id)

    if plan_update.name is not None:
        plan.name = plan_update.name
    if plan_update.daily_goal is not None:
        plan.daily_goal = plan_update.daily_goal
    if plan_update.review_ratio is not None:
        plan.review_ratio = plan_update.review_ratio
    if plan_update.dictionary_id is not None:
        plan.dictionary_id = plan_update.dictionary_id

    if plan_update.is_active is True and not plan.is_active:
        statement = select(StudyPlan).where(
            StudyPlan.user_id == current_user.id,
            StudyPlan.id != plan.id,
            StudyPlan.is_active == True,  # noqa: E712
        )
        result = await db.exec(statement)
        for other_plan in result.all():
            other_plan.is_active = False
            other_plan.updated_at = datetime.utcnow()
            db.add(other_plan)
        plan.is_active = True

    plan.updated_at = datetime.utcnow()
    db.add(plan)
    await db.commit()
    await db.refresh(plan)
    return _to_study_plan_response(plan)


@router.post("/{plan_id}/activate", response_model=dict)
async def activate_study_plan(
    db: UserDB,
    current_user: Annotated[User, Depends(get_current_active_user)],
    plan_id: str,
) -> dict:
    """激活学习计划"""
    plan = await _resolve_user_plan(db, current_user, plan_id)

    statement = select(StudyPlan).where(
        StudyPlan.user_id == current_user.id,
        StudyPlan.id != plan.id,
        StudyPlan.is_active == True,  # noqa: E712
    )
    result = await db.exec(statement)
    for other_plan in result.all():
        other_plan.is_active = False
        other_plan.updated_at = datetime.utcnow()
        db.add(other_plan)

    plan.is_active = True
    plan.updated_at = datetime.utcnow()
    db.add(plan)
    await db.commit()
    await db.refresh(plan)
    return _to_study_plan_response(plan)


@router.get("/{plan_id}/learn-words", response_model=List[WordRead])
async def get_learn_words(
    user_db: UserDB,
    dict_db: DictDB,
    current_user: Annotated[User, Depends(get_current_active_user)],
    plan_id: str,
    date: str | None = Query(None, description="日期 YYYY-MM-DD"),
) -> List[WordRead]:
    """
    获取待背诵单词列表
    - 优先取用户未学习过的单词
    - 按学习计划的 daily_goal 与 dictionary_id 过滤
    """
    _ = date  # 预留，后续可用于按日期做去重分配
    plan = await _resolve_user_plan(user_db, current_user, plan_id)
    target_count = max(1, plan.daily_goal)

    progress_statement = select(WordProgress.word_id).where(WordProgress.user_id == current_user.id)
    progress_result = await user_db.exec(progress_statement)
    learned_word_ids = {row for row in progress_result.all()}

    words = await _pick_random_words(
        dict_db=dict_db,
        limit=target_count,
        dictionary_id=plan.dictionary_id,
        exclude_ids=learned_word_ids,
    )

    if len(words) < target_count:
        fallback_words = await _pick_random_words(
            dict_db=dict_db,
            limit=target_count - len(words),
            dictionary_id=plan.dictionary_id,
            exclude_ids={int(word.id) for word in words},
        )
        words.extend(fallback_words)

    return words[:target_count]


@router.get("/{plan_id}/review-words", response_model=List[WordRead])
async def get_review_words(
    user_db: UserDB,
    dict_db: DictDB,
    current_user: Annotated[User, Depends(get_current_active_user)],
    plan_id: str,
    date: str | None = Query(None, description="日期 YYYY-MM-DD"),
) -> List[WordRead]:
    """
    获取复习单词列表
    - 优先复习 fuzzy/unknown
    - 不足时补充 known
    """
    _ = date
    plan = await _resolve_user_plan(user_db, current_user, plan_id)
    review_count = max(0, int(round(plan.daily_goal * plan.review_ratio)))
    if review_count == 0:
        return []

    priority_statement = (
        select(WordProgress.word_id)
        .where(
            WordProgress.user_id == current_user.id,
            WordProgress.status.in_([ProgressStatus.UNKNOWN, ProgressStatus.FUZZY]),
        )
        .order_by(WordProgress.last_reviewed_at.asc())
        .limit(review_count)
    )
    priority_result = await user_db.exec(priority_statement)
    review_word_ids: list[int] = list(priority_result.all())

    if len(review_word_ids) < review_count:
        supplement_statement = (
            select(WordProgress.word_id)
            .where(
                WordProgress.user_id == current_user.id,
                WordProgress.status == ProgressStatus.KNOWN,
                ~WordProgress.word_id.in_(review_word_ids) if review_word_ids else True,
            )
            .order_by(WordProgress.last_reviewed_at.asc())
            .limit(review_count - len(review_word_ids))
        )
        supplement_result = await user_db.exec(supplement_statement)
        review_word_ids.extend(list(supplement_result.all()))

    words = await _fetch_words_by_ids(dict_db, review_word_ids)
    if len(words) < review_count:
        fallback_words = await _pick_random_words(
            dict_db=dict_db,
            limit=review_count - len(words),
            dictionary_id=plan.dictionary_id,
            exclude_ids={int(word.id) for word in words},
        )
        words.extend(fallback_words)

    return words[:review_count]


@router.post("/{plan_id}/sessions", response_model=dict)
async def save_learning_session(
    db: UserDB,
    current_user: Annotated[User, Depends(get_current_active_user)],
    plan_id: str,
    session_in: LearningSessionCreate,
) -> dict:
    """保存学习轮次，并同步单词学习进度"""
    plan = await _resolve_user_plan(db, current_user, plan_id)
    study_date = _parse_session_date(session_in.date)

    now = datetime.utcnow()
    session = LearningSession(
        plan_id=plan.id or 0,
        date=session_in.date,
        learned_words=json.dumps(session_in.learned_words, ensure_ascii=False),
        reviewed_words=json.dumps(session_in.reviewed_words, ensure_ascii=False),
        known_count=session_in.known_count,
        fuzzy_count=session_in.fuzzy_count,
        unknown_count=session_in.unknown_count,
        completed_at=now,
    )
    db.add(session)

    affected_word_ids = set(_parse_word_ids(session_in.learned_words + session_in.reviewed_words))
    for word_id in affected_word_ids:
        statement = select(WordProgress).where(
            WordProgress.user_id == current_user.id,
            WordProgress.word_id == word_id,
        )
        result = await db.exec(statement)
        progress = result.first()
        if progress is None:
            progress = WordProgress(
                user_id=current_user.id,
                word_id=word_id,
                status=ProgressStatus.UNKNOWN,
                review_count=1,
                correct_count=0,
                last_reviewed_at=now,
            )
        else:
            progress.review_count += 1
            progress.last_reviewed_at = now
        db.add(progress)

    recited_count = (
        max(0, session_in.known_count)
        + max(0, session_in.fuzzy_count)
        + max(0, session_in.unknown_count)
    )
    learned_count = len(session_in.learned_words)
    if current_user.id is not None:
        stats, _ = await study_stats_service.get_or_create(db, current_user.id)
        study_stats_service.apply_learning_activity(
            stats,
            study_date=study_date,
            recited_count=recited_count,
            learned_count=learned_count,
        )
        db.add(stats)

    plan.updated_at = now
    db.add(plan)
    await db.commit()
    await db.refresh(session)
    return _to_session_response(session)


@router.get("/{plan_id}/sessions", response_model=List[dict])
async def get_learning_sessions(
    db: UserDB,
    current_user: Annotated[User, Depends(get_current_active_user)],
    plan_id: str,
) -> List[dict]:
    """获取学习轮次列表"""
    plan = await _resolve_user_plan(db, current_user, plan_id)
    statement = (
        select(LearningSession)
        .where(LearningSession.plan_id == plan.id)
        .order_by(LearningSession.id.desc())
    )
    result = await db.exec(statement)
    sessions = result.all()
    return [_to_session_response(session) for session in sessions]


@router.post("/{plan_id}/add-more", response_model=dict)
async def request_add_more(
    user_db: UserDB,
    dict_db: DictDB,
    current_user: Annotated[User, Depends(get_current_active_user)],
    plan_id: str,
    additional_count: int = Query(5, ge=1, le=20, description="额外学习数量"),
) -> dict:
    """请求加量学习（返回额外单词）"""
    plan = await _resolve_user_plan(user_db, current_user, plan_id)
    words = await _pick_random_words(
        dict_db=dict_db,
        limit=additional_count,
        dictionary_id=plan.dictionary_id,
    )
    return {"success": True, "moreWords": [word.model_dump() for word in words]}
