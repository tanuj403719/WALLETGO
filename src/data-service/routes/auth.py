"""
Auth endpoints: signup, signin, me, logout.
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from schemas.requests import SignInRequest, SignUpRequest

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/signup")
async def sign_up(request: SignUpRequest):
    raise HTTPException(
        status_code=400,
        detail="Local signup is disabled. Use Supabase auth from the frontend.",
    )


@router.post("/signin")
async def sign_in(request: SignInRequest):
    raise HTTPException(
        status_code=400,
        detail="Local signin is disabled. Use Supabase auth from the frontend.",
    )


@router.get("/me")
async def get_current_user():
    return {"message": "Use gateway /api/auth/me with a Bearer token."}


@router.post("/logout")
async def logout():
    return {"success": True}
