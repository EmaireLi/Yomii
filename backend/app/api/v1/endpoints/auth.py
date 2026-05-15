"""
认证相关 API
"""
from datetime import timedelta
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr

from app.core.deps import UserDB, get_current_active_user
from app.core.security import create_access_token
from app.core.config import settings
from app.schemas.token import Token
from app.models.user import UserCreate, User
from app.services.user_service import user_service
from app.db.session import ensure_default_release_user

router = APIRouter()


class UserResponse(BaseModel):
    """用户信息响应"""
    id: int
    username: str
    email: Optional[str] = None
    phone: Optional[str] = None
    is_active: bool


class RegisterRequest(BaseModel):
    """注册请求 (JSON 格式)"""
    username: str
    email: Optional[str] = None
    phone: Optional[str] = None  # 兼容前端 phone 字段
    password: str


class RegisterResponse(BaseModel):
    """注册响应"""
    success: bool
    message: str
    user_id: Optional[int] = None
    error: Optional[str] = None


class LoginRequest(BaseModel):
    """登录请求 (JSON 格式)"""
    username: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None  # 兼容前端 phone 字段
    password: str


class LoginResponse(BaseModel):
    """登录响应 (兼容前端格式)"""
    success: bool
    message: str
    token: Optional[str] = None
    access_token: Optional[str] = None
    token_type: str = "bearer"
    user: Optional[UserResponse] = None
    error: Optional[str] = None


async def _do_login(db, identifier: str, password: str) -> LoginResponse:
    """执行登录逻辑"""
    if not identifier or not password:
        return LoginResponse(
            success=False,
            message="用户名和密码不能为空",
            error="验证失败"
        )
    
    user = await user_service.authenticate(db, identifier, password)
    if not user:
        return LoginResponse(
            success=False,
            message="用户名或密码错误",
            error="认证失败"
        )
    
    if not user.is_active:
        return LoginResponse(
            success=False,
            message="用户已被禁用",
            error="账户已禁用"
        )
    
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(subject=user.id, expires_delta=access_token_expires)
    
    return LoginResponse(
        success=True,
        message="登录成功",
        token=access_token,
        access_token=access_token,
        user=UserResponse(
            id=user.id,
            username=user.username,
            email=user.email,
            phone=user.phone,
            is_active=user.is_active
        )
    )


@router.post("/login", response_model=LoginResponse)
async def login(
    db: UserDB,
    login_data: LoginRequest
) -> LoginResponse:
    """
    用户登录 (JSON 格式)
    
    - **username/email/phone**: 用户名、邮箱或手机号
    - **password**: 密码
    """
    identifier = login_data.username or login_data.email or login_data.phone
    return await _do_login(db, identifier, login_data.password)


@router.post("/token", response_model=LoginResponse)
async def login_for_token(
    db: UserDB,
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()]
) -> LoginResponse:
    """
    用户登录 (OAuth2 表单格式，用于 Swagger UI)
    
    - **username**: 用户名或邮箱
    - **password**: 密码
    """
    return await _do_login(db, form_data.username, form_data.password)


@router.post("/register", response_model=RegisterResponse)
async def register(
    db: UserDB,
    user_in: RegisterRequest
) -> RegisterResponse:
    """
    用户注册
    
    - **username**: 用户名
    - **email/phone**: 邮箱或手机号
    - **password**: 密码
    """
    phone = user_in.phone
    email = user_in.email
    
    # 至少需要一个联系方式
    if not email and not phone:
        return RegisterResponse(
            success=False,
            message="邮箱或手机号不能为空",
            error="验证失败"
        )
    
    # 检查手机号是否已注册
    if phone:
        existing_user = await user_service.get_by_phone(db, phone)
        if existing_user:
            return RegisterResponse(
                success=False,
                message="该手机号已被注册",
                error="手机号已存在"
            )
    
    # 检查邮箱是否已注册
    if email:
        existing_user = await user_service.get_by_email(db, email)
        if existing_user:
            return RegisterResponse(
                success=False,
                message="该邮箱已被注册",
                error="邮箱已存在"
            )
    
    # 检查用户名是否已使用
    existing_user = await user_service.get_by_username(db, user_in.username)
    if existing_user:
        return RegisterResponse(
            success=False,
            message="用户名已被使用",
            error="用户名已存在"
        )
    
    # 创建用户
    try:
        user_create = UserCreate(
            email=email,
            phone=phone,
            username=user_in.username,
            password=user_in.password
        )
        user = await user_service.create(db, user_create)
        
        return RegisterResponse(
            success=True,
            message="注册成功",
            user_id=user.id
        )
    except Exception as e:
        return RegisterResponse(
            success=False,
            message="注册失败",
            error=str(e)
        )


@router.post("/logout")
async def logout() -> dict:
    """用户登出"""
    # JWT 无状态，客户端删除 token 即可
    return {"success": True, "message": "登出成功"}


@router.post("/default-login", response_model=LoginResponse)
async def default_login(
    db: UserDB,
) -> LoginResponse:
    """发布版默认用户自动登录，仅在本地 SQLite 发布模式启用。"""
    if not settings.ENABLE_DEFAULT_AUTO_LOGIN:
        raise HTTPException(status_code=404, detail="default login disabled")

    await ensure_default_release_user()
    return await _do_login(db, settings.DEFAULT_RELEASE_USERNAME, settings.SECRET_KEY)


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: Annotated[User, Depends(get_current_active_user)]
) -> UserResponse:
    """获取当前登录用户信息"""
    return UserResponse(
        id=current_user.id,
        username=current_user.username,
        email=current_user.email,
        phone=current_user.phone,
        is_active=current_user.is_active
    )
