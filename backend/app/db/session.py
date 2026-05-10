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
        sync_conn.exec_driver_sql(
            "ALTER TABLE word_progress ADD COLUMN `interval` FLOAT NOT NULL DEFAULT 0.02"
        )
    if "ease" not in column_names:
        sync_conn.exec_driver_sql(
            "ALTER TABLE word_progress ADD COLUMN ease FLOAT NOT NULL DEFAULT 2.5"
        )
    if "lapse_count" not in column_names:
        sync_conn.exec_driver_sql(
            "ALTER TABLE word_progress ADD COLUMN lapse_count INT NOT NULL DEFAULT 0"
        )
    if "last_review" not in column_names:
        sync_conn.exec_driver_sql(
            "ALTER TABLE word_progress ADD COLUMN last_review DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP"
        )
    if "created_at" not in column_names:
        sync_conn.exec_driver_sql(
            "ALTER TABLE word_progress ADD COLUMN created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP"
        )
    if "next_review" not in column_names:
        sync_conn.exec_driver_sql(
            "ALTER TABLE word_progress ADD COLUMN next_review DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP"
        )

    latest_column_names = {column["name"] for column in inspect(sync_conn).get_columns("word_progress")}
    if "last_reviewed_at" in latest_column_names:
        sync_conn.exec_driver_sql(
            "UPDATE word_progress SET last_review = COALESCE(last_reviewed_at, last_review)"
        )
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
        sync_conn.exec_driver_sql(
            "ALTER TABLE quiz_results ADD COLUMN session_id INT NULL AFTER user_id"
        )
    if "difficulty" not in column_names:
        sync_conn.exec_driver_sql(
            "ALTER TABLE quiz_results ADD COLUMN difficulty VARCHAR(255) NOT NULL DEFAULT 'medium'"
        )

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
        sync_conn.exec_driver_sql(
            "ALTER TABLE essays ADD COLUMN target_level VARCHAR(32) NOT NULL DEFAULT 'N3'"
        )
    if "status" not in column_names:
        sync_conn.exec_driver_sql(
            "ALTER TABLE essays ADD COLUMN status VARCHAR(32) NOT NULL DEFAULT 'pending'"
        )
    if "evaluation_requested_at" not in column_names:
        sync_conn.exec_driver_sql(
            "ALTER TABLE essays ADD COLUMN evaluation_requested_at DATETIME NULL"
        )
    if "evaluation_completed_at" not in column_names:
        sync_conn.exec_driver_sql(
            "ALTER TABLE essays ADD COLUMN evaluation_completed_at DATETIME NULL"
        )
    if "last_error" not in column_names:
        sync_conn.exec_driver_sql(
            "ALTER TABLE essays ADD COLUMN last_error TEXT NULL"
        )

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
        sync_conn.exec_driver_sql(
            "ALTER TABLE essay_scores ADD COLUMN task_completion_score INT NOT NULL DEFAULT 0"
        )
    if "naturalness_score" not in column_names:
        sync_conn.exec_driver_sql(
            "ALTER TABLE essay_scores ADD COLUMN naturalness_score INT NOT NULL DEFAULT 0"
        )
    if "jlpt_fit_score" not in column_names:
        sync_conn.exec_driver_sql(
            "ALTER TABLE essay_scores ADD COLUMN jlpt_fit_score INT NOT NULL DEFAULT 0"
        )
    if "level_estimate" not in column_names:
        sync_conn.exec_driver_sql(
            "ALTER TABLE essay_scores ADD COLUMN level_estimate VARCHAR(32) NOT NULL DEFAULT 'N5'"
        )
    if "summary" not in column_names:
        sync_conn.exec_driver_sql(
            "ALTER TABLE essay_scores ADD COLUMN summary TEXT NULL"
        )
    if "model_version" not in column_names:
        sync_conn.exec_driver_sql(
            "ALTER TABLE essay_scores ADD COLUMN model_version VARCHAR(128) NOT NULL DEFAULT ''"
        )

    sync_conn.exec_driver_sql(
        "UPDATE essay_scores SET task_completion_score = CASE WHEN task_completion_score = 0 THEN overall_score ELSE task_completion_score END"
    )
    sync_conn.exec_driver_sql(
        "UPDATE essay_scores SET naturalness_score = CASE WHEN naturalness_score = 0 THEN COALESCE(fluency_score, overall_score) ELSE naturalness_score END"
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
        sync_conn.exec_driver_sql(
            "ALTER TABLE essay_revisions ADD COLUMN expanded_revision TEXT NULL"
        )
    if "polished_revision" not in column_names:
        sync_conn.exec_driver_sql(
            "ALTER TABLE essay_revisions ADD COLUMN polished_revision TEXT NULL"
        )
    if "revised_score_json" not in column_names:
        sync_conn.exec_driver_sql(
            "ALTER TABLE essay_revisions ADD COLUMN revised_score_json TEXT NULL"
        )
    sync_conn.exec_driver_sql(
        "UPDATE essay_revisions SET expanded_revision = COALESCE(expanded_revision, '')"
    )
    sync_conn.exec_driver_sql(
        "UPDATE essay_revisions SET polished_revision = COALESCE(polished_revision, '')"
    )
    sync_conn.exec_driver_sql(
        "UPDATE essay_revisions SET revised_score_json = COALESCE(revised_score_json, '')"
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

    async with mysql_engine.begin() as conn:
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
