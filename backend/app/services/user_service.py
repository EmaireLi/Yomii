"""
用户服务
"""
from typing import Optional
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import select

from app.models.user import User, UserCreate
from app.models.stats import StudyStats
from app.core.security import get_password_hash, verify_password


class UserService:
    """用户服务"""
    
    async def get_by_email(self, db: AsyncSession, email: str) -> Optional[User]:
        """通过邮箱获取用户"""
        if not email:
            return None
        statement = select(User).where(User.email == email)
        result = await db.exec(statement)
        return result.first()
    
    async def get_by_phone(self, db: AsyncSession, phone: str) -> Optional[User]:
        """通过手机号获取用户"""
        if not phone:
            return None
        statement = select(User).where(User.phone == phone)
        result = await db.exec(statement)
        return result.first()
    
    async def get_by_username(self, db: AsyncSession, username: str) -> Optional[User]:
        """通过用户名获取用户"""
        statement = select(User).where(User.username == username)
        result = await db.exec(statement)
        return result.first()
    
    async def get(self, db: AsyncSession, user_id: int) -> Optional[User]:
        """获取用户详情"""
        statement = select(User).where(User.id == user_id)
        result = await db.exec(statement)
        return result.first()
    
    async def create(self, db: AsyncSession, user_in: UserCreate) -> User:
        """创建用户"""
        user = User(
            email=user_in.email,
            phone=user_in.phone,
            username=user_in.username,
            hashed_password=get_password_hash(user_in.password)
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)
        
        # 创建用户学习统计记录
        study_stats = StudyStats(user_id=user.id)
        db.add(study_stats)
        await db.commit()
        
        return user
    
    async def authenticate(
        self,
        db: AsyncSession,
        identifier: str,
        password: str
    ) -> Optional[User]:
        """验证用户登录 (支持用户名、邮箱或手机号)"""
        user = None
        
        # 先尝试手机号登录
        user = await self.get_by_phone(db, identifier)
        
        # 再尝试邮箱登录
        if not user:
            user = await self.get_by_email(db, identifier)
        
        # 最后尝试用户名登录
        if not user:
            user = await self.get_by_username(db, identifier)
        
        if not user:
            return None
        if not verify_password(password, user.hashed_password):
            return None
        return user
    
    async def update_password(
        self,
        db: AsyncSession,
        user: User,
        new_password: str
    ) -> User:
        """更新用户密码"""
        user.hashed_password = get_password_hash(new_password)
        db.add(user)
        await db.commit()
        await db.refresh(user)
        return user


user_service = UserService()
