from functools import lru_cache

import jwt as pyjwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError
from jwt import PyJWKClient

from config import get_settings
from services.price_service import PriceService

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
_supabase_client = None
_jwks_client = None


def get_supabase_client():
    global _supabase_client
    if _supabase_client is None:
        from supabase import create_client

        settings = get_settings()
        _supabase_client = create_client(
            settings.supabase_url,
            settings.supabase_secret_key,
        )
    return _supabase_client


def get_jwks_client() -> PyJWKClient:
    global _jwks_client
    if _jwks_client is None:
        settings = get_settings()
        _jwks_client = PyJWKClient(
            f"{settings.supabase_url}/auth/v1/.well-known/jwks.json"
        )
    return _jwks_client


def decode_supabase_token(token: str) -> dict:
    settings = get_settings()
    issuer = f"{settings.supabase_url}/auth/v1"

    try:
        unverified_header = pyjwt.get_unverified_header(token)
    except pyjwt.PyJWTError as exc:
        raise JWTError("Invalid token header") from exc

    algorithm = unverified_header.get("alg")
    try:
        if algorithm == "HS256":
            if not settings.supabase_legacy_jwt_secret:
                raise JWTError("Legacy JWT secret is not configured")
            return pyjwt.decode(
                token,
                settings.supabase_legacy_jwt_secret,
                algorithms=["HS256"],
                issuer=issuer,
                options={"verify_aud": False},
            )

        signing_key = get_jwks_client().get_signing_key_from_jwt(token)
        decode_algorithms = [algorithm] if algorithm else None
        return pyjwt.decode(
            token,
            signing_key.key,
            algorithms=decode_algorithms,
            issuer=issuer,
            options={"verify_aud": False},
        )
    except pyjwt.PyJWTError as exc:
        raise JWTError("Invalid or expired token") from exc


async def get_current_user(token: str = Depends(oauth2_scheme)) -> str:
    try:
        payload = decode_supabase_token(token)
        return payload["sub"]
    except (JWTError, KeyError) as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        ) from exc


def get_supabase_service(user_id: str = Depends(get_current_user)):
    from services.supabase_service import SupabaseService

    return SupabaseService(get_supabase_client(), user_id)


@lru_cache
def get_price_service() -> PriceService:
    return PriceService()
