"""
单词相关 API
"""
from typing import List

from fastapi import APIRouter, HTTPException, Query

from app.core.deps import DictDB
from app.models.word import Word, WordRead
from app.services.word_service import word_service

router = APIRouter()


@router.get("/search", response_model=List[WordRead])
async def search_words(
    db: DictDB,
    q: str = Query(..., description="搜索关键词"),
    limit: int = Query(10, ge=1, le=100, description="返回数量限制")
) -> List[WordRead]:
    """
    搜索单词
    
    - **q**: 搜索关键词（单词、假名或释义）
    - **limit**: 返回结果数量限制
    """
    # TODO: 实现搜索逻辑
    # words = await word_service.search(db, q, limit)
    # return words
    return []


@router.get("/random", response_model=List[WordRead])
async def get_random_words(
    db: DictDB,
    count: int = Query(5, ge=1, le=50, description="随机单词数量")
) -> List[WordRead]:
    """
    获取随机单词（用于背单词）
    
    - **count**: 需要的随机单词数量
    """
    # TODO: 实现随机获取逻辑
    # words = await word_service.get_random(db, count)
    # return words
    return []


@router.get("/{word_id}", response_model=WordRead)
async def get_word(
    db: DictDB,
    word_id: int
) -> WordRead:
    """
    获取单词详情
    
    - **word_id**: 单词 ID
    """
    # TODO: 实现获取逻辑
    # word = await word_service.get(db, word_id)
    # if not word:
    #     raise HTTPException(status_code=404, detail="单词不存在")
    # return word
    raise HTTPException(status_code=404, detail="单词不存在")


@router.get("/", response_model=dict)
async def get_all_words(
    db: DictDB,
    page: int = Query(1, ge=1, description="页码"),
    limit: int = Query(20, ge=1, le=100, description="每页数量")
) -> dict:
    """
    获取所有单词（分页）
    
    - **page**: 页码
    - **limit**: 每页数量
    """
    # TODO: 实现分页获取逻辑
    # words, total = await word_service.get_all(db, page, limit)
    # return {"words": words, "total": total, "page": page, "limit": limit}
    return {"words": [], "total": 0, "page": page, "limit": limit}
