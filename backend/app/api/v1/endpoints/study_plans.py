"""
学习计划相关 API
"""
from typing import List

from fastapi import APIRouter, Query

from app.core.deps import UserDB, DictDB
from app.models.study_plan import (
    StudyPlan, StudyPlanCreate, StudyPlanUpdate,
    LearningSession, LearningSessionCreate
)

router = APIRouter()


@router.get("/", response_model=List[dict])
async def get_study_plans(
    db: UserDB
) -> List[dict]:
    """获取所有学习计划 (从 MySQL 用户数据库)"""
    # TODO: 实现获取学习计划逻辑
    return []


@router.get("/current", response_model=dict)
async def get_current_study_plan(
    db: UserDB
) -> dict:
    """获取当前活跃的学习计划 (从 MySQL 用户数据库)"""
    # TODO: 实现获取当前计划逻辑
    return {
        "id": "default",
        "name": "默认计划",
        "dailyGoal": 10,
        "reviewRatio": 0.5,
        "isActive": True,
        "createdAt": 0,
        "updatedAt": 0
    }


@router.post("/", response_model=dict)
async def create_study_plan(
    db: UserDB,
    plan_in: StudyPlanCreate
) -> dict:
    """创建新的学习计划 (保存到 MySQL 用户数据库)"""
    # TODO: 实现创建计划逻辑
    return {
        "id": "new_plan",
        "name": plan_in.name,
        "dailyGoal": plan_in.daily_goal,
        "reviewRatio": plan_in.review_ratio,
        "isActive": False,
        "createdAt": 0,
        "updatedAt": 0
    }


@router.put("/{plan_id}", response_model=dict)
async def update_study_plan(
    db: UserDB,
    plan_id: str,
    plan_update: StudyPlanUpdate
) -> dict:
    """更新学习计划 (保存到 MySQL 用户数据库)"""
    # TODO: 实现更新计划逻辑
    return {"id": plan_id, "updated": True}


@router.post("/{plan_id}/activate", response_model=dict)
async def activate_study_plan(
    db: UserDB,
    plan_id: str
) -> dict:
    """激活学习计划 (更新 MySQL 用户数据库)"""
    # TODO: 实现激活计划逻辑
    return {"id": plan_id, "isActive": True}


@router.get("/{plan_id}/learn-words", response_model=List[dict])
async def get_learn_words(
    user_db: UserDB,
    dict_db: DictDB,
    plan_id: str,
    date: str = Query(None, description="日期 YYYY-MM-DD")
) -> List[dict]:
    """
    获取待背诵的单词列表
    - 从 MySQL 获取学习计划和进度
    - 从 SQLite 获取单词详情
    """
    # TODO: 实现获取待学习单词逻辑
    return []


@router.get("/{plan_id}/review-words", response_model=List[dict])
async def get_review_words(
    user_db: UserDB,
    dict_db: DictDB,
    plan_id: str,
    date: str = Query(None, description="日期 YYYY-MM-DD")
) -> List[dict]:
    """
    获取复习单词列表
    - 从 MySQL 获取学习计划和进度
    - 从 SQLite 获取单词详情
    """
    # TODO: 实现获取复习单词逻辑
    return []


@router.post("/{plan_id}/sessions", response_model=dict)
async def save_learning_session(
    db: UserDB,
    plan_id: str,
    session_in: LearningSessionCreate
) -> dict:
    """保存学习轮次 (保存到 MySQL 用户数据库)"""
    # TODO: 实现保存学习轮次逻辑
    return {"id": "session_new", **session_in.model_dump()}


@router.get("/{plan_id}/sessions", response_model=List[dict])
async def get_learning_sessions(
    db: UserDB,
    plan_id: str
) -> List[dict]:
    """获取学习轮次列表 (从 MySQL 用户数据库)"""
    # TODO: 实现获取学习轮次逻辑
    return []


@router.post("/{plan_id}/add-more", response_model=dict)
async def request_add_more(
    user_db: UserDB,
    dict_db: DictDB,
    plan_id: str,
    additional_count: int = Query(5, ge=1, le=20, description="额外学习数量")
) -> dict:
    """
    请求加量学习
    - 从 SQLite 获取额外单词
    - 更新 MySQL 学习进度
    """
    # TODO: 实现加量学习逻辑
    return {"success": True, "moreWords": []}
