from fastapi import HTTPException

from app.schemas.common import ErrorCode

ALLOWED_AUDIO_MIME_TYPES = {
    "audio/webm",
    "audio/webm;codecs=opus",
    "audio/mpeg",
    "audio/mp3",
    "audio/wav",
    "audio/x-wav",
    "audio/mp4",
    "audio/aac",
    "audio/x-m4a",
    "audio/m4a",
    "video/mp4",
}

MAX_AUDIO_SIZE_BYTES = 10 * 1024 * 1024  # 10MB

FILLER_WORDS = {
    "um",
    "uh",
    "like",
    "you know",
    "basically",
    "literally",
    "actually",
    "so",
    "right",
    "okay",
    "kind of",
    "sort of",
    "i mean",
    "you see",
    "well",
}


def validate_audio_mime_type(content_type: str) -> None:
    """Raise HTTPException 400 if MIME type not allowed."""
    normalized_content_type = (content_type or "").split(";", 1)[0].strip().lower()

    if normalized_content_type not in ALLOWED_AUDIO_MIME_TYPES:
        raise HTTPException(
            status_code=400,
            detail={
                "success": False,
                "error": {
                    "code": ErrorCode.UNSUPPORTED_FILE_TYPE,
                    "message": "Unsupported audio format",
                    "details": {
                        "received_content_type": content_type,
                        "normalized_content_type": normalized_content_type,
                        "allowed_types": sorted(ALLOWED_AUDIO_MIME_TYPES),
                    },
                },
            },
        )


def validate_audio_size(size_bytes: int) -> None:
    """Raise HTTPException 400 if file exceeds 10MB."""
    if size_bytes > MAX_AUDIO_SIZE_BYTES:
        raise HTTPException(
            status_code=400,
            detail={
                "success": False,
                "error": {
                    "code": ErrorCode.FILE_TOO_LARGE,
                    "message": "Audio file must be less than 10MB",
                    "details": {
                        "max_size_mb": 10,
                        "received_size_mb": round(size_bytes / 1024 / 1024, 2),
                    },
                },
            },
        )


def validate_audio_duration(duration_seconds: float, max_seconds: int = 60) -> None:
    """Raise HTTPException 400 if duration exceeds limit."""
    if duration_seconds > max_seconds:
        raise HTTPException(
            status_code=400,
            detail={
                "success": False,
                "error": {
                    "code": ErrorCode.VALIDATION_ERROR,
                    "message": "Audio duration exceeds the allowed limit",
                    "details": {
                        "max_duration_seconds": max_seconds,
                        "received_duration_seconds": duration_seconds,
                    },
                },
            },
        )


def count_words(text: str) -> int:
    """Count words in transcript text."""
    return len(text.split()) if text.strip() else 0


def detect_filler_words(text: str) -> dict:
    """
    Detect filler words in transcript.
    Returns: {"count": int, "examples": list[str]}
    """
    text_lower = text.lower()
    found = []
    for word in FILLER_WORDS:
        if word in text_lower:
            found.append(word)
    return {
        "count": len(found),
        "examples": found[:5],  # return max 5 examples
    }
