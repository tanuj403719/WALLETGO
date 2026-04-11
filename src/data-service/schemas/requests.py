"""
Pydantic request/response schemas for the data-service.
"""

from __future__ import annotations

from pydantic import BaseModel, EmailStr


class SignUpRequest(BaseModel):
    email: EmailStr
    password: str


class SignInRequest(BaseModel):
    email: EmailStr
    password: str
