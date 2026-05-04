import time

import httpx
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwk, jwt
from jose.utils import base64url_decode

from app.core.config import settings

bearer_scheme = HTTPBearer(auto_error=False)
_JWKS_CACHE: dict[str, object] = {"expires_at": 0.0, "keys": None}
_JWKS_CACHE_TTL_SECONDS = 300


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> str:
    """
    Verify Supabase JWT and return user_id (UUID string).

    DEV_AUTH_BYPASS and REQUIRE_AUTH=false short-circuit before JWT parsing.
    """
    if settings.DEV_AUTH_BYPASS or not settings.REQUIRE_AUTH:
        return settings.DEV_USER_ID

    if not credentials or not credentials.credentials:
        raise HTTPException(
            status_code=401,
            detail={
                "success": False,
                "error": {
                    "code": "UNAUTHORIZED",
                    "message": "Authentication required",
                    "details": {},
                },
            },
        )

    token = credentials.credentials

    if token == "mock_token" and settings.DEBUG:
        return settings.DEV_USER_ID

    payload = None
    last_error = None

    if settings.SUPABASE_JWT_SECRET:
        try:
            payload = jwt.decode(
                token,
                settings.SUPABASE_JWT_SECRET,
                algorithms=["HS256"],
                options={"verify_aud": False},
            )
        except JWTError as exc:
            last_error = exc

    if payload is None and settings.SUPABASE_URL:
        try:
            payload = await _decode_with_supabase_jwks(token)
        except Exception as exc:  # pragma: no cover - network/runtime fallback
            last_error = exc

    if payload is None:
        raise HTTPException(
            status_code=401,
            detail={
                "success": False,
                "error": {
                    "code": "UNAUTHORIZED",
                    "message": "Invalid or expired token",
                    "details": {"reason": str(last_error) if last_error else "verification failed"},
                },
            },
        )

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=401,
            detail={
                "success": False,
                "error": {
                    "code": "UNAUTHORIZED",
                    "message": "Token missing user ID",
                    "details": {},
                },
            },
        )

    return str(user_id)


def get_user_email_from_token(token: str) -> str | None:
    try:
        payload = jwt.decode(
            token,
            settings.SUPABASE_JWT_SECRET,
            algorithms=["HS256"],
            options={"verify_aud": False},
        )
        return payload.get("email")
    except Exception:
        return None


async def _get_supabase_jwks() -> list[dict]:
    now = time.time()
    cached_keys = _JWKS_CACHE.get("keys")
    expires_at = float(_JWKS_CACHE.get("expires_at", 0.0) or 0.0)
    if cached_keys and now < expires_at:
        return cached_keys  # type: ignore[return-value]

    jwks_url = f"{settings.SUPABASE_URL.rstrip('/')}/auth/v1/.well-known/jwks.json"
    async with httpx.AsyncClient(timeout=5.0) as client:
        response = await client.get(jwks_url)
        response.raise_for_status()
        payload = response.json()

    keys = payload.get("keys", [])
    _JWKS_CACHE["keys"] = keys
    _JWKS_CACHE["expires_at"] = now + _JWKS_CACHE_TTL_SECONDS
    return keys


async def _decode_with_supabase_jwks(token: str) -> dict:
    header = jwt.get_unverified_header(token)
    kid = header.get("kid")
    alg = header.get("alg")
    if not kid or not alg:
        raise JWTError("Token missing kid or alg header")

    keys = await _get_supabase_jwks()
    matching_key = next((key for key in keys if key.get("kid") == kid), None)
    if matching_key is None:
        raise JWTError("No matching JWKS key found")

    public_key = jwk.construct(matching_key, algorithm=alg)
    message, encoded_signature = token.rsplit(".", 1)
    decoded_signature = base64url_decode(encoded_signature.encode())
    if not public_key.verify(message.encode(), decoded_signature):
        raise JWTError("Signature verification failed")

    claims = jwt.get_unverified_claims(token)
    exp = claims.get("exp")
    if exp is not None and time.time() >= float(exp):
        raise JWTError("Token has expired")
    return claims
