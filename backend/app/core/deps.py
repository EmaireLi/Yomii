"""
依赖注入
"""
from typing import Generator, Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.config import settings
from app.db.session import get_sqlite_session, get_mysql_session
from app.models.user import User
from app.schemas.token import TokenPayload
from app.services.user_service import user_service

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


async def get_dict_db() -> Generator[AsyncSession, None, None]:
    """获取词典数据库会话 (SQLite)"""
    async for session in get_sqlite_session():
        yield session


async def get_user_db() -> Generator[AsyncSession, None, None]:
    """获取用户数据库会话 (MySQL)"""
    async for session in get_mysql_session():
        yield session


# 类型别名
DictDB = Annotated[AsyncSession, Depends(get_dict_db)]
UserDB = Annotated[AsyncSession, Depends(get_user_db)]


async def get_current_user(
    db: UserDB,
    token: Annotated[str, Depends(oauth2_scheme)]
) -> User:
    """获取当前认证用户"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="无法验证凭据",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
        token_data = TokenPayload(sub=user_id)
    except JWTError:
        raise credentials_exception
    
    # 从数据库获取用户
    user = await user_service.get(db, int(token_data.sub))
    if user is None:
        raise credentials_exception
    return user


async def get_current_active_user(
    current_user: Annotated[User, Depends(get_current_user)]
) -> User:
    """获取当前活跃用户"""
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="用户已被禁用")
    return current_user


# 可选的认证依赖（用于公开接口，但支持已登录用户）
async def get_optional_current_user(
    db: UserDB,
    token: Annotated[str | None, Depends(OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login", auto_error=False))] = None
) -> User | None:
    """获取当前用户（可选，未登录返回 None）"""
    if token is None:
        return None
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            return None
        user = await user_service.get(db, int(user_id))
        return user
    except JWTError:
        return None
