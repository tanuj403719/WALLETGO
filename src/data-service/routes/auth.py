"""
Auth endpoints: signup, signin, me, logout.
"""

from __future__ import annotations

from fastapi import APIRouter

from models.db import SessionLocal, UserModel
from schemas.requests import SignInRequest, SignUpRequest
from services.auth_service import (
    DEMO_USER_ID,
    create_token,
    hash_password,
    verify_password,
)

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/signup")
async def sign_up(request: SignUpRequest):
    """Create a new account persisted to SQLite."""
    with SessionLocal() as session:
        existing = session.query(UserModel).filter_by(email=request.email).first()
        if existing:
            token = create_token(existing.id, existing.email)
            return {
                "user": {"id": existing.id, "email": request.email},
                "access_token": token,
                "message": "Account already exists. Signed in automatically.",
            }

        user = UserModel(
            email=request.email,
            password_hash=hash_password(request.password),
            display_name=request.email.split("@")[0],
        )
        session.add(user)
        session.commit()
        session.refresh(user)
        token = create_token(user.id, user.email)

    return {
        "user": {"id": user.id, "email": request.email},
        "access_token": token,
        "next_step": "/bank-linking",
        "message": "Account created. Continue to bank linking.",
    }


@router.post("/signin")
async def sign_in(request: SignInRequest):
    """Sign in to an existing account."""
    with SessionLocal() as session:
        user = session.query(UserModel).filter_by(email=request.email).first()

        if user and verify_password(request.password, user.password_hash):
            token = create_token(user.id, user.email)
            return {
                "user": {
                    "id": user.id,
                    "email": user.email,
                    "demo": user.id == DEMO_USER_ID,
                },
                "access_token": token,
                "next_step": "/dashboard",
            }

    return {
        "error": "Invalid email or password",
        "user": None,
        "access_token": None,
    }


@router.get("/me")
async def get_current_user():
    """Get current user info (demo shortcut — gateway enforces auth)."""
    return {"user": {"email": "demo@radar.com", "demo": True}}


@router.post("/logout")
async def logout():
    return {"success": True}
