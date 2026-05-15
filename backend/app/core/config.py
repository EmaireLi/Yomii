from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


PROJECT_ROOT = Path(__file__).resolve().parents[3]


def _resolve_project_path(value: str) -> Path:
    """Resolve relative project paths from the repository root."""
    path = Path(value).expanduser()
    if path.is_absolute():
        return path
    return PROJECT_ROOT / path


class Settings(BaseSettings):
    # 应用基础配置
    APP_NAME: str = "Yomii API"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    SQL_ECHO: bool = False
    
    # 数据库配置 - SQLite (词典数据)
    SQLITE_DATABASE_PATH: str = "backend/data/dictionary.db"
    USER_DATABASE_BACKEND: Literal["mysql", "sqlite"] = "mysql"
    USER_SQLITE_DATABASE_PATH: str = "backend/data/user_data.db"
    ENABLE_ESSAY_EVALUATION: bool = True
    ENABLE_DEFAULT_AUTO_LOGIN: bool = False
    DEFAULT_RELEASE_USERNAME: str = "丰川祥子"
    DEFAULT_RELEASE_PHONE: str = "18800000000"
    
    # 数据库配置 - MySQL (用户行为数据，主要用于开发环境)
    MYSQL_HOST: str = "localhost"
    MYSQL_PORT: int = 3306
    MYSQL_USER: str = "root"
    MYSQL_PASSWORD: str = ""
    MYSQL_DATABASE: str = "yomii"

    @property
    def SQLITE_DATABASE_FILE(self) -> Path:
        """SQLite database file resolved from the repository root."""
        return _resolve_project_path(self.SQLITE_DATABASE_PATH)
    
    @property
    def SQLITE_DATABASE_URL(self) -> str:
        """SQLite 连接 URL (词典数据)"""
        return f"sqlite+aiosqlite:///{self.SQLITE_DATABASE_FILE.as_posix()}"

    @property
    def USER_SQLITE_DATABASE_FILE(self) -> Path:
        """用户 SQLite 数据库文件路径。"""
        return _resolve_project_path(self.USER_SQLITE_DATABASE_PATH)

    @property
    def USER_SQLITE_DATABASE_URL(self) -> str:
        """SQLite 连接 URL (用户行为数据)。"""
        return f"sqlite+aiosqlite:///{self.USER_SQLITE_DATABASE_FILE.as_posix()}"
    
    @property
    def MYSQL_DATABASE_URL(self) -> str:
        """MySQL 连接 URL (用户行为数据)"""
        return f"mysql+aiomysql://{self.MYSQL_USER}:{self.MYSQL_PASSWORD}@{self.MYSQL_HOST}:{self.MYSQL_PORT}/{self.MYSQL_DATABASE}"

    @property
    def USER_DATABASE_URL(self) -> str:
        """当前启用的用户行为数据库 URL。"""
        if self.USER_DATABASE_BACKEND == "sqlite":
            return self.USER_SQLITE_DATABASE_URL
        return self.MYSQL_DATABASE_URL
    
    # JWT 认证配置
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24小时
    
    # CORS 配置 (允许前端访问)
    CORS_ORIGINS: list[str] = [
        "http://localhost:5173",  # Vite 默认端口
        "http://localhost:5174",  # Vite 备用端口
        "http://localhost:3000",  # 前端可能使用的端口
        "http://127.0.0.1:5173",
        "http://127.0.0.1:5174",
        "http://127.0.0.1:3000",
    ]
    # 开发环境下允许 localhost / 127.0.0.1 的任意端口
    CORS_ORIGIN_REGEX: str = r"^https?://(localhost|127\.0\.0\.1)(:\d+)?$"
    
    # AI 服务配置
    AI_API_KEY: str = ""
    AI_API_URL: str = ""
    AI_MODEL: str = "gpt-4"
    DEEPSEEK_API_KEY: str = ""
    DEEPSEEK_BASE_URL: str = "https://api.deepseek.com"
    DEEPSEEK_MODEL: str = "deepseek-v4-flash"
    DEEPSEEK_TIMEOUT_SECONDS: float = 60.0
    ESSAY_SCORE_MODEL_URL: str = ""
    ESSAY_SCORE_MODEL_NAME: str = "mock-jlpt-score-v1"
    ESSAY_REVISION_MODEL_URL: str = ""
    ESSAY_REVISION_MODEL_NAME: str = "mock-jlpt-revision-v1"
    ESSAY_MODEL_TIMEOUT_SECONDS: float = 180.0
    
    model_config = SettingsConfigDict(
        env_file=PROJECT_ROOT / ".env",
        case_sensitive=True,
        extra="ignore",
    )


@lru_cache()
def get_settings() -> Settings:
    """获取缓存的配置实例"""
    return Settings()


settings = get_settings()
