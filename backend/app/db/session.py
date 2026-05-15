"""
数据库会话管理

双数据库架构:
- SQLite: 存储词典数据 (words, quiz_questions)
- 用户行为数据库: 开发环境默认 MySQL，发布版可切换为 SQLite
"""
from typing import AsyncGenerator

from sqlmodel import SQLModel
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy import MetaData, Table, func, inspect, select
from sqlalchemy.ext.asyncio import create_async_engine, AsyncEngine
from sqlalchemy.orm import sessionmaker

from app.core.config import settings

# 创建 SQLite 数据目录
settings.SQLITE_DATABASE_FILE.parent.mkdir(parents=True, exist_ok=True)
settings.USER_SQLITE_DATABASE_FILE.parent.mkdir(parents=True, exist_ok=True)

# ==================== SQLite 引擎 (词典数据) ====================
sqlite_engine: AsyncEngine = create_async_engine(
    settings.SQLITE_DATABASE_URL,
    echo=settings.SQL_ECHO,
    future=True,
    connect_args={"check_same_thread": False}  # SQLite 需要此参数
)

sqlite_session_maker = sessionmaker(
    sqlite_engine,
    class_=AsyncSession,
    expire_on_commit=False
)

# ==================== 用户行为数据库引擎 (MySQL / SQLite) ====================
if settings.USER_DATABASE_BACKEND == "sqlite":
    user_engine: AsyncEngine = create_async_engine(
        settings.USER_DATABASE_URL,
        echo=settings.SQL_ECHO,
        future=True,
        connect_args={"check_same_thread": False},
    )
else:
    user_engine = create_async_engine(
        settings.USER_DATABASE_URL,
        echo=settings.SQL_ECHO,
        future=True,
        pool_pre_ping=True,
        pool_size=10,
        max_overflow=20,
    )

user_session_maker = sessionmaker(
    user_engine,
    class_=AsyncSession,
    expire_on_commit=False
)

# 兼容旧代码路径
mysql_session_maker = user_session_maker


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


def _sqlite_compatible_add_column(sync_conn, table_name: str, definition_mysql: str, definition_sqlite: str | None = None) -> None:
    """针对 SQLite / MySQL 生成兼容的 ADD COLUMN 语句。"""
    definition = definition_sqlite if settings.USER_DATABASE_BACKEND == "sqlite" and definition_sqlite else definition_mysql
    sync_conn.exec_driver_sql(f"ALTER TABLE {table_name} ADD COLUMN {definition}")


def _migrate_study_plans_table_columns(sync_conn) -> None:
    """为 study_plans 表补齐新字段。"""
    inspector = inspect(sync_conn)
    if "study_plans" not in inspector.get_table_names():
        return

    column_names = {column["name"] for column in inspector.get_columns("study_plans")}
    if "dictionary_id" not in column_names:
        sync_conn.exec_driver_sql(
            "ALTER TABLE study_plans ADD COLUMN dictionary_id VARCHAR(64) NOT NULL DEFAULT 'common'"
        )


def _migrate_word_progress_table_columns(sync_conn) -> None:
    """为 word_progress 表补齐新版复习调度字段。"""
    inspector = inspect(sync_conn)
    if "word_progress" not in inspector.get_table_names():
        return

    column_names = {column["name"] for column in inspector.get_columns("word_progress")}
    if "interval" not in column_names:
        _sqlite_compatible_add_column(sync_conn, "word_progress", "`interval` FLOAT NOT NULL DEFAULT 0.02")
    if "ease" not in column_names:
        _sqlite_compatible_add_column(sync_conn, "word_progress", "ease FLOAT NOT NULL DEFAULT 2.5")
    if "lapse_count" not in column_names:
        _sqlite_compatible_add_column(sync_conn, "word_progress", "lapse_count INT NOT NULL DEFAULT 0")
    if "last_review" not in column_names:
        _sqlite_compatible_add_column(sync_conn, "word_progress", "last_review DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP")
    if "created_at" not in column_names:
        _sqlite_compatible_add_column(sync_conn, "word_progress", "created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP")
    if "next_review" not in column_names:
        _sqlite_compatible_add_column(sync_conn, "word_progress", "next_review DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP")

    latest_column_names = {column["name"] for column in inspect(sync_conn).get_columns("word_progress")}
    if "last_reviewed_at" in latest_column_names:
        sync_conn.exec_driver_sql(
            "UPDATE word_progress SET last_review = COALESCE(last_reviewed_at, last_review)"
        )
    if settings.USER_DATABASE_BACKEND == "sqlite":
        sync_conn.exec_driver_sql(
            "UPDATE word_progress SET next_review = datetime(last_review, '+' || CASE WHEN \"interval\" > 0.02 THEN \"interval\" ELSE 0.02 END || ' days')"
        )
    else:
        sync_conn.exec_driver_sql(
            "UPDATE word_progress SET next_review = DATE_ADD(last_review, INTERVAL GREATEST(`interval`, 0.02) DAY)"
        )

    index_names = {idx["name"] for idx in inspector.get_indexes("word_progress")}
    if "idx_word_progress_next_review" not in index_names:
        sync_conn.exec_driver_sql(
            "CREATE INDEX idx_word_progress_next_review ON word_progress (next_review)"
        )


def _migrate_quiz_sessions_table_columns(sync_conn) -> None:
    """为 quiz_sessions 表补齐历史报告字段。"""
    inspector = inspect(sync_conn)
    if "quiz_sessions" not in inspector.get_table_names():
        return

    column_names = {column["name"] for column in inspector.get_columns("quiz_sessions")}
    if "consistency_score" not in column_names:
        sync_conn.exec_driver_sql(
            "ALTER TABLE quiz_sessions ADD COLUMN consistency_score FLOAT NOT NULL DEFAULT 0"
        )
    if "speed_score" not in column_names:
        sync_conn.exec_driver_sql(
            "ALTER TABLE quiz_sessions ADD COLUMN speed_score FLOAT NOT NULL DEFAULT 0"
        )
    if "report_recommendations" not in column_names:
        sync_conn.exec_driver_sql(
            "ALTER TABLE quiz_sessions ADD COLUMN report_recommendations TEXT NULL"
        )
    if "difficulty_breakdown" not in column_names:
        sync_conn.exec_driver_sql(
            "ALTER TABLE quiz_sessions ADD COLUMN difficulty_breakdown TEXT NULL"
        )
    sync_conn.exec_driver_sql(
        "UPDATE quiz_sessions SET report_recommendations = COALESCE(report_recommendations, '')"
    )
    sync_conn.exec_driver_sql(
        "UPDATE quiz_sessions SET difficulty_breakdown = COALESCE(difficulty_breakdown, '')"
    )


def _migrate_quiz_results_table_columns(sync_conn) -> None:
    """为 quiz_results 表补齐整场测试保存所需字段。"""
    inspector = inspect(sync_conn)
    if "quiz_results" not in inspector.get_table_names():
        return

    column_names = {column["name"] for column in inspector.get_columns("quiz_results")}
    if "session_id" not in column_names:
        _sqlite_compatible_add_column(
            sync_conn,
            "quiz_results",
            "session_id INT NULL AFTER user_id",
            "session_id INT NULL",
        )
    if "difficulty" not in column_names:
        _sqlite_compatible_add_column(sync_conn, "quiz_results", "difficulty VARCHAR(255) NOT NULL DEFAULT 'medium'")

    index_names = {idx["name"] for idx in inspect(sync_conn).get_indexes("quiz_results")}
    if "idx_quiz_results_session_id" not in index_names:
        sync_conn.exec_driver_sql(
            "CREATE INDEX idx_quiz_results_session_id ON quiz_results (session_id)"
        )
    if "idx_quiz_results_difficulty" not in index_names:
        sync_conn.exec_driver_sql(
            "CREATE INDEX idx_quiz_results_difficulty ON quiz_results (difficulty)"
        )


def _migrate_essays_table_columns(sync_conn) -> None:
    """为 essays 表补齐双模型评测所需字段。"""
    inspector = inspect(sync_conn)
    if "essays" not in inspector.get_table_names():
        return

    column_names = {column["name"] for column in inspector.get_columns("essays")}
    if "target_level" not in column_names:
        _sqlite_compatible_add_column(sync_conn, "essays", "target_level VARCHAR(32) NOT NULL DEFAULT 'N3'")
    if "status" not in column_names:
        _sqlite_compatible_add_column(sync_conn, "essays", "status VARCHAR(32) NOT NULL DEFAULT 'pending'")
    if "evaluation_requested_at" not in column_names:
        _sqlite_compatible_add_column(sync_conn, "essays", "evaluation_requested_at DATETIME NULL")
    if "evaluation_completed_at" not in column_names:
        _sqlite_compatible_add_column(sync_conn, "essays", "evaluation_completed_at DATETIME NULL")
    if "last_error" not in column_names:
        _sqlite_compatible_add_column(sync_conn, "essays", "last_error TEXT NULL")

    sync_conn.exec_driver_sql("UPDATE essays SET status = COALESCE(status, 'pending')")
    sync_conn.exec_driver_sql("UPDATE essays SET target_level = COALESCE(target_level, 'N3')")
    sync_conn.exec_driver_sql("UPDATE essays SET last_error = COALESCE(last_error, '')")


def _migrate_essay_scores_table_columns(sync_conn) -> None:
    """为 essay_scores 表补齐结构化评分字段。"""
    inspector = inspect(sync_conn)
    if "essay_scores" not in inspector.get_table_names():
        return

    column_names = {column["name"] for column in inspector.get_columns("essay_scores")}
    if "task_completion_score" not in column_names:
        _sqlite_compatible_add_column(sync_conn, "essay_scores", "task_completion_score INT NOT NULL DEFAULT 0")
    if "naturalness_score" not in column_names:
        _sqlite_compatible_add_column(sync_conn, "essay_scores", "naturalness_score INT NOT NULL DEFAULT 0")
    if "jlpt_fit_score" not in column_names:
        _sqlite_compatible_add_column(sync_conn, "essay_scores", "jlpt_fit_score INT NOT NULL DEFAULT 0")
    if "level_estimate" not in column_names:
        _sqlite_compatible_add_column(sync_conn, "essay_scores", "level_estimate VARCHAR(32) NOT NULL DEFAULT 'N5'")
    if "summary" not in column_names:
        _sqlite_compatible_add_column(sync_conn, "essay_scores", "summary TEXT NULL")
    if "model_version" not in column_names:
        _sqlite_compatible_add_column(sync_conn, "essay_scores", "model_version VARCHAR(128) NOT NULL DEFAULT ''")

    sync_conn.exec_driver_sql(
        "UPDATE essay_scores SET task_completion_score = CASE WHEN task_completion_score = 0 THEN overall_score ELSE task_completion_score END"
    )
    latest_column_names = {column["name"] for column in inspect(sync_conn).get_columns("essay_scores")}
    naturalness_source = "COALESCE(fluency_score, overall_score)" if "fluency_score" in latest_column_names else "overall_score"
    sync_conn.exec_driver_sql(
        f"UPDATE essay_scores SET naturalness_score = CASE WHEN naturalness_score = 0 THEN {naturalness_source} ELSE naturalness_score END"
    )
    sync_conn.exec_driver_sql(
        "UPDATE essay_scores SET jlpt_fit_score = CASE WHEN jlpt_fit_score = 0 THEN overall_score ELSE jlpt_fit_score END"
    )
    sync_conn.exec_driver_sql(
        "UPDATE essay_scores SET level_estimate = CASE WHEN level_estimate = '' THEN 'N5' ELSE level_estimate END"
    )
    sync_conn.exec_driver_sql(
        "UPDATE essay_scores SET summary = COALESCE(summary, comments, '')"
    )


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


def _migrate_essay_revisions_table_columns(sync_conn) -> None:
    """为 essay_revisions 表补齐修改后重评分字段。"""
    inspector = inspect(sync_conn)
    if "essay_revisions" not in inspector.get_table_names():
        return

    column_names = {column["name"] for column in inspector.get_columns("essay_revisions")}
    if "expanded_revision" not in column_names:
        _sqlite_compatible_add_column(sync_conn, "essay_revisions", "expanded_revision TEXT NULL")
    if "polished_revision" not in column_names:
        _sqlite_compatible_add_column(sync_conn, "essay_revisions", "polished_revision TEXT NULL")
    if "revised_score_json" not in column_names:
        _sqlite_compatible_add_column(sync_conn, "essay_revisions", "revised_score_json TEXT NULL")
    sync_conn.exec_driver_sql(
        "UPDATE essay_revisions SET expanded_revision = COALESCE(expanded_revision, '')"
    )
    sync_conn.exec_driver_sql(
        "UPDATE essay_revisions SET polished_revision = COALESCE(polished_revision, '')"
    )
    sync_conn.exec_driver_sql(
        "UPDATE essay_revisions SET revised_score_json = COALESCE(revised_score_json, '')"
    )


def _migrate_essay_jobs_table_columns(sync_conn) -> None:
    """为 essay_jobs 表补齐评测进度字段。"""
    inspector = inspect(sync_conn)
    if "essay_jobs" not in inspector.get_table_names():
        return

    column_names = {column["name"] for column in inspector.get_columns("essay_jobs")}
    if "progress_percent" not in column_names:
        _sqlite_compatible_add_column(sync_conn, "essay_jobs", "progress_percent INT NOT NULL DEFAULT 0")
    if "progress_message" not in column_names:
        _sqlite_compatible_add_column(sync_conn, "essay_jobs", "progress_message TEXT NULL")

    if settings.USER_DATABASE_BACKEND == "sqlite":
        sync_conn.exec_driver_sql(
            "UPDATE essay_jobs SET progress_percent = CASE "
            "WHEN status = 'completed' THEN 100 "
            "WHEN status = 'failed' THEN 100 "
            "WHEN status = 'revising' THEN MAX(progress_percent, 60) "
            "WHEN status = 'scoring' THEN MAX(progress_percent, 25) "
            "ELSE COALESCE(progress_percent, 0) END"
        )
    else:
        sync_conn.exec_driver_sql(
            "UPDATE essay_jobs SET progress_percent = CASE "
            "WHEN status = 'completed' THEN 100 "
            "WHEN status = 'failed' THEN 100 "
            "WHEN status = 'revising' THEN GREATEST(progress_percent, 60) "
            "WHEN status = 'scoring' THEN GREATEST(progress_percent, 25) "
            "ELSE COALESCE(progress_percent, 0) END"
        )
    sync_conn.exec_driver_sql(
        "UPDATE essay_jobs SET progress_message = COALESCE(progress_message, '')"
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


async def create_user_tables():
    """创建用户行为数据库表 (MySQL / SQLite)"""
    from app.models.user import User
    from app.models.progress import WordProgress
    from app.models.favorite import Favorite, SearchHistory
    from app.models.stats import StudyStats
    from app.models.quiz import QuizResult, QuizSession
    from app.models.essay import Essay, EssayScore, EssayRevision, EssayJob
    from app.models.study_plan import StudyPlan, LearningSession
    mysql_tables = _model_tables(
        User,
        WordProgress,
        Favorite,
        SearchHistory,
        StudyStats,
        QuizSession,
        QuizResult,
        Essay,
        EssayScore,
        EssayRevision,
        EssayJob,
        StudyPlan,
        LearningSession,
    )

    async with user_engine.begin() as conn:
        await conn.run_sync(
            _drop_tables_if_exist,
            {"words", "word_tags", "quiz_questions"},
        )
        await conn.run_sync(_create_selected_tables, mysql_tables)
        await conn.run_sync(_migrate_study_plans_table_columns)
        await conn.run_sync(_migrate_quiz_sessions_table_columns)
        await conn.run_sync(_migrate_quiz_results_table_columns)
        await conn.run_sync(_migrate_word_progress_table_columns)
        await conn.run_sync(_migrate_essays_table_columns)
        await conn.run_sync(_migrate_essay_scores_table_columns)
        await conn.run_sync(_migrate_essay_revisions_table_columns)
        await conn.run_sync(_migrate_essay_jobs_table_columns)


async def ensure_default_release_user() -> None:
    """为发布版 SQLite 用户库创建默认账户。"""
    if settings.USER_DATABASE_BACKEND != "sqlite" or not settings.ENABLE_DEFAULT_AUTO_LOGIN:
        return

    from app.core.security import get_password_hash
    from app.models.stats import StudyStats
    from app.models.user import User

    async with user_session_maker() as session:
        existing_user = await session.scalar(
            select(User).where(User.username == settings.DEFAULT_RELEASE_USERNAME)
        )
        if existing_user is None:
            existing_user = User(
                username=settings.DEFAULT_RELEASE_USERNAME,
                phone=settings.DEFAULT_RELEASE_PHONE,
                hashed_password=get_password_hash(settings.SECRET_KEY),
                is_active=True,
            )
            session.add(existing_user)
            await session.commit()
            await session.refresh(existing_user)

        existing_stats = await session.scalar(
            select(StudyStats).where(StudyStats.user_id == existing_user.id)
        )
        if existing_stats is None:
            session.add(StudyStats(user_id=existing_user.id))
            await session.commit()


async def create_db_and_tables():
    """创建所有数据库表"""
    await create_sqlite_tables()
    await create_user_tables()
    await ensure_default_release_user()


async def get_sqlite_session() -> AsyncGenerator[AsyncSession, None]:
    """获取 SQLite 数据库会话 (词典数据)"""
    async with sqlite_session_maker() as session:
        yield session


async def get_user_session() -> AsyncGenerator[AsyncSession, None]:
    """获取用户行为数据库会话。"""
    async with user_session_maker() as session:
        yield session


async def get_mysql_session() -> AsyncGenerator[AsyncSession, None]:
    """兼容旧接口名称，实际返回当前用户数据库会话。"""
    async for session in get_user_session():
        yield session


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """获取默认用户数据库会话。"""
    async for session in get_user_session():
        yield session
