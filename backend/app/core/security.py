from uuid import UUID

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt

from app.core.config import get_settings, settings

security_scheme = HTTPBearer(auto_error=False)
MOCK_USER_ID = str(UUID("00000000-0000-0000-0000-000000000001"))


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(security_scheme),
) -> str:
    if settings.USE_MOCK_AI:
        if credentials is None or not credentials.credentials:
            return MOCK_USER_ID

        try:
            payload = jwt.decode(
                credentials.credentials,
                settings.SUPABASE_JWT_SECRET,
                algorithms=["HS256"],
            )
            user_id = payload.get("sub")
            return user_id or MOCK_USER_ID
        except JWTError:
            return MOCK_USER_ID

    if credentials is None or not credentials.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authentication token",
        )

    current_settings = get_settings()

    try:
        payload = jwt.decode(
            credentials.credentials,
            current_settings.SUPABASE_JWT_SECRET,
            algorithms=["HS256"],
        )
    except JWTError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token",
        ) from exc

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token",
        )

    return user_id
