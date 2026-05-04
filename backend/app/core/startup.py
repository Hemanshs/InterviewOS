import logging
import sys

from app.core.config import settings

logger = logging.getLogger("interviewos.startup")

ALWAYS_REQUIRED = [
    "DATABASE_URL",
    "SUPABASE_JWT_SECRET",
]

CONDITIONAL_REQUIRED = {
    "GEMINI_API_KEY": lambda: not settings.USE_MOCK_LLM,
    "ELEVENLABS_API_KEY": lambda: not settings.USE_MOCK_TTS,
    "SUPABASE_URL": lambda: settings.REQUIRE_AUTH and not settings.DEV_AUTH_BYPASS,
    "SUPABASE_ANON_KEY": lambda: settings.REQUIRE_AUTH and not settings.DEV_AUTH_BYPASS,
}


def validate_startup_config() -> None:
    errors: list[str] = []

    for var in ALWAYS_REQUIRED:
        value = getattr(settings, var, None)
        if not value:
            errors.append(f"  MISSING: {var}")

    for var, condition in CONDITIONAL_REQUIRED.items():
        if condition():
            value = getattr(settings, var, None)
            if not value:
                errors.append(f"  MISSING: {var} (required for current config)")

    if errors:
        logger.critical("=" * 60)
        logger.critical("InterviewOS startup failed — missing required config:")
        for err in errors:
            logger.critical(err)
        logger.critical("=" * 60)
        logger.critical("Check backend/.env.example for required variables.")
        sys.exit(1)

    logger.info("InterviewOS starting up")
    logger.info("  APP_ENV: %s", settings.APP_ENV)
    logger.info(
        "  LLM_PROVIDER: %s | USE_MOCK_LLM: %s",
        settings.LLM_PROVIDER,
        settings.USE_MOCK_LLM,
    )
    logger.info(
        "  STT_PROVIDER: %s | USE_MOCK_STT: %s",
        settings.STT_PROVIDER,
        settings.USE_MOCK_STT,
    )
    logger.info("  USE_MOCK_TTS: %s", settings.USE_MOCK_TTS)
    logger.info(
        "  REQUIRE_AUTH: %s | DEV_AUTH_BYPASS: %s",
        settings.REQUIRE_AUTH,
        settings.DEV_AUTH_BYPASS,
    )
    logger.info("  CORS origins: %s", settings.cors_origins)

    if settings.DEV_AUTH_BYPASS and settings.APP_ENV == "production":
        logger.warning("DEV_AUTH_BYPASS=true in production — this is unsafe!")
