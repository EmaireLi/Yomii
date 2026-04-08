"""
作文相关 API
"""
from typing import List

from fastapi import APIRouter, HTTPException, Query

from app.core.deps import UserDB
from app.models.essay import Essay, EssayCreate, EssayRead, EssayScoreRead
from app.services.ai_evaluation import ai_evaluation_service

router = APIRouter()


@router.post("/submit", response_model=dict)
async def submit_essay(
    db: UserDB,
    essay_in: EssayCreate
) -> dict:
    """
    提交作文 (保存到 MySQL 用户数据库)
    
    - **title**: 作文标题
    - **content**: 作文内容
    - **topic**: 作文主题
    - **word_count**: 字数
    """
    # TODO: 实现作文提交逻辑
    # essay = Essay(
    #     user_id=current_user.id,
    #     title=essay_in.title,
    #     content=essay_in.content,
    #     topic=essay_in.topic,
    #     word_count=essay_in.word_count
    # )
    # db.add(essay)
    # await db.commit()
    # await db.refresh(essay)
    # return {"id": essay.id, "title": essay.title, ...}
    
    return {
        "id": "essay_mock",
        "title": essay_in.title,
        "content": essay_in.content,
        "topic": essay_in.topic,
        "word_count": essay_in.word_count,
        "submit_time": 0
    }


@router.get("/history", response_model=List[dict])
async def get_essay_history(
    db: UserDB,
    limit: int = Query(20, ge=1, le=100, description="返回数量限制")
) -> List[dict]:
    """
    获取作文历史 (从 MySQL 用户数据库)
    
    - **limit**: 返回数量限制
    """
    # TODO: 实现获取历史逻辑
    return []


@router.get("/{essay_id}/score", response_model=dict)
async def get_essay_score(
    db: UserDB,
    essay_id: str
) -> dict:
    """
    获取作文评分（AI 评测）
    
    - **essay_id**: 作文 ID
    """
    # TODO: 从数据库获取作文内容
    # essay = await get_essay(db, essay_id)
    # if not essay:
    #     raise HTTPException(status_code=404, detail="作文不存在")
    
    # 调用 AI 评测服务
    score = await ai_evaluation_service.evaluate_essay(
        content="模拟作文内容",
        topic="模拟主题"
    )
    
    return {
        "id": f"score_{essay_id}",
        "essay_id": essay_id,
        **score,
        "evaluation_time": 0
    }
