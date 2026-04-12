"""
FastAPI dependency: JWT verification.

Supports:
- Local HS256 JWTs (legacy data-service flow)
- Supabase JWTs via JWKS
- Demo bypass token for local demo mode
"""

from __future__ import annotations

import os
from typing import Optional

import jwt
from dotenv import load_dotenv
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pathlib import Path

_project_root = Path(__file__).resolve().parent.parent.parent
load_dotenv(_project_root / ".env")

JWT_SECRET = os.getenv("JWT_SECRET", "walletgo-hackathon-demo-secret-2024")
JWT_ALGORITHM = "HS256"
SUPABASE_URL = os.getenv("SUPABASE_URL") or os.getenv("VITE_SUPABASE_URL")
SUPABASE_AUDIENCE = os.getenv("SUPABASE_JWT_AUDIENCE", "authenticated")
SUPABASE_ISSUER = (
    os.getenv("SUPABASE_ISSUER")
    or (f"{SUPABASE_URL.rstrip('/')}/auth/v1" if SUPABASE_URL else "")
)
SUPABASE_JWKS_URL = (
    f"{SUPABASE_URL.rstrip('/')}/auth/v1/.well-known/jwks.json" if SUPABASE_URL else ""
)

_bearer_scheme = HTTPBearer(auto_error=False)
_supabase_jwks_client = jwt.PyJWKClient(SUPABASE_JWKS_URL) if SUPABASE_JWKS_URL else None


def _extract_subject(payload: dict) -> str:
    user_id = str(payload.get("sub", ""))
    if not user_id:
        raise HTTPException(
            status_code=401,
            detail={"error": "Invalid token", "message": "Token payload missing 'sub' claim."},
        )
    return user_id


def _decode_local_jwt(token: str) -> str:
    payload = jwt.decode(
        token,
        JWT_SECRET,
        algorithms=[JWT_ALGORITHM],
        audience="authenticated",
    )
    return _extract_subject(payload)


def _decode_supabase_jwt(token: str) -> str:
    if _supabase_jwks_client is None:
        raise jwt.InvalidTokenError("Supabase JWKS is not configured.")

    signing_key = _supabase_jwks_client.get_signing_key_from_jwt(token)
    payload = jwt.decode(
        token,
        signing_key.key,
        algorithms=["RS256", "ES256"],
        audience=SUPABASE_AUDIENCE,
        issuer=SUPABASE_ISSUER,
    )
    return _extract_subject(payload)


async def verify_token(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(_bearer_scheme),
) -> str:
    if credentials is None:
        raise HTTPException(
            status_code=401,
            detail={"error": "Unauthorized", "message": "Authorization header is required."},
        )

    token = credentials.credentials
    if token == "demo-token":
        return "demo-user"

    try:
        return _decode_local_jwt(token)
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=401,
            detail={"error": "Token expired", "message": "Your session has expired. Please sign in again."},
        )
    except jwt.InvalidTokenError as local_exc:
        local_error = str(local_exc)

    try:
        return _decode_supabase_jwt(token)
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=401,
            detail={"error": "Token expired", "message": "Your Supabase session has expired. Please sign in again."},
        )
    except jwt.InvalidTokenError as supabase_exc:
        raise HTTPException(
            status_code=401,
            detail={
                "error": "Invalid token",
                "message": (
                    "Token verification failed with local and Supabase validators: "
                    f"{local_error}; {supabase_exc}"
                ),
            },
        )
