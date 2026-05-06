from types import SimpleNamespace

import pytest
from jose import JWTError
from fastapi import HTTPException

from backend.api import deps
from backend.models.api.auth import AuthenticatedUser


def test_decode_supabase_token_validates_audience(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(
        deps,
        "get_settings",
        lambda: SimpleNamespace(
            supabase_url="https://example.supabase.co",
            supabase_legacy_jwt_secret="secret",
            supabase_jwt_audience="authenticated",
        ),
    )
    monkeypatch.setattr(deps.pyjwt, "get_unverified_header", lambda token: {"alg": "HS256"})

    captured: dict[str, object] = {}

    def fake_decode(token, key, algorithms, issuer, audience):
        captured["token"] = token
        captured["key"] = key
        captured["algorithms"] = algorithms
        captured["issuer"] = issuer
        captured["audience"] = audience
        return {"sub": "user-123"}

    monkeypatch.setattr(deps.pyjwt, "decode", fake_decode)

    payload = deps.decode_supabase_token("signed-token")

    assert payload == {"sub": "user-123"}
    assert captured["audience"] == "authenticated"
    assert captured["issuer"] == "https://example.supabase.co/auth/v1"


def test_decode_supabase_token_rejects_unsupported_algorithm(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(
        deps,
        "get_settings",
        lambda: SimpleNamespace(
            supabase_url="https://example.supabase.co",
            supabase_legacy_jwt_secret="secret",
            supabase_jwt_audience="authenticated",
        ),
    )
    monkeypatch.setattr(deps.pyjwt, "get_unverified_header", lambda token: {"alg": "none"})

    with pytest.raises(JWTError):
        deps.decode_supabase_token("unsigned-token")


def test_decode_supabase_token_rejects_invalid_header(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(
        deps,
        "get_settings",
        lambda: SimpleNamespace(
            supabase_url="https://example.supabase.co",
            supabase_legacy_jwt_secret="secret",
            supabase_jwt_audience="authenticated",
        ),
    )

    def bad_header(token):
        raise deps.pyjwt.PyJWTError("bad header")

    monkeypatch.setattr(deps.pyjwt, "get_unverified_header", bad_header)

    with pytest.raises(JWTError, match="Invalid token header"):
        deps.decode_supabase_token("broken-token")


def test_decode_supabase_token_requires_legacy_secret_for_hs256(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(
        deps,
        "get_settings",
        lambda: SimpleNamespace(
            supabase_url="https://example.supabase.co",
            supabase_legacy_jwt_secret="",
            supabase_jwt_audience="authenticated",
        ),
    )
    monkeypatch.setattr(deps.pyjwt, "get_unverified_header", lambda token: {"alg": "HS256"})

    with pytest.raises(JWTError, match="Legacy JWT secret is not configured"):
        deps.decode_supabase_token("signed-token")


def test_decode_supabase_token_uses_jwks_for_asymmetric_algorithms(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(
        deps,
        "get_settings",
        lambda: SimpleNamespace(
            supabase_url="https://example.supabase.co",
            supabase_legacy_jwt_secret="secret",
            supabase_jwt_audience="authenticated",
        ),
    )
    monkeypatch.setattr(deps.pyjwt, "get_unverified_header", lambda token: {"alg": "RS256"})
    monkeypatch.setattr(
        deps,
        "get_jwks_client",
        lambda: SimpleNamespace(get_signing_key_from_jwt=lambda token: SimpleNamespace(key="public-key")),
    )

    captured: dict[str, object] = {}

    def fake_decode(token, key, algorithms, issuer, audience):
        captured["key"] = key
        captured["algorithms"] = algorithms
        return {"sub": "user-456"}

    monkeypatch.setattr(deps.pyjwt, "decode", fake_decode)

    assert deps.decode_supabase_token("signed-token") == {"sub": "user-456"}
    assert captured["key"] == "public-key"
    assert captured["algorithms"] == ["RS256"]


def test_decode_supabase_token_requires_absolute_supabase_url(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(
        deps,
        "get_settings",
        lambda: SimpleNamespace(
            supabase_url="",
            supabase_legacy_jwt_secret="secret",
            supabase_jwt_audience="authenticated",
        ),
    )
    monkeypatch.setattr(deps.pyjwt, "get_unverified_header", lambda token: {"alg": "RS256"})

    with pytest.raises(RuntimeError, match="SUPABASE_URL must be an absolute URL"):
        deps.decode_supabase_token("signed-token")


@pytest.mark.asyncio
async def test_get_current_user_returns_id_and_email(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(
        deps,
        "decode_supabase_token",
        lambda token: {"sub": "user-123", "email": "admin@example.com"},
    )

    user = await deps.get_current_user("signed-token")

    assert user == AuthenticatedUser(id="user-123", email="admin@example.com")


@pytest.mark.asyncio
async def test_get_current_user_raises_401_for_invalid_token(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(deps, "decode_supabase_token", lambda token: (_ for _ in ()).throw(JWTError("bad token")))

    with pytest.raises(HTTPException) as exc:
        await deps.get_current_user("bad-token")

    assert exc.value.status_code == 401
    assert exc.value.detail == "Invalid or expired token"


@pytest.mark.asyncio
async def test_get_current_user_raises_503_for_auth_configuration_errors(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(
        deps,
        "decode_supabase_token",
        lambda token: (_ for _ in ()).throw(RuntimeError("SUPABASE_URL must be an absolute URL")),
    )

    with pytest.raises(HTTPException) as exc:
        await deps.get_current_user("bad-token")

    assert exc.value.status_code == 503
    assert exc.value.detail == "Authentication is not configured correctly"
