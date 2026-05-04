from functools import lru_cache

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    APP_NAME: str = "interviewos-api"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    USE_MOCK_AI: bool = True
    USE_MOCK_STT: bool = True
    USE_MOCK_LLM: bool = True
    USE_MOCK_TTS: bool = True
    DATABASE_URL: str
    ALEMBIC_DATABASE_URL: str = ""
    SUPABASE_URL: str = ""
    SUPABASE_ANON_KEY: str = ""
    SUPABASE_JWT_SECRET: str = ""
    AUTH_PROVIDER: str = "supabase"
    REQUIRE_AUTH: bool = True
    DEV_AUTH_BYPASS: bool = False
    GEMINI_API_KEY: str = ""
    STT_PROVIDER: str = "gemini"
    LLM_PROVIDER: str = "gemini"
    GEMINI_MODEL: str = "gemini-2.5-flash-lite"
    GEMINI_REPORT_MODEL: str = "gemini-2.5-flash-lite"
    ELEVENLABS_API_KEY: str = ""
    ELEVENLABS_VOICE_ID: str = "21m00Tcm4TlvDq8ikWAM"
    ALLOWED_ORIGINS: list[str] = Field(default_factory=lambda: ["http://localhost:3000"])
    DAILY_AI_BUDGET_USD: float = 20.0
    FREE_INTERVIEW_TOTAL_LIMIT: int = 1
    FREE_SESSION_QUESTION_LIMIT: int = 5
    FREE_MAX_AUDIO_SECONDS: int = 60
    FREE_MAX_AUDIO_MB: int = 10
    FREE_MAX_RESUME_MB: int = 10
    TTS_CACHE_ENABLED: bool = True
    RAW_AUDIO_RETENTION: bool = False
    DEV_USER_EMAIL: str = "dev@interviewos.local"
    DEV_USER_ID: str = "00000000-0000-0000-0000-000000000001"

    @field_validator(
        "DEBUG",
        "USE_MOCK_AI",
        "USE_MOCK_STT",
        "USE_MOCK_LLM",
        "USE_MOCK_TTS",
        "REQUIRE_AUTH",
        "DEV_AUTH_BYPASS",
        mode="before",
    )
    @classmethod
    def normalize_bool_like_values(cls, value):
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            normalized = value.strip().lower()
            if normalized in {"true", "1", "yes", "on"}:
                return True
            if normalized in {"false", "0", "no", "off", "release", "prod", "production"}:
                return False
        return value

    @field_validator("STT_PROVIDER", "LLM_PROVIDER", "AUTH_PROVIDER", mode="before")
    @classmethod
    def normalize_provider_values(cls, value):
        if isinstance(value, str):
            return value.strip().lower()
        return value

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
