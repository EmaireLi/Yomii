"""
API v1 路由聚合
"""
from fastapi import APIRouter

from app.api.v1.endpoints import auth, words, quiz, essays, user, study_plans, review

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["认证"])
api_router.include_router(words.router, prefix="/words", tags=["单词"])
api_router.include_router(quiz.router, prefix="/quiz", tags=["测试"])
api_router.include_router(essays.router, prefix="/essays", tags=["作文"])
api_router.include_router(user.router, prefix="/user", tags=["用户"])
api_router.include_router(study_plans.router, prefix="/study-plans", tags=["学习计划"])
api_router.include_router(review.router, prefix="/review", tags=["复习"])
