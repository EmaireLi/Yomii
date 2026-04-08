"""
认证相关 API
"""
from datetime import timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr

from app.core.deps import UserDB, get_current_active_user
from app.core.security import create_access_token
from app.core.config import settings
from app.schemas.token import Token
from app.models.user import UserCreate, User
from app.services.user_service import user_service

router = APIRouter()


class UserResponse(BaseModel):
    """用户信息响应"""
    id: int
    username: str
    email: str
    is_active: bool


class RegisterResponse(BaseModel):
    """注册响应"""
    success: bool
    message: str
    user_id: int


class LoginResponse(BaseModel):
    """登录响应"""
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


@router.post("/login", response_model=LoginResponse)
async def login(
    db: UserDB,
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()]
) -> LoginResponse:
    """
    用户登录
    
    - **username**: 用户名或邮箱
    - **password**: 密码
    """
    user = await user_service.authenticate(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user.is_active:
        raise HTTPException(status_code=400, detail="用户已被禁用")
    
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(subject=user.id, expires_delta=access_token_expires)
    
    return LoginResponse(
        access_token=access_token,
        user=UserResponse(
            id=user.id,
            username=user.username,
            email=user.email,
            is_active=user.is_active
        )
    )


@router.post("/register", response_model=RegisterResponse)
async def register(
    db: UserDB,
    user_in: UserCreate
) -> RegisterResponse:
    """
    用户注册
    
    - **email**: 邮箱
    - **username**: 用户名
    - **password**: 密码
    """
    # 检查邮箱是否已注册
    existing_user = await user_service.get_by_email(db, user_in.email)
    if existing_user:
        raise HTTPException(status_code=400, detail="邮箱已被注册")
    
    # 检查用户名是否已使用
    existing_user = await user_service.get_by_username(db, user_in.username)
    if existing_user:
        raise HTTPException(status_code=400, detail="用户名已被使用")
    
    # 创建用户
    user = await user_service.create(db, user_in)
    
    return RegisterResponse(
        success=True,
        message="注册成功",
        user_id=user.id
    )


@router.post("/logout")
async def logout() -> dict:
    """用户登出"""
    # JWT 无状态，客户端删除 token 即可
    return {"success": True, "message": "登出成功"}


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: Annotated[User, Depends(get_current_active_user)]
) -> UserResponse:
    """获取当前登录用户信息"""
    return UserResponse(
        id=current_user.id,
        username=current_user.username,
        email=current_user.email,
        is_active=current_user.is_active
    )
