from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.db.database import get_async_session

router = APIRouter(prefix="", tags=["System"])


@router.get("/health")
async def get_health():
    return {
        "success": True,
        "data": {
            "status": "ok",
            "service": "interviewos-api",
            "version": "1.0.0",
        },
        "message": "Service is running",
    }


@router.get("/health/deep", tags=["System"])
async def deep_health(db: AsyncSession = Depends(get_async_session)):
    checks: dict[str, object] = {}

    try:
        await db.execute(text("SELECT 1"))
        checks["database"] = "ok"
    except Exception as exc:
        checks["database"] = f"error: {type(exc).__name__}"

    checks["gemini_api_key"] = "present" if settings.GEMINI_API_KEY else "missing"
    checks["supabase_jwt_secret"] = "present" if settings.SUPABASE_JWT_SECRET else "missing"
    checks["elevenlabs_api_key"] = "present" if settings.ELEVENLABS_API_KEY else "missing"
    checks["mock_mode"] = {
        "llm": settings.USE_MOCK_LLM,
        "stt": settings.USE_MOCK_STT,
        "tts": settings.USE_MOCK_TTS,
    }
    checks["app_env"] = settings.APP_ENV
    checks["auth_required"] = settings.REQUIRE_AUTH
    checks["dev_bypass"] = settings.DEV_AUTH_BYPASS

    all_ok = checks["database"] == "ok"
    status_code = 200 if all_ok else 503

    return JSONResponse(
        status_code=status_code,
        content={
            "success": all_ok,
            "data": {
                "status": "ok" if all_ok else "degraded",
                "service": "interviewos-api",
                "version": settings.APP_VERSION,
                "checks": checks,
            },
            "message": "All systems operational" if all_ok else "Some checks failed",
        },
    )
