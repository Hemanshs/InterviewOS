from functools import lru_cache

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    APP_NAME: str = "interviewos-api"
    APP_VERSION: str = "1.0.0"
    APP_ENV: str = "development"
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
    GEMINI_REPORT_MODEL: str = ""
    ELEVENLABS_API_KEY: str = ""
    ELEVENLABS_VOICE_ID: str = "21m00Tcm4TlvDq8ikWAM"
    ALLOWED_ORIGINS: list[str] = Field(
        default_factory=lambda: [
            "http://localhost:3000",
            "http://127.0.0.1:3000",
        ]
    )
    BACKEND_CORS_ORIGINS: str = ""
    VERCEL_URL: str = ""
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

    @field_validator("ALLOWED_ORIGINS", mode="before")
    @classmethod
    def normalize_allowed_origins(cls, value):
        if isinstance(value, list):
            return value
        if isinstance(value, str):
            stripped = value.strip()
            if not stripped:
                return []
            if stripped.startswith("["):
                import json

                try:
                    parsed = json.loads(stripped)
                except json.JSONDecodeError:
                    parsed = None
                if isinstance(parsed, list):
                    return [str(item).strip() for item in parsed if str(item).strip()]
            return [item.strip() for item in stripped.split(",") if item.strip()]
        return value

    @property
    def cors_origins(self) -> list[str]:
        origins = list(self.ALLOWED_ORIGINS)
        raw_backend_origins = self.BACKEND_CORS_ORIGINS.strip()
        if raw_backend_origins:
            if raw_backend_origins.startswith("["):
                import json

                try:
                    parsed = json.loads(raw_backend_origins)
                except json.JSONDecodeError:
                    parsed = []
                if isinstance(parsed, list):
                    origins = [str(item).strip() for item in parsed if str(item).strip()]
            else:
                origins = [
                    item.strip() for item in raw_backend_origins.split(",") if item.strip()
                ]
        if self.VERCEL_URL:
            vercel_url = self.VERCEL_URL
            if not vercel_url.startswith("http"):
                vercel_url = f"https://{vercel_url}"
            if vercel_url not in origins:
                origins.append(vercel_url)
        return origins

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
