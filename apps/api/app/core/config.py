from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


API_ROOT = Path(__file__).resolve().parents[2]
REPOSITORY_ROOT = Path(__file__).resolve().parents[4]


class Settings(BaseSettings):
    app_env: str = Field(default="development", alias="APP_ENV")
    log_level: str = Field(default="info", alias="LOG_LEVEL")

    database_url: str = Field(
        default="postgresql+psycopg://postgres:postgres@localhost:5432/ai_analytics",
        alias="DATABASE_URL",
    )
    redis_url: str = Field(default="redis://localhost:6379/0", alias="REDIS_URL")

    supabase_url: str | None = Field(default=None, alias="SUPABASE_URL")
    supabase_publishable_key: str | None = Field(default=None, alias="SUPABASE_PUBLISHABLE_KEY")
    supabase_anon_key: str | None = Field(default=None, alias="SUPABASE_ANON_KEY")
    supabase_secret_key: str | None = Field(default=None, alias="SUPABASE_SECRET_KEY")
    supabase_service_role_key: str | None = Field(
        default=None,
        alias="SUPABASE_SERVICE_ROLE_KEY",
    )
    supabase_jwt_secret: str | None = Field(default=None, alias="SUPABASE_JWT_SECRET")
    supabase_jwt_audience: str = Field(default="authenticated", alias="SUPABASE_JWT_AUDIENCE")
    supabase_storage_bucket: str = Field(default="datasets", alias="SUPABASE_STORAGE_BUCKET")
    max_upload_size_bytes: int = Field(default=26_214_400, alias="MAX_UPLOAD_SIZE_BYTES")

    ai_provider: str = Field(default="mimo", alias="AI_PROVIDER")
    mimo_base_url: str = Field(default="https://api.xiaomimimo.com/v1", alias="MIMO_BASE_URL")
    mimo_api_key: str | None = Field(default=None, alias="MIMO_API_KEY")
    mimo_model: str = Field(default="mimo-v2-flash", alias="MIMO_MODEL")

    openai_api_key: str | None = Field(default=None, alias="OPENAI_API_KEY")
    openai_model: str = Field(default="gpt-4.1-mini", alias="OPENAI_MODEL")
    deepseek_api_key: str | None = Field(default=None, alias="DEEPSEEK_API_KEY")
    deepseek_model: str | None = Field(default=None, alias="DEEPSEEK_MODEL")
    qwen_api_key: str | None = Field(default=None, alias="QWEN_API_KEY")
    qwen_model: str | None = Field(default=None, alias="QWEN_MODEL")
    claude_api_key: str | None = Field(default=None, alias="CLAUDE_API_KEY")
    claude_model: str | None = Field(default=None, alias="CLAUDE_MODEL")

    cors_origins: list[str] = Field(
        default=["http://localhost:3000"],
        alias="CORS_ORIGINS",
    )

    model_config = SettingsConfigDict(
        env_file=(REPOSITORY_ROOT / ".env", API_ROOT / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
        populate_by_name=True,
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
