"""
用户服务
"""
from typing import Optional
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import select

from app.models.user import User, UserCreate
from app.core.security import get_password_hash, verify_password


class UserService:
    """用户服务"""
    
    async def get_by_email(self, db: AsyncSession, email: str) -> Optional[User]:
        """通过邮箱获取用户"""
        # TODO: 实现获取逻辑
        pass
    
    async def get_by_username(self, db: AsyncSession, username: str) -> Optional[User]:
        """通过用户名获取用户"""
        # TODO: 实现获取逻辑
        pass
    
    async def get(self, db: AsyncSession, user_id: int) -> Optional[User]:
        """获取用户详情"""
        # TODO: 实现获取逻辑
        pass
    
    async def create(self, db: AsyncSession, user_in: UserCreate) -> User:
        """创建用户"""
        # TODO: 实现创建逻辑
        # user = User(
        #     email=user_in.email,
        #     username=user_in.username,
        #     hashed_password=get_password_hash(user_in.password)
        # )
        # db.add(user)
        # await db.commit()
        # await db.refresh(user)
        # return user
        pass
    
    async def authenticate(
        self,
        db: AsyncSession,
        email: str,
        password: str
    ) -> Optional[User]:
        """验证用户登录"""
        # TODO: 实现验证逻辑
        # user = await self.get_by_email(db, email)
        # if not user:
        #     return None
        # if not verify_password(password, user.hashed_password):
        #     return None
        # return user
        pass


user_service = UserService()
