"""
单词相关 API
"""
from typing import Annotated, List

from fastapi import APIRouter, Depends, HTTPException, Query

from app.core.deps import DictDB, UserDB, get_optional_current_user
from app.models.favorite import SearchHistory
from app.models.user import User
from app.models.word import WordRead
from app.services.word_service import word_service

router = APIRouter()


@router.get("/search", response_model=dict)
async def search_words(
    db: DictDB,
    user_db: UserDB,
    current_user: Annotated[User | None, Depends(get_optional_current_user)],
    q: str = Query(..., description="搜索关键词"),
    page: int = Query(1, ge=1, description="页码"),
    limit: int = Query(10, ge=1, le=100, description="返回数量限制")
) -> dict:
    """
    搜索单词
    
    - **q**: 搜索关键词（单词、假名或释义）
    - **page**: 页码
    - **limit**: 每页数量
    """
    words, total = await word_service.search(db, q, page, limit)

    # 登录用户记录搜索历史（用于后续“最近搜索”能力扩展）
    normalized_query = q.strip()
    if current_user is not None and normalized_query and page == 1:
        user_db.add(
            SearchHistory(
                user_id=current_user.id,
                keyword=normalized_query,
                result_count=total,
            )
        )
        await user_db.commit()

    return {"words": words, "total": total, "page": page, "limit": limit}


@router.get("/random", response_model=List[WordRead])
async def get_random_words(
    db: DictDB,
    count: int = Query(5, ge=1, le=50, description="随机单词数量")
) -> List[WordRead]:
    """
    获取随机单词（用于背单词）
    
    - **count**: 需要的随机单词数量
    """
    return await word_service.get_random(db, count)


@router.get("/{word_id}", response_model=WordRead)
async def get_word(
    db: DictDB,
    word_id: int
) -> WordRead:
    """
    获取单词详情
    
    - **word_id**: 单词 ID
    """
    word = await word_service.get(db, word_id)
    if not word:
        raise HTTPException(status_code=404, detail="单词不存在")
    return word


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
    words, total = await word_service.get_all(db, page, limit)
    return {"words": words, "total": total, "page": page, "limit": limit}
