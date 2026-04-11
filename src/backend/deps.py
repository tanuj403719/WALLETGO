"""
FastAPI dependency: JWT verification.

Only the explicit string "demo-token" bypasses JWT verification.
Unauthenticated requests (no Authorization header) return HTTP 401.
"""

from __future__ import annotations

import logging
import os
from typing import Optional

import jwt
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

JWT_SECRET = os.getenv("JWT_SECRET", "prism-hackathon-demo-secret-2024")
JWT_ALGORITHM = "HS256"

logger = logging.getLogger("prism.gateway.auth")

_bearer_scheme = HTTPBearer(auto_error=False)


async def verify_token(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(_bearer_scheme),
) -> str:
    """
    Decode and verify the Bearer JWT. Returns the authenticated user_id.

    Demo bypass: if the token is exactly "demo-token", return "demo-user"
    without cryptographic verification — for frictionless hackathon judging.

    All other unauthenticated or invalid requests receive HTTP 401.
    """
    if credentials is None:
        raise HTTPException(
            status_code=401,
            detail={"error": "Unauthorized", "message": "Authorization header is required."},
        )

    token = credentials.credentials

    if token == "demo-token":
        return "demo-user"

    try:
        payload = jwt.decode(
            token,
            JWT_SECRET,
            algorithms=[JWT_ALGORITHM],
            audience="authenticated",
        )
        user_id: str = payload.get("sub", "")
        if not user_id:
            raise HTTPException(
                status_code=401,
                detail={"error": "Invalid token", "message": "Token payload missing 'sub' claim."},
            )
        return user_id

    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=401,
            detail={"error": "Token expired", "message": "Your session has expired. Please sign in again."},
        )
    except jwt.InvalidTokenError as exc:
        raise HTTPException(
            status_code=401,
            detail={"error": "Invalid token", "message": f"Token verification failed: {exc}"},
        )
