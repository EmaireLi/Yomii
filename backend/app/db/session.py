"""
数据库会话管理

双数据库架构:
- SQLite: 存储词典数据 (words, quiz_questions)
- MySQL: 存储用户行为数据 (users, progress, essays, study_plans, etc.)
"""
from typing import AsyncGenerator
from pathlib import Path

from sqlmodel import SQLModel
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy import MetaData, Table, func, inspect, select
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


def _model_tables(*models: type[SQLModel]) -> list[Table]:
    """从模型类提取表对象"""
    return [model.__table__ for model in models]


def _create_selected_tables(sync_conn, tables: list[Table]) -> None:
    """仅创建指定表"""
    SQLModel.metadata.create_all(sync_conn, tables=tables)


def _drop_non_dictionary_tables(sync_conn, allowed_table_names: set[str]) -> None:
    """
    清理 SQLite 中非词典表（仅在空表时删除）。
    若检测到非词典表包含数据，则抛错阻止误删。
    """
    existing_table_names = set(inspect(sync_conn).get_table_names())
    extra_table_names = sorted(
        table_name
        for table_name in existing_table_names
        if table_name not in allowed_table_names and not table_name.startswith("sqlite_")
    )
    if not extra_table_names:
        return

    temp_metadata = MetaData()
    extra_tables = {
        table_name: Table(table_name, temp_metadata, autoload_with=sync_conn)
        for table_name in extra_table_names
    }

    non_empty_tables: list[str] = []
    for table_name, table in extra_tables.items():
        row_count = sync_conn.execute(select(func.count()).select_from(table)).scalar_one()
        if row_count > 0:
            non_empty_tables.append(f"{table_name}({row_count})")

    if non_empty_tables:
        tables_text = ", ".join(non_empty_tables)
        raise RuntimeError(
            f"SQLite 中存在含数据的非词典表，已停止自动清理: {tables_text}"
        )

    for table_name in extra_table_names:
        extra_tables[table_name].drop(sync_conn)


def _drop_tables_if_exist(sync_conn, table_names: set[str]) -> None:
    """删除数据库中指定名称的表（若存在）。"""
    existing_table_names = set(inspect(sync_conn).get_table_names())
    matched_table_names = sorted(existing_table_names.intersection(table_names))
    if not matched_table_names:
        return

    temp_metadata = MetaData()
    for table_name in matched_table_names:
        table = Table(table_name, temp_metadata, autoload_with=sync_conn)
        table.drop(sync_conn)


def _migrate_words_table_meaning_columns(sync_conn) -> None:
    """将 words.meaning 迁移为 japanese_meaning，并补齐 chinese_meaning。"""
    inspector = inspect(sync_conn)
    if "words" not in inspector.get_table_names():
        return

    def get_word_columns() -> set[str]:
        return {column["name"] for column in inspect(sync_conn).get_columns("words")}

    column_names = get_word_columns()
    if "meaning" in column_names and "japanese_meaning" not in column_names:
        sync_conn.exec_driver_sql(
            "ALTER TABLE words RENAME COLUMN meaning TO japanese_meaning"
        )
        column_names = get_word_columns()

    if "chinese_meaning" not in column_names:
        sync_conn.exec_driver_sql(
            "ALTER TABLE words ADD COLUMN chinese_meaning VARCHAR NOT NULL DEFAULT ''"
        )


async def create_sqlite_tables():
    """创建 SQLite 表 (词典数据)"""
    from app.models.word import Word, WordTag
    from app.models.quiz import QuizQuestion
    sqlite_tables = _model_tables(Word, WordTag, QuizQuestion)
    allowed_table_names = {table.name for table in sqlite_tables}

    async with sqlite_engine.begin() as conn:
        await conn.run_sync(_drop_non_dictionary_tables, allowed_table_names)
        await conn.run_sync(_migrate_words_table_meaning_columns)
        await conn.run_sync(_create_selected_tables, sqlite_tables)


async def create_mysql_tables():
    """创建 MySQL 表 (用户行为数据)"""
    from app.models.user import User
    from app.models.progress import WordProgress
    from app.models.favorite import Favorite, SearchHistory
    from app.models.stats import StudyStats
    from app.models.quiz import QuizResult
    from app.models.essay import Essay, EssayScore
    from app.models.study_plan import StudyPlan, LearningSession
    mysql_tables = _model_tables(
        User,
        WordProgress,
        Favorite,
        SearchHistory,
        StudyStats,
        QuizResult,
        Essay,
        EssayScore,
        StudyPlan,
        LearningSession,
    )

    async with mysql_engine.begin() as conn:
        await conn.run_sync(
            _drop_tables_if_exist,
            {"words", "word_tags", "quiz_questions"},
        )
        await conn.run_sync(_create_selected_tables, mysql_tables)


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
