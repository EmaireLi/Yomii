"""
认证相关 API
"""
from datetime import timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm

from app.core.deps import UserDB
from app.core.security import create_access_token
from app.core.config import settings
from app.schemas.token import Token
from app.models.user import UserCreate, User
from app.services.user_service import user_service

router = APIRouter()


@router.post("/login", response_model=Token)
async def login(
    db: UserDB,
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()]
) -> Token:
    """
    用户登录
    
    - **username**: 用户名或邮箱
    - **password**: 密码
    """
    # TODO: 实现登录逻辑
    # user = await user_service.authenticate(db, form_data.username, form_data.password)
    # if not user:
    #     raise HTTPException(
    #         status_code=status.HTTP_401_UNAUTHORIZED,
    #         detail="用户名或密码错误",
    #         headers={"WWW-Authenticate": "Bearer"},
    #     )
    # if not user.is_active:
    #     raise HTTPException(status_code=400, detail="用户已被禁用")
    # 
    # access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    # access_token = create_access_token(subject=user.id, expires_delta=access_token_expires)
    # return Token(access_token=access_token)
    
    raise HTTPException(status_code=501, detail="登录功能待实现")


@router.post("/register", response_model=dict)
async def register(
    db: UserDB,
    user_in: UserCreate
) -> dict:
    """
    用户注册
    
    - **email**: 邮箱
    - **username**: 用户名
    - **password**: 密码
    """
    # TODO: 实现注册逻辑
    # existing_user = await user_service.get_by_email(db, user_in.email)
    # if existing_user:
    #     raise HTTPException(status_code=400, detail="邮箱已被注册")
    # 
    # existing_user = await user_service.get_by_username(db, user_in.username)
    # if existing_user:
    #     raise HTTPException(status_code=400, detail="用户名已被使用")
    # 
    # user = await user_service.create(db, user_in)
    # return {"success": True, "message": "注册成功", "user_id": user.id}
    
    raise HTTPException(status_code=501, detail="注册功能待实现")


@router.post("/logout")
async def logout() -> dict:
    """用户登出"""
    # JWT 无状态，客户端删除 token 即可
    return {"success": True, "message": "登出成功"}
