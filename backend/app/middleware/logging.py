import contextlib
import logging
import time
import uuid

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

logger = logging.getLogger("interviewos.requests")

QUIET_PATHS = {"/api/health", "/docs", "/openapi.json", "/redoc"}


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        request_id = str(uuid.uuid4())[:8]
        start = time.time()
        path = request.url.path

        if path not in QUIET_PATHS:
            logger.info("[%s] → %s %s", request_id, request.method, path)

        response = await call_next(request)

        duration_ms = int((time.time() - start) * 1000)
        if path not in QUIET_PATHS:
            level = logging.WARNING if response.status_code >= 400 else logging.INFO
            logger.log(level, "[%s] ← %s %s (%sms)", request_id, response.status_code, path, duration_ms)

        response.headers["X-Request-Id"] = request_id
        response.headers["X-Response-Time-Ms"] = str(duration_ms)
        return response


@contextlib.contextmanager
def log_ai_call(provider: str, operation: str):
    start = time.time()
    ai_logger = logging.getLogger(f"interviewos.ai.{provider}")
    try:
        yield
        duration_ms = int((time.time() - start) * 1000)
        ai_logger.info("%s completed in %sms", operation, duration_ms)
    except Exception as exc:
        duration_ms = int((time.time() - start) * 1000)
        ai_logger.error("%s failed after %sms: %s", operation, duration_ms, type(exc).__name__)
        raise
