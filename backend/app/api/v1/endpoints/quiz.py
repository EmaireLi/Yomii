"""
测试相关 API
"""
from typing import List

from fastapi import APIRouter, Query

from app.core.deps import DictDB, UserDB
from app.models.quiz import QuizQuestion, QuizSubmit

router = APIRouter()


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
    # TODO: 实现获取题目逻辑
    return []


@router.post("/submit", response_model=dict)
async def submit_quiz_answer(
    user_db: UserDB,
    submit: QuizSubmit
) -> dict:
    """
    提交测试答案 (保存到 MySQL 用户数据库)
    
    - **question_id**: 题目 ID
    - **user_answer**: 用户答案
    - **is_correct**: 是否正确
    """
    # TODO: 实现提交答案逻辑
    # 记录用户答题结果，更新学习进度
    return {"success": True, "score": 1 if submit.is_correct else 0}
