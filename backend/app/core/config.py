from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    app_name: str = "Veluna"
    app_env: Literal["development", "staging", "production"] = "development"
    debug: bool = False
    secret_key: str = Field(..., min_length=32)
    api_v1_prefix: str = "/api/v1"

    backend_host: str = "0.0.0.0"
    backend_port: int = 8000
    cors_origins: str = "http://localhost:3000"

    database_url: str
    redis_url: str = "redis://localhost:6379/0"
    redis_cache_db: int = 1
    redis_session_db: int = 2

    jwt_secret_key: str = Field(..., min_length=32)
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 60
    jwt_refresh_token_expire_days: int = 30

    telegram_bot_token: str = ""
    telegram_webapp_url: str = ""

    ai_chat_provider: Literal["openai", "openrouter", "groq"] = "openai"
    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"
    openrouter_api_key: str = ""
    openrouter_model: str = "openai/gpt-4o-mini"
    groq_api_key: str = ""
    groq_model: str = "llama-3.3-70b-versatile"

    image_provider: Literal["fal", "replicate"] = "fal"
    fal_api_key: str = ""
    replicate_api_token: str = ""

    storage_provider: Literal["minio", "s3"] = "minio"
    minio_endpoint: str = "localhost:9000"
    minio_access_key: str = ""
    minio_secret_key: str = ""
    minio_bucket: str = "veluna"
    minio_use_ssl: bool = False
    minio_public_url: str = "http://localhost:9000/veluna"
    aws_access_key_id: str = ""
    aws_secret_access_key: str = ""
    aws_region: str = "us-east-1"
    s3_bucket: str = "veluna"

    celery_broker_url: str = "redis://localhost:6379/3"
    celery_result_backend: str = "redis://localhost:6379/4"

    rate_limit_requests: int = 100
    rate_limit_window_seconds: int = 60

    gem_cost_per_message: int = 1
    gem_cost_per_generation: int = 10
    default_user_gems: int = 50

    admin_telegram_ids: str = ""
    admin_telegram_usernames: str = "Iabobuss"

    @property
    def cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    @property
    def admin_telegram_ids_list(self) -> list[int]:
        if not self.admin_telegram_ids:
            return []
        return [int(x.strip()) for x in self.admin_telegram_ids.split(",") if x.strip()]

    @property
    def admin_telegram_usernames_list(self) -> list[str]:
        if not self.admin_telegram_usernames:
            return []
        return [
            x.strip().lstrip("@").lower()
            for x in self.admin_telegram_usernames.split(",")
            if x.strip()
        ]

    @property
    def is_production(self) -> bool:
        return self.app_env == "production"


@lru_cache
def get_settings() -> Settings:
    return Settings()
