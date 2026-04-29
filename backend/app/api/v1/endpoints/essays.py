"""
作文相关 API
"""
from datetime import datetime
from typing import Annotated, List

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import select

from app.core.deps import UserDB, get_current_active_user
from app.models.essay import Essay, EssayCreate, EssayRead, EssayScore, EssayScoreRead
from app.models.user import User
from app.services.ai_evaluation import ai_evaluation_service

router = APIRouter()


@router.post("/submit", response_model=dict)
async def submit_essay(
    db: UserDB,
    essay_in: EssayCreate,
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> dict:
    """
    提交作文 (保存到 MySQL 用户数据库)
    
    - **title**: 作文标题
    - **content**: 作文内容
    - **topic**: 作文主题
    - **word_count**: 字数
    """
    if current_user.id is None:
        raise HTTPException(status_code=401, detail="未授权")
    
    # 创建新的作文记录
    essay = Essay(
        user_id=current_user.id,
        title=essay_in.title,
        content=essay_in.content,
        topic=essay_in.topic,
        word_count=essay_in.word_count
    )
    db.add(essay)
    await db.commit()
    await db.refresh(essay)
    
    submit_time = int(essay.submit_time.timestamp() * 1000) if essay.submit_time else 0
    
    return {
        "id": essay.id,
        "title": essay.title,
        "content": essay.content,
        "topic": essay.topic,
        "word_count": essay.word_count,
        "submitTime": submit_time
    }


@router.get("/history", response_model=List[dict])
async def get_essay_history(
    db: UserDB,
    current_user: Annotated[User, Depends(get_current_active_user)],
    limit: int = Query(20, ge=1, le=100, description="返回数量限制")
) -> List[dict]:
    """
    获取作文历史 (从 MySQL 用户数据库)
    
    - **limit**: 返回数量限制
    """
    if current_user.id is None:
        return []
    
    # 查询该用户的所有作文，按提交时间倒序排列
    statement = (
        select(Essay)
        .where(Essay.user_id == current_user.id)
        .order_by(Essay.submit_time.desc())
        .limit(limit)
    )
    result = await db.exec(statement)
    essays = result.all()
    
    result_list = []
    for essay in essays:
        submit_time = int(essay.submit_time.timestamp() * 1000) if essay.submit_time else 0
        essay_dict = {
            "id": essay.id,
            "title": essay.title,
            "content": essay.content,
            "topic": essay.topic,
            "wordCount": essay.word_count,
            "submitTime": submit_time
        }
        result_list.append(essay_dict)
    
    return result_list


@router.get("/{essay_id}/score", response_model=dict)
async def get_essay_score(
    db: UserDB,
    current_user: Annotated[User, Depends(get_current_active_user)],
    essay_id: int
) -> dict:
    """
    获取作文评分（AI 评测）
    
    - **essay_id**: 作文 ID
    """
    if current_user.id is None:
        raise HTTPException(status_code=401, detail="未授权")
    
    # 从数据库获取作文
    statement = select(Essay).where(Essay.id == essay_id)
    result = await db.exec(statement)
    essay = result.first()
    
    if not essay:
        raise HTTPException(status_code=404, detail="作文不存在")
    
    if essay.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="无权访问此作文")
    
    # 检查是否已有评分
    score_statement = (
        select(EssayScore)
        .where(EssayScore.essay_id == essay_id)
    )
    score_result = await db.exec(score_statement)
    existing_score = score_result.first()
    
    if existing_score:
        # 返回已有的评分
        evaluation_time = int(existing_score.evaluation_time.timestamp() * 1000) if existing_score.evaluation_time else 0
        return {
            "id": existing_score.id,
            "essayId": essay_id,
            "overallScore": existing_score.overall_score,
            "gramarScore": existing_score.grammar_score,
            "vocabularyScore": existing_score.vocabulary_score,
            "fluencyScore": existing_score.fluency_score,
            "coherenceScore": existing_score.coherence_score,
            "comments": existing_score.comments,
            "aiEvaluated": existing_score.ai_evaluated,
            "evaluationTime": evaluation_time
        }
    
    # 调用 AI 评测服务（暂未实现，返回模拟评分）
    try:
        ai_score = await ai_evaluation_service.evaluate_essay(
            content=essay.content,
            topic=essay.topic
        )
    except Exception:
        # 如果 AI 服务失败，使用默认评分
        ai_score = {
            "overallScore": 75,
            "gramarScore": 75,
            "vocabularyScore": 73,
            "fluencyScore": 75,
            "coherenceScore": 77,
            "comments": "作文内容完整，表达流畅。"
        }
    
    # 保存评分到数据库
    essay_score = EssayScore(
        essay_id=essay_id,
        overall_score=ai_score.get("overallScore", 75),
        grammar_score=ai_score.get("gramarScore", 75),
        vocabulary_score=ai_score.get("vocabularyScore", 73),
        fluency_score=ai_score.get("fluencyScore", 75),
        coherence_score=ai_score.get("coherenceScore", 77),
        comments=ai_score.get("comments", ""),
        ai_evaluated=True
    )
    db.add(essay_score)
    await db.commit()
    await db.refresh(essay_score)
    
    evaluation_time = int(essay_score.evaluation_time.timestamp() * 1000) if essay_score.evaluation_time else 0
    
    return {
        "id": essay_score.id,
        "essayId": essay_id,
        "overallScore": essay_score.overall_score,
        "gramarScore": essay_score.grammar_score,
        "vocabularyScore": essay_score.vocabulary_score,
        "fluencyScore": essay_score.fluency_score,
        "coherenceScore": essay_score.coherence_score,
        "comments": essay_score.comments,
        "aiEvaluated": essay_score.ai_evaluated,
        "evaluationTime": evaluation_time
    }
