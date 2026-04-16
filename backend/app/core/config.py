"""
应用配置
"""
from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache
from pathlib import Path


class Settings(BaseSettings):
    # 应用基础配置
    APP_NAME: str = "Yomii API"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    
    # 数据库配置 - SQLite (词典数据)
    SQLITE_DATABASE_PATH: str = "data/dictionary.db"
    
    # 数据库配置 - MySQL (用户行为数据)
    MYSQL_HOST: str = "localhost"
    MYSQL_PORT: int = 3306
    MYSQL_USER: str = "root"
    MYSQL_PASSWORD: str = "lhy41712040823"
    MYSQL_DATABASE: str = "yomii"
    
    @property
    def SQLITE_DATABASE_URL(self) -> str:
        """SQLite 连接 URL (词典数据)"""
        return f"sqlite+aiosqlite:///{self.SQLITE_DATABASE_PATH}"
    
    @property
    def MYSQL_DATABASE_URL(self) -> str:
        """MySQL 连接 URL (用户行为数据)"""
        return f"mysql+aiomysql://{self.MYSQL_USER}:{self.MYSQL_PASSWORD}@{self.MYSQL_HOST}:{self.MYSQL_PORT}/{self.MYSQL_DATABASE}"
    
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
    
    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True
    )


@lru_cache()
def get_settings() -> Settings:
    """获取缓存的配置实例"""
    return Settings()


settings = get_settings()
