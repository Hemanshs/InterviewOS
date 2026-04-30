import enum
from typing import Generic, Optional, TypeVar

from fastapi.responses import JSONResponse
from pydantic import BaseModel

T = TypeVar("T")


class ErrorCode(str, enum.Enum):
    UNAUTHORIZED = "UNAUTHORIZED"
    FORBIDDEN = "FORBIDDEN"
    VALIDATION_ERROR = "VALIDATION_ERROR"
    FILE_TOO_LARGE = "FILE_TOO_LARGE"
    UNSUPPORTED_FILE_TYPE = "UNSUPPORTED_FILE_TYPE"
    RATE_LIMIT_EXCEEDED = "RATE_LIMIT_EXCEEDED"
    SESSION_NOT_FOUND = "SESSION_NOT_FOUND"
    SESSION_ALREADY_COMPLETED = "SESSION_ALREADY_COMPLETED"
    QUESTION_NOT_FOUND = "QUESTION_NOT_FOUND"
    TRANSCRIPTION_FAILED = "TRANSCRIPTION_FAILED"
    LLM_FAILED = "LLM_FAILED"
    VOICE_GENERATION_FAILED = "VOICE_GENERATION_FAILED"
    INTERNAL_ERROR = "INTERNAL_ERROR"
    NOT_IMPLEMENTED = "NOT_IMPLEMENTED"


class ErrorDetail(BaseModel):
    code: str
    message: str
    details: Optional[dict] = None


class ErrorResponse(BaseModel):
    success: bool = False
    error: ErrorDetail


class SuccessResponse(BaseModel, Generic[T]):
    success: bool = True
    data: T
    message: str = "Request completed successfully"


def not_implemented() -> JSONResponse:
    return JSONResponse(
        status_code=501,
        content=ErrorResponse(
            error=ErrorDetail(
                code=ErrorCode.NOT_IMPLEMENTED,
                message="This endpoint is not yet implemented",
            )
        ).model_dump(),
    )
