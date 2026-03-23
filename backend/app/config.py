"""
Application Configuration Module

Uses Pydantic Settings to manage environment variables and application configuration.
Supports both development and production environments.
"""

from functools import lru_cache
from typing import List, Optional

from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, field_validator


class Settings(BaseSettings):
    """
    Application settings using Pydantic Settings.

    Environment variables are loaded from .env file if present.
    All sensitive values should be set via environment variables in production.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Application Settings
    app_name: str = Field(default="AI Learning Platform API", alias="APP_NAME")
    app_version: str = Field(default="1.0.0", alias="APP_VERSION")
    debug: bool = Field(default=False, alias="DEBUG")
    environment: str = Field(default="development", alias="ENVIRONMENT")

    # CORS Settings
    allowed_origins: str = Field(
        default="http://localhost:3000,http://frontend:3000",
        alias="ALLOWED_ORIGINS"
    )

    @field_validator("allowed_origins")
    @classmethod
    def parse_allowed_origins(cls, v: str) -> List[str]:
        """Parse comma-separated origins into list."""
        return [origin.strip() for origin in v.split(",") if origin.strip()]

    # Database Settings (MySQL)
    mysql_host: str = Field(default="localhost", alias="MYSQL_HOST")
    mysql_port: int = Field(default=3306, alias="MYSQL_PORT")
    mysql_database: str = Field(default="ai_learning", alias="MYSQL_DATABASE")
    mysql_user: str = Field(default="app_user", alias="MYSQL_USER")
    mysql_PASSWORD: str = Field(default="app_password", alias="MYSQL_PASSWORD")

    # SQLAlchemy Connection Pool Settings
    db_pool_size: int = Field(default=20, alias="DB_POOL_SIZE")
    db_max_overflow: int = Field(default=30, alias="DB_MAX_OVERFLOW")
    db_pool_timeout: int = Field(default=30, alias="DB_POOL_TIMEOUT")
    db_pool_recycle: int = Field(default=3600, alias="DB_POOL_RECYCLE")

    @property
    def database_url(self) -> str:
        """Construct database URL from components."""
        return (
            f"mysql+pymysql://{self.mysql_user}:{self.mysql_PASSWORD}"
            f"@{self.mysql_host}:{self.mysql_port}/{self.mysql_database}"
        )

    @property
    def async_database_url(self) -> str:
        """Construct async database URL from components."""
        return (
            f"mysql+aiomysql://{self.mysql_user}:{self.mysql_PASSWORD}"
            f"@{self.mysql_host}:{self.mysql_port}/{self.mysql_database}"
        )

    # MinIO Settings
    minio_endpoint: str = Field(default="localhost:9000", alias="MINIO_ENDPOINT")
    minio_access_key: str = Field(default="minioadmin", alias="MINIO_ROOT_USER")
    minio_secret_key: str = Field(default="minioadmin", alias="MINIO_ROOT_PASSWORD")
    minio_bucket_name: str = Field(default="materials", alias="MINIO_BUCKET_NAME")
    minio_secure: bool = Field(default=False, alias="MINIO_SECURE")

    # JWT Authentication Settings
    jwt_secret_key: str = Field(
        default="your-secret-key-change-in-production",
        alias="JWT_SECRET_KEY"
    )
    algorithm: str = Field(default="HS256", alias="ALGORITHM")
    access_token_expire_minutes: int = Field(
        default=10080,  # 7 days
        alias="ACCESS_TOKEN_EXPIRE_MINUTES"
    )

    # File Upload Settings
    # Video: max 500MB, PDF: max 50MB
    max_video_size: int = Field(default=524_288_000, alias="MAX_VIDEO_SIZE")  # 500MB
    max_pdf_size: int = Field(default=52_428_800, alias="MAX_PDF_SIZE")  # 50MB

    # Allowed formats per design requirements
    allowed_video_formats: List[str] = Field(
        default=["mp4", "webm"],
        alias="ALLOWED_VIDEO_FORMATS"
    )
    allowed_document_formats: List[str] = Field(
        default=["pdf"],
        alias="ALLOWED_DOCUMENT_FORMATS"
    )

    # Upload chunk size for streaming (8MB)
    upload_chunk_size: int = Field(default=8_388_608, alias="UPLOAD_CHUNK_SIZE")  # 8MB

    # Thumbnail Settings
    thumbnail_width: int = Field(default=320, alias="THUMBNAIL_WIDTH")
    thumbnail_height: int = Field(default=180, alias="THUMBNAIL_HEIGHT")
    thumbnail_format: str = Field(default="jpeg", alias="THUMBNAIL_FORMAT")

    # Pagination Settings
    default_page_size: int = Field(default=20, alias="DEFAULT_PAGE_SIZE")
    max_page_size: int = Field(default=100, alias="MAX_PAGE_SIZE")


@lru_cache()
def get_settings() -> Settings:
    """
    Get cached settings instance.

    Using lru_cache ensures settings are loaded only once per application lifecycle,
    improving performance by avoiding repeated environment variable parsing.
    """
    return Settings()


# Export settings instance for easy import
settings = get_settings()
