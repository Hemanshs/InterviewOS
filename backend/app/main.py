from contextlib import asynccontextmanager
import logging

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import get_settings
from app.core.startup import validate_startup_config
from app.db.database import close_database_pool, connect_to_database
from app.middleware.logging import RequestLoggingMiddleware
from app.routes import account, audio, feedback, health, interview, resume, usage

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

settings = get_settings()
logger = logging.getLogger(__name__)
OPENAPI_TAGS = [
    {"name": "System", "description": "System health and operational endpoints."},
    {"name": "Users", "description": "User account and usage endpoints."},
    {"name": "Resumes", "description": "Resume upload and retrieval endpoints."},
    {"name": "Interviews", "description": "Interview session lifecycle endpoints."},
    {"name": "Audio", "description": "Audio upload and transcription endpoints."},
    {"name": "Evaluation", "description": "Evaluation and feedback endpoints."},
]


@asynccontextmanager
async def lifespan(app: FastAPI):
    validate_startup_config()
    app.state.db_pool = None
    try:
        app.state.db_pool = await connect_to_database()
    except Exception as exc:
        if settings.USE_MOCK_AI:
            logger.warning("Database connection unavailable in mock mode: %s", exc)
        else:
            raise
    try:
        yield
    finally:
        await close_database_pool(app.state.db_pool)


def create_application() -> FastAPI:
    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        debug=settings.DEBUG,
        lifespan=lifespan,
        openapi_tags=OPENAPI_TAGS,
    )

    app.add_middleware(RequestLoggingMiddleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.exception_handler(HTTPException)
    async def http_exception_handler(_: Request, exc: HTTPException) -> JSONResponse:
        if isinstance(exc.detail, dict):
            if "success" in exc.detail:
                return JSONResponse(status_code=exc.status_code, content=exc.detail)
            if "error" in exc.detail:
                return JSONResponse(
                    status_code=exc.status_code,
                    content={"success": False, **exc.detail},
                )
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "success": False,
                "data": None,
                "message": str(exc.detail),
            },
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(_: Request, exc: Exception) -> JSONResponse:
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "data": None,
                "message": str(exc),
            },
        )

    app.include_router(health.router, prefix="/api")
    app.include_router(resume.router, prefix="/api")
    app.include_router(interview.router, prefix="/api")
    app.include_router(audio.router, prefix="/api")
    app.include_router(feedback.router, prefix="/api")
    app.include_router(account.router, prefix="/api")
    app.include_router(usage.router, prefix="/api")

    return app


app = create_application()
