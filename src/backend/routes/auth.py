"""
Auth proxy routes — forwards to data-service; no auth required.
"""

from __future__ import annotations

import os

from fastapi import APIRouter, Depends
from pydantic import BaseModel, EmailStr

from client import forward
from deps import verify_token

DATA_SERVICE_URL = os.getenv("DATA_SERVICE_URL", "http://localhost:8003")

router = APIRouter(prefix="/api/auth", tags=["auth"])


class SignUpRequest(BaseModel):
    email: EmailStr
    password: str


class SignInRequest(BaseModel):
    email: EmailStr
    password: str


@router.post("/signup")
async def sign_up(request: SignUpRequest):
    return await forward("POST", f"{DATA_SERVICE_URL}/api/auth/signup", json=request.model_dump())


@router.post("/signin")
async def sign_in(request: SignInRequest):
    return await forward("POST", f"{DATA_SERVICE_URL}/api/auth/signin", json=request.model_dump())


@router.get("/me")
async def get_current_user(user_id: str = Depends(verify_token)):
    return {"user_id": user_id, "authenticated": True}


@router.post("/logout")
async def logout():
    return await forward("POST", f"{DATA_SERVICE_URL}/api/auth/logout")
