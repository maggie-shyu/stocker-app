from functools import lru_cache
from urllib.parse import urlparse

import jwt as pyjwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError
from jwt import PyJWKClient

from backend.config import get_settings
from backend.domain.ledger.interfaces import LedgerStore, StockCatalog
from backend.domain.portfolio.price_service import PriceService
from backend.infrastructure.supabase.ledger_store import SupabaseLedgerStore
from backend.infrastructure.supabase.stock_catalog import SupabaseStockCatalog
from backend.models.api.auth import AuthenticatedUser

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
_supabase_client = None
_jwks_client = None
_ALLOWED_ASYMMETRIC_ALGORITHMS = {"RS256", "RS384", "RS512", "ES256", "ES384", "ES512", "EdDSA"}


def get_supabase_auth_base_url() -> str:
    settings = get_settings()
    supabase_url = settings.supabase_url.strip().rstrip("/")
    parsed = urlparse(supabase_url)
    if not parsed.scheme or not parsed.netloc:
        raise RuntimeError("SUPABASE_URL must be an absolute URL")
    return f"{supabase_url}/auth/v1"


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
        _jwks_client = PyJWKClient(f"{get_supabase_auth_base_url()}/.well-known/jwks.json")
    return _jwks_client


def decode_supabase_token(token: str) -> dict:
    settings = get_settings()
    issuer = get_supabase_auth_base_url()
    audience = settings.supabase_jwt_audience

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
                audience=audience,
            )

        if algorithm not in _ALLOWED_ASYMMETRIC_ALGORITHMS:
            raise JWTError("Unsupported token algorithm")
        signing_key = get_jwks_client().get_signing_key_from_jwt(token)
        return pyjwt.decode(
            token,
            signing_key.key,
            algorithms=[algorithm],
            issuer=issuer,
            audience=audience,
        )
    except pyjwt.PyJWTError as exc:
        raise JWTError("Invalid or expired token") from exc


async def get_current_user(token: str = Depends(oauth2_scheme)) -> AuthenticatedUser:
    try:
        payload = decode_supabase_token(token)
        return AuthenticatedUser(
            id=payload["sub"],
            email=payload.get("email"),
        )
    except RuntimeError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Authentication is not configured correctly",
        ) from exc
    except (JWTError, KeyError) as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        ) from exc


def get_ledger_store(user: AuthenticatedUser = Depends(get_current_user)) -> LedgerStore:
    return SupabaseLedgerStore(get_supabase_client(), user.id)


def get_stock_catalog(_: AuthenticatedUser = Depends(get_current_user)) -> StockCatalog:
    return SupabaseStockCatalog(get_supabase_client())


def is_admin_user(user: AuthenticatedUser) -> bool:
    if not user.email:
        return False
    settings = get_settings()
    return user.email.strip().lower() in settings.admin_email_allowlist


def require_admin_user(
    user: AuthenticatedUser = Depends(get_current_user),
) -> AuthenticatedUser:
    if not is_admin_user(user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )
    return user


def get_admin_service(_: AuthenticatedUser = Depends(require_admin_user)):
    from backend.admin.metrics import AdminService

    return AdminService(get_supabase_client())


@lru_cache
def get_price_service() -> PriceService:
    return PriceService()
