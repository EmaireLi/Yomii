"""
数据库会话管理

双数据库架构:
- SQLite: 存储词典数据 (words, quiz_questions)
- MySQL: 存储用户行为数据 (users, progress, essays, study_plans, etc.)
"""
from typing import AsyncGenerator
from pathlib import Path

from sqlmodel import SQLModel, MetaData
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy.ext.asyncio import create_async_engine, AsyncEngine
from sqlalchemy.orm import sessionmaker

from app.core.config import settings

# 创建 SQLite 数据目录
Path(settings.SQLITE_DATABASE_PATH).parent.mkdir(parents=True, exist_ok=True)

# ==================== SQLite 引擎 (词典数据) ====================
sqlite_engine: AsyncEngine = create_async_engine(
    settings.SQLITE_DATABASE_URL,
    echo=settings.DEBUG,
    future=True,
    connect_args={"check_same_thread": False}  # SQLite 需要此参数
)

sqlite_session_maker = sessionmaker(
    sqlite_engine,
    class_=AsyncSession,
    expire_on_commit=False
)

# ==================== MySQL 引擎 (用户行为数据) ====================
mysql_engine: AsyncEngine = create_async_engine(
    settings.MYSQL_DATABASE_URL,
    echo=settings.DEBUG,
    future=True,
    pool_pre_ping=True,  # 连接健康检查
    pool_size=10,
    max_overflow=20
)

mysql_session_maker = sessionmaker(
    mysql_engine,
    class_=AsyncSession,
    expire_on_commit=False
)


# ==================== 元数据定义 ====================
# 词典数据元数据 (SQLite)
dictionary_metadata = MetaData()

# 用户数据元数据 (MySQL)
user_metadata = MetaData()


async def create_sqlite_tables():
    """创建 SQLite 表 (词典数据)"""
    from app.models.word import Word, WordTag
    from app.models.quiz import QuizQuestion
    
    async with sqlite_engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)


async def create_mysql_tables():
    """创建 MySQL 表 (用户行为数据)"""
    from app.models.user import User
    from app.models.progress import WordProgress
    from app.models.quiz import QuizResult
    from app.models.essay import Essay, EssayScore
    from app.models.study_plan import StudyPlan, LearningSession
    
    async with mysql_engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)


async def create_db_and_tables():
    """创建所有数据库表"""
    await create_sqlite_tables()
    await create_mysql_tables()


async def get_sqlite_session() -> AsyncGenerator[AsyncSession, None]:
    """获取 SQLite 数据库会话 (词典数据)"""
    async with sqlite_session_maker() as session:
        yield session


async def get_mysql_session() -> AsyncGenerator[AsyncSession, None]:
    """获取 MySQL 数据库会话 (用户行为数据)"""
    async with mysql_session_maker() as session:
        yield session


# 兼容性别名
async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """获取默认数据库会话 (MySQL)"""
    async for session in get_mysql_session():
        yield session
