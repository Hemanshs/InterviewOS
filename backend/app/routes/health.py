from fastapi import APIRouter

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
