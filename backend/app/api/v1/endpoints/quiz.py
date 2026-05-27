"""
测试相关 API
"""
from __future__ import annotations

import json
import random
import re
from datetime import timedelta
from math import exp, sqrt
from statistics import mean
from typing import Annotated, Any, List

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func
from sqlalchemy.exc import SQLAlchemyError
from sqlmodel import select

from app.core.deps import DictDB, UserDB, get_current_active_user
from app.core.word_levels import (
    get_difficulty_label,
    get_difficulty_target_seconds,
    get_difficulty_weight,
    get_quiz_difficulty_catalog,
    get_tags_by_difficulty,
)
from app.models.quiz import QuizResult, QuizSession, QuizSessionSubmit, QuizSubmit
from app.models.user import User
from app.models.word import Word, WordTag

router = APIRouter()

DIFFICULTY_LEVELS = {item["value"] for item in get_quiz_difficulty_catalog()} | {"easy", "medium", "hard"}
REPORT_RECENT_WINDOW_DAYS = 90
REPORT_WEIGHT_HALF_LIFE_DAYS = 21
REPORT_MIN_RECENT_SESSIONS = 3
LATIN_LETTER_RE = re.compile(r"[A-Za-z]")
JAPANESE_READING_RE = re.compile(r"[\u3040-\u30ff\u3400-\u9fff]")


def _json_dumps(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False)


def _json_loads(value: str | None, fallback: Any) -> Any:
    if not value:
        return fallback
    try:
        return json.loads(value)
    except (TypeError, json.JSONDecodeError):
        return fallback


def _safe_question_id(value: int | str | None) -> int | None:
    if value is None:
        return None
    try:
        question_id = int(value)
    except (TypeError, ValueError):
        return None
    return question_id if question_id > 0 else None


def _session_payload(session: QuizSession) -> dict[str, Any]:
    completed_at = int(session.created_at.timestamp() * 1000)
    return {
        "id": session.id,
        "difficulty": session.difficulty,
        "difficultyLabel": get_difficulty_label(session.difficulty),
        "totalQuestions": session.total_questions,
        "correctAnswers": session.correct_answers,
        "accuracy": round(session.accuracy * 100.0, 1),
        "durationSeconds": session.duration_seconds,
        "abilityScore": session.ability_score,
        "level": session.report_level,
        "summary": session.report_summary,
        "trendDelta": round(session.trend_delta, 1),
        "consistencyScore": session.consistency_score,
        "speedScore": session.speed_score,
        "recommendations": _json_loads(session.report_recommendations, []),
        "difficultyBreakdown": _json_loads(session.difficulty_breakdown, []),
        "completedAt": completed_at,
    }


def _to_word_payload(word: Word) -> dict[str, Any]:
    return {
        "id": str(word.id or 0),
        "word": word.word,
        "kana": word.kana,
        "japaneseMeaning": word.japanese_meaning,
        "chineseMeaning": word.chinese_meaning,
        "example": word.example,
        "partOfSpeech": word.part_of_speech,
        "audioUrl": word.audio_url,
        "tags": [],
    }


def _build_options(correct: str, candidates: list[str], size: int = 4) -> list[str]:
    distractors = [value for value in candidates if value and value != correct]
    random.shuffle(distractors)
    options = [correct, *distractors[: max(0, size - 1)]]
    if len(options) < size:
        filler = ["不知道", "无法判断", "以上都不对", "以上都正确"]
        for value in filler:
            if value not in options:
                options.append(value)
            if len(options) >= size:
                break
    random.shuffle(options)
    return options[:size]


def _is_valid_reading_option(value: str | None) -> bool:
    if not value:
        return False
    return bool(JAPANESE_READING_RE.search(value)) and not LATIN_LETTER_RE.search(value)


def _speed_score(avg_seconds_per_question: float, difficulty: str) -> float:
    if avg_seconds_per_question <= 0:
        return 100.0
    target_seconds = float(get_difficulty_target_seconds(difficulty))
    score = 100.0 * (target_seconds / avg_seconds_per_question)
    return max(35.0, min(100.0, score))


def _ability_level(score: float) -> str:
    if score >= 96:
        return "N1 低频挑战"
    if score >= 91:
        return "N1 中频"
    if score >= 86:
        return "N1 高频"
    if score >= 80:
        return "N2 全量"
    if score >= 73:
        return "N2 高频"
    if score >= 66:
        return "N3 全量"
    if score >= 58:
        return "N3 高频"
    if score >= 48:
        return "N4+N5"
    return "入门阶段"


def _trend_direction(delta: float) -> str:
    if delta >= 3:
        return "up"
    if delta <= -3:
        return "down"
    return "stable"


def _build_summary(score: float, direction: str, level: str) -> str:
    trend_text = {
        "up": "近期表现明显提升",
        "down": "近期表现出现回落",
        "stable": "近期表现整体稳定",
    }[direction]
    return f"当前能力定位接近 {level}，综合能力分 {score:.1f}，{trend_text}。建议持续按周进行测试并针对薄弱项复习。"


def _select_recent_sessions(sessions: list[QuizSession]) -> list[QuizSession]:
    if not sessions:
        return []

    latest_time = max(item.created_at for item in sessions)
    recent_cutoff = latest_time - timedelta(days=REPORT_RECENT_WINDOW_DAYS)
    recent_sessions = [item for item in sessions if item.created_at >= recent_cutoff]
    if len(recent_sessions) >= REPORT_MIN_RECENT_SESSIONS:
        return recent_sessions
    return sessions[-REPORT_MIN_RECENT_SESSIONS:] if len(sessions) > REPORT_MIN_RECENT_SESSIONS else sessions


def _build_report(sessions: list[QuizSession]) -> dict[str, Any]:
    if not sessions:
        return {
            "overallScore": 0.0,
            "level": "暂无评级",
            "trend": {"direction": "stable", "delta": 0.0},
            "consistencyScore": 0.0,
            "speedScore": 0.0,
            "historyCount": 0,
            "basedOnSessions": 0,
            "recommendations": ["完成至少 1 次测试后即可生成能力报告。"],
            "summary": "暂无历史测试记录，无法评估能力趋势。",
            "generatedAt": 0,
            "currentSession": None,
            "difficultyBreakdown": [],
        }

    report_sessions = _select_recent_sessions(sessions)
    accuracy_series = [max(0.0, min(1.0, item.accuracy)) * 100.0 for item in report_sessions]
    mastery_series: list[float] = []
    sec_per_q_series: list[float] = []
    difficulty_score_series: list[float] = []
    latest_time = max(item.created_at for item in report_sessions)
    for item in report_sessions:
        difficulty_weight = get_difficulty_weight(item.difficulty)
        accuracy_pct = max(0.0, min(1.0, item.accuracy)) * 100.0
        mastery_series.append(min(100.0, accuracy_pct * difficulty_weight))
        difficulty_score_series.append(min(100.0, difficulty_weight * 100.0 / 1.3))
        if item.total_questions > 0 and item.duration_seconds > 0:
            sec_per_q_series.append(item.duration_seconds / item.total_questions)

    weighted_sum = 0.0
    weight_total = 0.0
    for item, value in zip(report_sessions, mastery_series):
        # 按真实时间衰减：越久以前的测试越不影响当前综合能力。
        age_days = max(0.0, (latest_time - item.created_at).total_seconds() / 86400.0)
        weight = exp(-age_days / REPORT_WEIGHT_HALF_LIFE_DAYS)
        weighted_sum += value * weight
        weight_total += weight
    weighted_mastery = weighted_sum / weight_total if weight_total else 0.0

    if len(mastery_series) >= 6:
        previous_avg = mean(mastery_series[-6:-3])
        recent_avg = mean(mastery_series[-3:])
    elif len(mastery_series) >= 2:
        previous_avg = mastery_series[0]
        recent_avg = mastery_series[-1]
    else:
        previous_avg = mastery_series[0]
        recent_avg = mastery_series[0]

    trend_delta = recent_avg - previous_avg
    trend_direction = _trend_direction(trend_delta)

    avg_mastery = mean(mastery_series)
    variance = mean([(value - avg_mastery) ** 2 for value in mastery_series])
    consistency_score = max(0.0, min(100.0, 100.0 - sqrt(variance) * 1.9))

    latest_difficulty = report_sessions[-1].difficulty
    speed_score = _speed_score(mean(sec_per_q_series), latest_difficulty) if sec_per_q_series else 72.0
    difficulty_score = mean(difficulty_score_series) if difficulty_score_series else 50.0
    overall_score = round(
        weighted_mastery * 0.55 + difficulty_score * 0.2 + consistency_score * 0.15 + speed_score * 0.1,
        1,
    )
    level = _ability_level(overall_score)

    difficulty_stats: dict[str, list[float]] = {}
    for session in report_sessions:
        difficulty_stats.setdefault(session.difficulty, []).append(session.accuracy * 100.0)

    difficulty_breakdown = [
        {
            "difficulty": key,
            "label": get_difficulty_label(key),
            "accuracy": round(mean(values), 1),
            "count": len(values),
        }
        for key, values in difficulty_stats.items()
    ]
    difficulty_breakdown.sort(key=lambda item: item["accuracy"])

    recommendations: list[str] = []
    if len(report_sessions) < len(sessions):
        recommendations.append(
            f"综合能力已按最近 {REPORT_RECENT_WINDOW_DAYS} 天内的测试优先计算，较早历史记录仅保留展示。"
        )
    if trend_direction == "down":
        recommendations.append("近期准确率回落，建议先复习错题词汇，再进行同难度复测。")
    elif trend_direction == "up":
        recommendations.append("能力在提升，下一次测试可尝试更高难度以扩大能力边界。")
    else:
        recommendations.append("能力表现稳定，建议固定每周 2-3 次测试保持节奏。")

    if difficulty_breakdown:
        weakest = difficulty_breakdown[0]
        recommendations.append(
            f"当前薄弱层级为 {weakest['label']}（平均正确率 {weakest['accuracy']}%），可优先加强该层级训练。"
        )
    strongest_difficulty = max(report_sessions, key=lambda item: get_difficulty_weight(item.difficulty))
    if strongest_difficulty.accuracy >= 0.78:
        recommendations.append(
            f"最近已能稳定应对 {get_difficulty_label(strongest_difficulty.difficulty)}，可以逐步向更高层级测试。"
        )

    latest = sessions[-1]
    generated_at = int(latest.created_at.timestamp() * 1000)

    return {
        "overallScore": overall_score,
        "level": level,
        "trend": {"direction": trend_direction, "delta": round(trend_delta, 1)},
        "consistencyScore": round(consistency_score, 1),
        "speedScore": round(speed_score, 1),
        "historyCount": len(sessions),
        "basedOnSessions": len(report_sessions),
        "recommendations": recommendations,
        "summary": _build_summary(overall_score, trend_direction, level),
        "generatedAt": generated_at,
        "currentSession": {
            "sessionId": latest.id,
            "accuracy": round(latest.accuracy * 100.0, 1),
            "difficulty": latest.difficulty,
            "difficultyLabel": get_difficulty_label(latest.difficulty),
            "totalQuestions": latest.total_questions,
            "correctAnswers": latest.correct_answers,
            "durationSeconds": latest.duration_seconds,
            "completedAt": generated_at,
            "abilityScore": latest.ability_score,
            "level": latest.report_level,
            "trendDelta": round(latest.trend_delta, 1),
            "summary": latest.report_summary,
        },
        "difficultyBreakdown": difficulty_breakdown,
    }


@router.get("/difficulties", response_model=List[dict])
async def get_quiz_difficulties() -> List[dict]:
    """获取测试难度分层配置"""
    return [
        {
            "value": item["value"],
            "label": item["label"],
            "tags": item["tags"],
        }
        for item in get_quiz_difficulty_catalog()
    ]


@router.get("/questions", response_model=List[dict])
async def get_quiz_questions(
    dict_db: DictDB,
    difficulty: str = Query("medium", description="难度级别"),
    count: int = Query(10, ge=1, le=50, description="题目数量")
) -> List[dict]:
    """
    获取测试题目 (从 SQLite 词典数据库)

    - **difficulty**: 难度级别 (easy/medium/hard)
    - **count**: 题目数量
    """
    normalized_difficulty = difficulty.lower()
    if normalized_difficulty not in DIFFICULTY_LEVELS:
        raise HTTPException(status_code=400, detail="不支持的难度级别")

    level_tags = list(get_tags_by_difficulty(normalized_difficulty))

    statement = select(Word)
    if level_tags:
        statement = (
            statement.join(WordTag, WordTag.word_id == Word.id)
            .where(WordTag.tag.in_(level_tags))
            .distinct()
        )
    statement = statement.order_by(func.random()).limit(max(40, count * 4))
    result = await dict_db.exec(statement)
    raw_words = result.all()

    # 仅在难度未映射出标签时回退到全词库；有标签时保持同标签出题。
    if not raw_words and not level_tags:
        fallback_statement = select(Word).order_by(func.random()).limit(max(40, count * 4))
        fallback_result = await dict_db.exec(fallback_statement)
        raw_words = fallback_result.all()

    if not raw_words:
        return []

    random.shuffle(raw_words)
    selected_words = raw_words[: min(count, len(raw_words))]
    all_kana = [item.kana for item in raw_words if _is_valid_reading_option(item.kana)]
    all_cn_meaning = [item.chinese_meaning for item in raw_words if item.chinese_meaning]

    questions: list[dict[str, Any]] = []
    for word in selected_words:
        if word.id is None:
            continue

        available_modes = ["chinese"]
        if _is_valid_reading_option(word.kana):
            available_modes.append("kana")
        question_mode = random.choice(available_modes)
        if question_mode == "kana":
            question_text = f"以下哪个选项是「{word.word}」的正确读音？"
            correct_answer = word.kana
            options = _build_options(correct_answer, all_kana)
            explanation = f"「{word.word}」的读音是「{word.kana}」。"
        else:
            question_text = f"「{word.word}」的中文含义是？"
            correct_answer = word.chinese_meaning or word.japanese_meaning
            options = _build_options(correct_answer, all_cn_meaning)
            explanation = f"「{word.word}」常见中文含义是「{correct_answer}」。"

        questions.append(
            {
                "id": str(word.id),
                "type": "multiple-choice",
                "questionMode": question_mode,
                "question": question_text,
                "word": _to_word_payload(word),
                "options": options,
                "correctAnswer": correct_answer,
                "explanation": explanation,
            }
        )

    return questions


@router.post("/submit", response_model=dict)
async def submit_quiz_answer(
    user_db: UserDB,
    submit: QuizSubmit,
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> dict:
    """
    提交单题答案 (保存到 MySQL 用户数据库)

    - **question_id**: 题目 ID
    - **user_answer**: 用户答案
    - **is_correct**: 是否正确
    """
    if current_user.id is None:
        raise HTTPException(status_code=401, detail="未授权")

    user_db.add(
        QuizResult(
            user_id=current_user.id,
            question_id=submit.question_id,
            user_answer=submit.user_answer,
            is_correct=submit.is_correct,
            difficulty="medium",
        )
    )
    await user_db.commit()

    return {"success": True, "score": 1 if submit.is_correct else 0}


@router.post("/session", response_model=dict)
async def submit_quiz_session(
    user_db: UserDB,
    session_submit: QuizSessionSubmit,
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> dict:
    """提交整场测试结果并生成基于历史记录的能力报告"""
    if current_user.id is None:
        raise HTTPException(status_code=401, detail="未授权")

    normalized_difficulty = session_submit.difficulty.lower()
    if normalized_difficulty not in DIFFICULTY_LEVELS:
        normalized_difficulty = "medium"

    safe_total = max(1, session_submit.total_questions)
    safe_correct = max(0, min(session_submit.correct_answers, safe_total))
    accuracy = safe_correct / safe_total

    session = QuizSession(
        user_id=current_user.id,
        difficulty=normalized_difficulty,
        total_questions=safe_total,
        correct_answers=safe_correct,
        accuracy=accuracy,
        duration_seconds=session_submit.duration_seconds,
    )
    user_db.add(session)
    await user_db.flush()

    history_statement = (
        select(QuizSession)
        .where(QuizSession.user_id == current_user.id)
        .order_by(QuizSession.created_at.desc())
        .limit(20)
    )
    history_result = await user_db.exec(history_statement)
    recent_sessions_desc = history_result.all()
    recent_sessions = list(reversed(recent_sessions_desc))
    report = _build_report(recent_sessions)

    session.ability_score = report["overallScore"]
    session.report_level = report["level"]
    session.report_summary = report["summary"]
    session.trend_delta = report["trend"]["delta"]
    session.consistency_score = report["consistencyScore"]
    session.speed_score = report["speedScore"]
    session.report_recommendations = _json_dumps(report["recommendations"])
    session.difficulty_breakdown = _json_dumps(report["difficultyBreakdown"])

    await user_db.commit()
    await user_db.refresh(session)

    answers_saved = True
    if session_submit.answers:
        try:
            for answer in session_submit.answers:
                question_id = _safe_question_id(answer.question_id)
                if question_id is None:
                    answers_saved = False
                    continue
                user_db.add(
                    QuizResult(
                        session_id=session.id,
                        user_id=current_user.id,
                        question_id=question_id,
                        user_answer=answer.user_answer,
                        is_correct=answer.is_correct,
                        difficulty=normalized_difficulty,
                    )
                )
            await user_db.commit()
        except SQLAlchemyError:
            answers_saved = False
            await user_db.rollback()

    session_payload = _session_payload(session)
    report["currentSession"] = session_payload
    return {
        "success": True,
        "answersSaved": answers_saved,
        "session": session_payload,
        "report": report,
    }


@router.get("/history", response_model=dict)
async def get_quiz_history(
    user_db: UserDB,
    current_user: Annotated[User, Depends(get_current_active_user)],
    skip: int = Query(0, ge=0, description="跳过条数"),
    limit: int = Query(10, ge=1, le=100, description="返回数量限制"),
) -> dict:
    """获取测试历史记录（分页）。"""
    if current_user.id is None:
        return {"items": [], "total": 0}

    # 总数
    count_result = await user_db.exec(
        select(QuizSession.id).where(QuizSession.user_id == current_user.id)
    )
    total = len(count_result.all())

    if total == 0:
        return {"items": [], "total": 0}

    statement = (
        select(QuizSession)
        .where(QuizSession.user_id == current_user.id)
        .order_by(QuizSession.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    result = await user_db.exec(statement)
    sessions = result.all()

    return {
        "items": [_session_payload(item) for item in sessions],
        "total": total,
    }


@router.get("/report", response_model=dict)
async def get_quiz_report(
    user_db: UserDB,
    current_user: Annotated[User, Depends(get_current_active_user)],
    limit: int = Query(20, ge=1, le=100),
) -> dict:
    """基于历史测试记录生成能力报告"""
    if current_user.id is None:
        return _build_report([])

    statement = (
        select(QuizSession)
        .where(QuizSession.user_id == current_user.id)
        .order_by(QuizSession.created_at.desc())
        .limit(limit)
    )
    result = await user_db.exec(statement)
    sessions = list(reversed(result.all()))
    return _build_report(sessions)


@router.delete("/sessions/{session_id}", response_model=dict)
async def delete_quiz_session(
    session_id: int,
    user_db: UserDB,
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> dict:
    """删除单条测试记录及关联的答题结果。"""
    session = await user_db.get(QuizSession, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="测试记录不存在")
    if session.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="无权删除此记录")

    # 删除关联的答题结果（先flush确保SQL执行顺序）
    result_stmt = select(QuizResult).where(QuizResult.session_id == session_id)
    results = await user_db.exec(result_stmt)
    for r in results.all():
        await user_db.delete(r)
    await user_db.flush()

    await user_db.delete(session)
    await user_db.commit()
    return {"success": True, "message": "测试记录已删除"}
