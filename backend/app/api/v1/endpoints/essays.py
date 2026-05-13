"""
作文相关 API
"""
from __future__ import annotations

import json
import logging
from datetime import datetime
from typing import Annotated, Any

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query
from fastapi.responses import JSONResponse
from sqlmodel import select

from app.core.deps import UserDB, get_current_active_user
from app.db.session import mysql_session_maker
from app.models.essay import Essay, EssayCreate, EssayJob, EssayRevision, EssayScore
from app.models.user import User
from app.services.ai_evaluation import essay_orchestrator_service

router = APIRouter()

ESSAY_TASK_SESSION_MAKER = mysql_session_maker
ACTIVE_STATUSES = {"pending", "scoring", "revising"}
STATUS_PROGRESS: dict[str, int] = {
    "pending": 0,
    "scoring": 25,
    "revising": 65,
    "completed": 100,
    "failed": 100,
}
STATUS_PROGRESS_MESSAGES: dict[str, str] = {
    "pending": "已提交，等待评测开始",
    "scoring": "正在生成评分报告",
    "revising": "正在生成修改建议",
    "completed": "评测完成",
    "failed": "评测失败",
}


def _terminal_progress_bar(percent: int, width: int = 24) -> str:
    filled = round(width * _clamp_progress(percent) / 100)
    return f"[{'#' * filled}{'.' * (width - filled)}]"


def _json_loads(value: str | None, fallback: Any) -> Any:
    if not value:
        return fallback
    try:
        return json.loads(value)
    except (TypeError, json.JSONDecodeError):
        return fallback


def _json_dumps(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False)


_SCORE_SNAKE_TO_CAMEL: dict[str, str] = {
    "overall_score": "overallScore",
    "task_completion_score": "taskCompletionScore",
    "grammar_score": "grammarScore",
    "vocabulary_score": "vocabularyScore",
    "coherence_score": "coherenceScore",
    "naturalness_score": "naturalnessScore",
    "jlpt_fit_score": "jlptFitScore",
    "level_estimate": "levelEstimate",
    "model_version": "modelVersion",
    "evaluation_time": "evaluationTime",
    "ai_evaluated": "aiEvaluated",
}


def _normalize_score_payload(payload: dict[str, Any] | None) -> dict[str, Any] | None:
    """将评分 payload 的 snake_case 转为 camelCase，与前端类型匹配。"""
    if not payload:
        return payload
    normalized: dict[str, Any] = {}
    for snake_key, value in payload.items():
        camel_key = _SCORE_SNAKE_TO_CAMEL.get(snake_key, snake_key)
        normalized[camel_key] = value
    return normalized


def _ts(value: datetime | None) -> int:
    return int(value.timestamp() * 1000) if value else 0


def _clamp_progress(value: Any) -> int:
    try:
        percent = int(value)
    except (TypeError, ValueError):
        percent = 0
    return max(0, min(100, percent))


def _progress_percent(status: str, job: EssayJob | None = None) -> int:
    fallback = STATUS_PROGRESS.get(status, 0)
    if job is None:
        return fallback
    percent = _clamp_progress(job.progress_percent)
    if status in {"completed", "failed"}:
        return 100
    return max(percent, fallback)


def _progress_message(status: str, job: EssayJob | None = None) -> str:
    if job and job.progress_message:
        return job.progress_message
    return STATUS_PROGRESS_MESSAGES.get(status, "")


def _set_evaluation_progress(
    essay: Essay,
    job: EssayJob,
    *,
    status: str,
    percent: int,
    message: str,
) -> None:
    essay.status = status
    job.status = status
    job.progress_percent = _clamp_progress(percent)
    job.progress_message = message
    essay_id = essay.id or job.essay_id or "unknown"
    print(
        f"essay_eval {essay_id} {_terminal_progress_bar(job.progress_percent)} "
        f"{job.progress_percent:3d}% {message}",
        flush=True,
    )


def _score_payload(score: EssayScore | None) -> dict[str, Any] | None:
    if score is None:
        return None
    return {
        "id": score.id,
        "essayId": score.essay_id,
        "overallScore": score.overall_score,
        "taskCompletionScore": score.task_completion_score,
        "grammarScore": score.grammar_score,
        "vocabularyScore": score.vocabulary_score,
        "coherenceScore": score.coherence_score,
        "naturalnessScore": score.naturalness_score,
        "jlptFitScore": score.jlpt_fit_score,
        "levelEstimate": score.level_estimate,
        "summary": score.summary,
        "comments": score.comments,
        "aiEvaluated": score.ai_evaluated,
        "modelVersion": score.model_version,
        "evaluationTime": _ts(score.evaluation_time),
    }


def _revision_payload(revision: EssayRevision | None) -> dict[str, Any] | None:
    if revision is None:
        return None
    return {
        "id": revision.id,
        "essayId": revision.essay_id,
        "issues": _json_loads(revision.issues_json, []),
        "sentenceSuggestions": _json_loads(revision.sentence_suggestions_json, []),
        "fullRevision": revision.full_revision,
        "expandedRevision": revision.expanded_revision,
        "polishedRevision": revision.polished_revision,
        "revisionNotes": revision.revision_notes,
        "revisedScore": _json_loads(revision.revised_score_json, None),
        "modelVersion": revision.model_version,
        "generatedAt": _ts(revision.generated_at),
    }


def _job_payload(job: EssayJob | None) -> dict[str, Any] | None:
    if job is None:
        return None
    return {
        "id": job.id,
        "essayId": job.essay_id,
        "status": job.status,
        "progressPercent": _progress_percent(job.status, job),
        "progressMessage": _progress_message(job.status, job),
        "errorMessage": job.error_message,
        "scoreModelVersion": job.score_model_version,
        "revisionModelVersion": job.revision_model_version,
        "startedAt": _ts(job.started_at),
        "completedAt": _ts(job.completed_at),
    }


def _essay_payload(
    essay: Essay,
    score: EssayScore | None = None,
    revision: EssayRevision | None = None,
    job: EssayJob | None = None,
) -> dict[str, Any]:
    return {
        "id": essay.id,
        "title": essay.title,
        "content": essay.content,
        "topic": essay.topic,
        "wordCount": essay.word_count,
        "targetLevel": essay.target_level,
        "status": essay.status,
        "progressPercent": _progress_percent(essay.status, job),
        "progressMessage": _progress_message(essay.status, job),
        "submitTime": _ts(essay.submit_time),
        "evaluationRequestedAt": _ts(essay.evaluation_requested_at),
        "evaluationCompletedAt": _ts(essay.evaluation_completed_at),
        "errorMessage": essay.last_error or (job.error_message if job else ""),
        "scoreReport": _score_payload(score),
        "revisionReport": _revision_payload(revision),
        "modelVersions": {
            "score": score.model_version if score else (job.score_model_version if job else ""),
            "revision": revision.model_version if revision else (job.revision_model_version if job else ""),
        },
    }


async def _get_owned_essay(db: UserDB, essay_id: int, current_user: User) -> Essay:
    statement = select(Essay).where(Essay.id == essay_id)
    result = await db.exec(statement)
    essay = result.first()
    if not essay:
        raise HTTPException(status_code=404, detail="作文不存在")
    if essay.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="无权访问此作文")
    return essay


async def _get_latest_score(db: UserDB, essay_id: int) -> EssayScore | None:
    result = await db.exec(
        select(EssayScore).where(EssayScore.essay_id == essay_id).order_by(EssayScore.evaluation_time.desc(), EssayScore.id.desc())
    )
    return result.first()


async def _get_latest_revision(db: UserDB, essay_id: int) -> EssayRevision | None:
    result = await db.exec(
        select(EssayRevision).where(EssayRevision.essay_id == essay_id).order_by(EssayRevision.generated_at.desc(), EssayRevision.id.desc())
    )
    return result.first()


async def _get_latest_job(db: UserDB, essay_id: int) -> EssayJob | None:
    result = await db.exec(
        select(EssayJob).where(EssayJob.essay_id == essay_id).order_by(EssayJob.started_at.desc(), EssayJob.id.desc())
    )
    return result.first()


async def _enqueue_evaluation(background_tasks: BackgroundTasks, db: UserDB, essay: Essay) -> EssayJob:
    now = datetime.utcnow()
    essay.status = "pending"
    essay.evaluation_requested_at = now
    essay.last_error = ""
    job = EssayJob(
        essay_id=essay.id or 0,
        status="pending",
        progress_percent=0,
        progress_message="已提交，等待评测开始",
        error_message="",
    )
    db.add(essay)
    db.add(job)
    await db.commit()
    await db.refresh(essay)
    await db.refresh(job)
    background_tasks.add_task(run_essay_evaluation_task, essay.id, job.id)
    return job


async def run_essay_evaluation_task(essay_id: int | None, job_id: int | None) -> None:
    if essay_id is None or job_id is None:
        return

    async with ESSAY_TASK_SESSION_MAKER() as db:
        essay = await db.get(Essay, essay_id)
        job = await db.get(EssayJob, job_id)
        if essay is None or job is None:
            return

        try:
            now = datetime.utcnow()
            essay.evaluation_requested_at = essay.evaluation_requested_at or now
            essay.last_error = ""
            job.error_message = ""
            job.started_at = now
            _set_evaluation_progress(
                essay,
                job,
                status="scoring",
                percent=20,
                message="正在调用评分模型生成评分报告",
            )
            db.add(essay)
            db.add(job)
            await db.commit()

            score_result = await essay_orchestrator_service.scoring_service.evaluate_essay(
                content=essay.content,
                topic=essay.topic,
                target_level=essay.target_level,
            )

            score = await _get_latest_score(db, essay_id)
            if score is None:
                score = EssayScore(essay_id=essay_id)
            score.overall_score = score_result.payload.get("overall_score", 0)
            score.task_completion_score = score_result.payload.get("task_completion_score", 0)
            score.grammar_score = score_result.payload.get("grammar_score", 0)
            score.vocabulary_score = score_result.payload.get("vocabulary_score", 0)
            score.coherence_score = score_result.payload.get("coherence_score", 0)
            score.naturalness_score = score_result.payload.get("naturalness_score", 0)
            score.jlpt_fit_score = score_result.payload.get("jlpt_fit_score", 0)
            score.level_estimate = score_result.payload.get("level_estimate", essay.target_level)
            score.summary = score_result.payload.get("summary", "")
            score.comments = score_result.payload.get("comments", "")
            score.ai_evaluated = bool(score_result.payload.get("ai_evaluated", False))
            score.model_version = score_result.model_version
            score.evaluation_time = datetime.utcnow()
            db.add(score)

            _set_evaluation_progress(
                essay,
                job,
                status="revising",
                percent=55,
                message="评分完成，正在生成修改建议",
            )
            job.score_model_version = score_result.model_version
            db.add(essay)
            db.add(job)
            await db.commit()

            revision_result = await essay_orchestrator_service.revision_service.revise_essay(
                content=essay.content,
                topic=essay.topic,
                target_level=essay.target_level,
                score_report=score_result.payload,
            )

            _set_evaluation_progress(
                essay,
                job,
                status="revising",
                percent=80,
                message="修改建议已生成，正在复评分并选择最佳结果",
            )
            db.add(essay)
            db.add(job)
            await db.commit()

            selected_revision_payload, revised_score_payload = await essay_orchestrator_service.select_best_revision(
                content=essay.content,
                topic=essay.topic,
                target_level=essay.target_level,
                original_score_report=score_result.payload,
                model_revision_report={
                    **revision_result.payload,
                    "model_version": revision_result.model_version,
                },
            )

            revision = await _get_latest_revision(db, essay_id)
            if revision is None:
                revision = EssayRevision(essay_id=essay_id)
            revision.issues_json = _json_dumps(selected_revision_payload.get("issues", []))
            revision.sentence_suggestions_json = _json_dumps(selected_revision_payload.get("sentence_suggestions", []))
            revision.full_revision = selected_revision_payload.get("full_revision", essay.content)
            revision.expanded_revision = selected_revision_payload.get("expanded_revision", "")
            revision.polished_revision = selected_revision_payload.get("polished_revision", "")
            revision.revision_notes = selected_revision_payload.get("revision_notes", "")
            revision.model_version = selected_revision_payload.get("model_version", revision_result.model_version)
            revision.generated_at = datetime.utcnow()
            revision.revised_score_json = _json_dumps(_normalize_score_payload(revised_score_payload)) if revised_score_payload else ""

            db.add(revision)

            finished_at = datetime.utcnow()
            essay.evaluation_completed_at = finished_at
            essay.last_error = ""
            _set_evaluation_progress(
                essay,
                job,
                status="completed",
                percent=100,
                message="评测完成",
            )
            job.completed_at = finished_at
            job.revision_model_version = revision_result.model_version
            db.add(essay)
            db.add(job)
            await db.commit()
        except Exception as exc:
            failed_at = datetime.utcnow()
            essay.evaluation_completed_at = failed_at
            essay.last_error = str(exc)
            _set_evaluation_progress(
                essay,
                job,
                status="failed",
                percent=100,
                message="评测失败",
            )
            job.error_message = str(exc)
            job.completed_at = failed_at
            db.add(essay)
            db.add(job)
            await db.commit()


@router.post("/submit", response_model=dict)
async def submit_essay(
    background_tasks: BackgroundTasks,
    db: UserDB,
    essay_in: EssayCreate,
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> dict:
    """提交作文并异步触发双模型评测。"""
    if current_user.id is None:
        raise HTTPException(status_code=401, detail="未授权")

    essay = Essay(
        user_id=current_user.id,
        title=essay_in.title,
        content=essay_in.content,
        topic=essay_in.topic,
        word_count=essay_in.word_count,
        target_level=essay_in.target_level,
        status="pending",
    )
    db.add(essay)
    await db.commit()
    await db.refresh(essay)

    job = await _enqueue_evaluation(background_tasks, db, essay)
    return _essay_payload(essay=essay, job=job)


@router.post("/{essay_id}/evaluate", response_model=dict)
async def evaluate_essay(
    essay_id: int,
    background_tasks: BackgroundTasks,
    db: UserDB,
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> dict:
    """手动触发或重试作文评测。"""
    essay = await _get_owned_essay(db, essay_id, current_user)
    latest_job = await _get_latest_job(db, essay_id)
    latest_score = await _get_latest_score(db, essay_id)
    latest_revision = await _get_latest_revision(db, essay_id)

    if essay.status in ACTIVE_STATUSES and latest_job:
        return {
            "success": True,
            "status": essay.status,
            "essay": _essay_payload(essay, latest_score, latest_revision, latest_job),
        }

    job = await _enqueue_evaluation(background_tasks, db, essay)
    return {
        "success": True,
        "status": essay.status,
        "essay": _essay_payload(essay, latest_score, latest_revision, job),
    }


@router.get("/history", response_model=dict)
async def get_essay_history(
    db: UserDB,
    current_user: Annotated[User, Depends(get_current_active_user)],
    skip: int = Query(0, ge=0, description="跳过条数"),
    limit: int = Query(20, ge=1, le=100, description="返回数量限制"),
) -> dict:
    """获取作文历史记录摘要（分页）。"""
    if current_user.id is None:
        return {"items": [], "total": 0}

    # 获取总数
    count_result = await db.exec(
        select(Essay.id).where(Essay.user_id == current_user.id)
    )
    total = len(count_result.all())

    if total == 0:
        return {"items": [], "total": 0}

    result = await db.exec(
        select(Essay)
        .where(Essay.user_id == current_user.id)
        .order_by(Essay.submit_time.desc(), Essay.id.desc())
        .offset(skip)
        .limit(limit)
    )
    essays = result.all()
    essay_ids = [essay.id for essay in essays if essay.id is not None]
    if not essay_ids:
        return {"items": [], "total": total}

    score_result = await db.exec(select(EssayScore).where(EssayScore.essay_id.in_(essay_ids)))
    revision_result = await db.exec(select(EssayRevision).where(EssayRevision.essay_id.in_(essay_ids)))
    job_result = await db.exec(select(EssayJob).where(EssayJob.essay_id.in_(essay_ids)))

    score_map: dict[int, EssayScore] = {}
    for score in score_result.all():
        current = score_map.get(score.essay_id)
        if current is None or (score.evaluation_time, score.id or 0) > (current.evaluation_time, current.id or 0):
            score_map[score.essay_id] = score

    revision_map: dict[int, EssayRevision] = {}
    for revision in revision_result.all():
        current = revision_map.get(revision.essay_id)
        if current is None or (revision.generated_at, revision.id or 0) > (current.generated_at, current.id or 0):
            revision_map[revision.essay_id] = revision

    job_map: dict[int, EssayJob] = {}
    for job in job_result.all():
        current = job_map.get(job.essay_id)
        if current is None or (job.started_at, job.id or 0) > (current.started_at, current.id or 0):
            job_map[job.essay_id] = job

    items = [
        _essay_payload(
            essay=essay,
            score=score_map.get(essay.id or 0),
            revision=revision_map.get(essay.id or 0),
            job=job_map.get(essay.id or 0),
        )
        for essay in essays
    ]
    return {"items": items, "total": total}


@router.get("/{essay_id}/report", response_model=dict)
async def get_essay_report(
    essay_id: int,
    db: UserDB,
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> dict:
    """获取作文完整评测报告。"""
    essay = await _get_owned_essay(db, essay_id, current_user)
    score = await _get_latest_score(db, essay_id)
    revision = await _get_latest_revision(db, essay_id)
    job = await _get_latest_job(db, essay_id)

    return {
        "essay": _essay_payload(essay, score, revision, job),
        "status": essay.status,
        "scoreReport": _score_payload(score),
        "revisionReport": _revision_payload(revision),
        "job": _job_payload(job),
        "modelVersions": {
            "score": score.model_version if score else (job.score_model_version if job else ""),
            "revision": revision.model_version if revision else (job.revision_model_version if job else ""),
        },
        "errorMessage": essay.last_error or (job.error_message if job else ""),
    }


@router.get("/{essay_id}/score", response_model=dict)
async def get_essay_score(
    essay_id: int,
    db: UserDB,
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> dict:
    """兼容旧前端的评分接口。"""
    essay = await _get_owned_essay(db, essay_id, current_user)
    score = await _get_latest_score(db, essay_id)

    if score is None:
        return JSONResponse(
            status_code=202,
            content={
                "status": essay.status,
                "message": "作文评测尚未完成",
            },
        )

    return _score_payload(score) or {}


@router.delete("/{essay_id}", response_model=dict)
async def delete_essay(
    essay_id: int,
    db: UserDB,
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> dict:
    """删除作文及关联的评分、修改、任务记录。"""
    essay = await _get_owned_essay(db, essay_id, current_user)

    # 按外键约束顺序删除：先删子表（立即flush），再删父表
    for model_cls, fk_name in [(EssayJob, "essay_id"), (EssayRevision, "essay_id"), (EssayScore, "essay_id")]:
        children = await db.exec(
            select(model_cls).where(getattr(model_cls, fk_name) == essay_id)
        )
        for child in children.all():
            await db.delete(child)
        await db.flush()

    await db.delete(essay)
    await db.commit()
    return {"success": True, "message": "作文已删除"}
