"""
应用配置
"""
from pydantic_settings import BaseSettings
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
    MYSQL_PASSWORD: str = "password"
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
    
    # CORS 配置
    CORS_ORIGINS: list[str] = ["http://localhost:5173", "http://localhost:3000"]
    
    # AI 服务配置
    AI_API_KEY: str = ""
    AI_API_URL: str = ""
    AI_MODEL: str = "gpt-4"
    
    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    """获取缓存的配置实例"""
    return Settings()


settings = get_settings()
