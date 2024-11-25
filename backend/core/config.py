import os
from pydantic import validator
from pydantic_settings import BaseSettings
from typing import List, Optional
import json

class Settings(BaseSettings):
    # Application settings
    PROGRAM_NAME: str = os.getenv("PROGRAM_NAME", "ReeLearn")
    PROGRAM_VERSION: str = os.getenv("PROGRAM_VERSION", "1.0.0")
    TIMEZONE: str = os.getenv("TIMEZONE", "UTC")
    API_V1_STR: str = os.getenv("API_V1_STR", "/api/v1")
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", 8000))
    
    ALLOWED_ORIGINS: List[str] = ["http://localhost", "http://localhost:3000"]

    # Database settings
    POSTGRES_USER: str = os.getenv("POSTGRES_USER", "reelearndb")
    POSTGRES_PASSWORD: str = os.getenv("POSTGRES_PASSWORD", "reelearndb")
    POSTGRES_SERVER: str = os.getenv("POSTGRES_SERVER", "localhost")
    POSTGRES_PORT: str = os.getenv("POSTGRES_PORT", "5433")
    POSTGRES_DB: str = os.getenv("POSTGRES_DB", "reelearndb")
    
    @property
    def DATABASE_URL(self) -> str:
        return f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_SERVER}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"

    @property
    def SYNC_DATABASE_URL(self) -> str:
        return f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_SERVER}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"

    # Video Processing Settings
    VIDEO_MIN_FRAGMENT_DURATION: float = float(os.getenv("VIDEO_MIN_FRAGMENT_DURATION", "2.0"))
    VIDEO_MAX_FRAGMENT_DURATION: float = float(os.getenv("VIDEO_MAX_FRAGMENT_DURATION", "15.0"))
    VIDEO_OPTIMAL_DURATION: float = float(os.getenv("VIDEO_OPTIMAL_DURATION", "5.0"))
    VIDEO_DEFAULT_LANGUAGE: str = os.getenv("VIDEO_DEFAULT_LANGUAGE", "en")
    VIDEO_MAX_SENTENCES_PER_FRAGMENT: int = int(os.getenv("VIDEO_MAX_SENTENCES_PER_FRAGMENT", "3"))

    # Elasticsearch settings
    ELASTICSEARCH_HOST: str = os.getenv("ELASTICSEARCH_HOST", "localhost")
    ELASTICSEARCH_PORT: int = int(os.getenv("ELASTICSEARCH_PORT", 9200))
    ELASTICSEARCH_INDEX_NAME: str = os.getenv("ELASTICSEARCH_INDEX_NAME", "reelearn_index")
    ELASTICSEARCH_BATCH_SIZE: int = int(os.getenv("ELASTICSEARCH_BATCH_SIZE", "100"))
    ELASTICSEARCH_TIMEOUT: int = int(os.getenv("ELASTICSEARCH_TIMEOUT", "30"))

    # S3 (MinIO) settings
    S3_ENDPOINT_URL: str = os.getenv("S3_ENDPOINT_URL", "http://localhost:9000")  # Внутренний URL для сервисов
    S3_PUBLIC_URL: str = os.getenv("S3_PUBLIC_URL", "http://localhost:9000")  # Публичный URL для клиентов
    S3_ACCESS_KEY: str = os.getenv("S3_ACCESS_KEY", "minioadmin")
    S3_SECRET_KEY: str = os.getenv("S3_SECRET_KEY", "minioadmin")
    S3_BUCKET_NAME: str = os.getenv("S3_BUCKET_NAME", "videos")

    # FFmpeg Settings
    FFMPEG_THREADS: int = int(os.getenv("FFMPEG_THREADS", "0"))  # 0 means auto
    FFMPEG_PRESET: str = os.getenv("FFMPEG_PRESET", "medium")
    FFMPEG_CRF: int = int(os.getenv("FFMPEG_CRF", "23"))

    # Celery settings
    CELERY_BROKER_URL: str = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0")
    CELERY_RESULT_BACKEND: str = os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/0")
    
    # Дополнительные настройки
    TEMP_UPLOAD_DIR: str = os.getenv("TEMP_UPLOAD_DIR", "/tmp/videos")

settings = Settings()
