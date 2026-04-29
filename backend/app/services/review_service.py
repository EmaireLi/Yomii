"""
复习调度服务（改进版 SM-2 + 规则增强）
"""
from __future__ import annotations

from datetime import datetime, timedelta
import random
from typing import Iterable, Literal

from app.models.progress import ProgressStatus, WordProgress

ReviewRating = Literal["again", "hard", "good"]

MIN_EASE = 1.3
MAX_INTERVAL_DAYS = 60.0
MIN_LEARNING_INTERVAL_DAYS = 0.02   # ~29 分钟
MAX_LEARNING_INTERVAL_DAYS = 0.1    # ~144 分钟

_LEARNING_INTERVAL_BY_RATING: dict[ReviewRating, float] = {
    "again": 0.02,
    "hard": 0.05,
    "good": 0.1,
}

_RATING_TO_STATUS: dict[ReviewRating, ProgressStatus] = {
    "again": ProgressStatus.UNKNOWN,
    "hard": ProgressStatus.FUZZY,
    "good": ProgressStatus.KNOWN,
}


def status_to_rating(status: ProgressStatus, is_correct: bool) -> ReviewRating:
    if status == ProgressStatus.KNOWN and is_correct:
        return "good"
    if status == ProgressStatus.FUZZY:
        return "hard"
    return "again"


def create_initial_progress(user_id: int, word_id: int, now: datetime | None = None) -> WordProgress:
    current = now or datetime.utcnow()
    interval = MIN_LEARNING_INTERVAL_DAYS
    return WordProgress(
        user_id=user_id,
        word_id=word_id,
        status=ProgressStatus.UNKNOWN,
        interval=interval,
        ease=2.5,
        review_count=0,
        lapse_count=0,
        correct_count=0,
        next_review=current + timedelta(days=interval),
        last_review=current,
        created_at=current,
    )


def apply_review(progress: WordProgress, rating: ReviewRating, now: datetime | None = None) -> WordProgress:
    current = now or datetime.utcnow()
    current_interval = max(float(progress.interval), MIN_LEARNING_INTERVAL_DAYS)
    current_ease = max(float(progress.ease), MIN_EASE)

    if rating == "again":
        next_interval = 1.0
        next_ease = max(MIN_EASE, current_ease - 0.2)
        progress.lapse_count += 1
    elif rating == "hard":
        next_interval = max(1.0, current_interval * 1.2)
        next_ease = max(MIN_EASE, current_ease - 0.15)
    else:
        next_interval = current_interval * current_ease
        next_ease = current_ease + 0.05
        progress.correct_count += 1

    progress.review_count += 1

    # 新词学习阶段：前两次成功前，强制短间隔重复
    if progress.review_count < 2:
        next_interval = _LEARNING_INTERVAL_BY_RATING[rating]

    if progress.lapse_count >= 3:
        next_ease = max(MIN_EASE, next_ease - 0.2)

    bounded_interval = min(MAX_INTERVAL_DAYS, max(MIN_LEARNING_INTERVAL_DAYS, next_interval))

    progress.status = _RATING_TO_STATUS[rating]
    progress.interval = float(round(bounded_interval, 6))
    progress.ease = float(round(next_ease, 6))
    progress.last_review = current
    progress.next_review = current + timedelta(days=progress.interval)
    return progress


def compute_weight(progress: WordProgress) -> float:
    interval = max(float(progress.interval), MIN_LEARNING_INTERVAL_DAYS)
    raw_weight = (1.0 / interval) + float(progress.lapse_count) * 0.5 - float(progress.ease) * 0.1
    return raw_weight


def weighted_sample_progress(
    rows: Iterable[WordProgress],
    limit: int,
    rng: random.Random | None = None,
) -> list[WordProgress]:
    items = list(rows)
    if limit <= 0 or not items:
        return []
    if len(items) <= limit:
        return items

    random_source = rng or random.Random()
    raw_weights = [compute_weight(item) for item in items]
    min_weight = min(raw_weights)
    if min_weight <= 0:
        normalized_weights = [weight - min_weight + 0.01 for weight in raw_weights]
    else:
        normalized_weights = [max(0.01, weight) for weight in raw_weights]

    pool: list[tuple[WordProgress, float]] = list(zip(items, normalized_weights))
    selected: list[WordProgress] = []
    while pool and len(selected) < limit:
        total_weight = sum(weight for _, weight in pool)
        pivot = random_source.uniform(0, total_weight)
        cumulative = 0.0
        for idx, (item, weight) in enumerate(pool):
            cumulative += weight
            if cumulative >= pivot:
                selected.append(item)
                pool.pop(idx)
                break
    return selected


def to_review_progress_payload(progress: WordProgress) -> dict[str, int | float | str]:
    return {
        "wordId": str(progress.word_id),
        "status": progress.status,
        "interval": progress.interval,
        "ease": progress.ease,
        "reviewCount": progress.review_count,
        "lapseCount": progress.lapse_count,
        "correctCount": progress.correct_count,
        "nextReview": int(progress.next_review.timestamp() * 1000),
        "lastReview": int(progress.last_review.timestamp() * 1000),
        "createdAt": int(progress.created_at.timestamp() * 1000),
    }
