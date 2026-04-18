"""
Pydantic request/response schemas for the data-service.
"""

from __future__ import annotations

from typing import Any, Dict, Optional

from pydantic import BaseModel, EmailStr


class SignUpRequest(BaseModel):
    email: EmailStr
    password: str


class SignInRequest(BaseModel):
    email: EmailStr
    password: str


class SaveScenarioRequest(BaseModel):
    user_id: str
    title: Optional[str] = None
    description: str
    language: str = "en"
    low_result: Dict[str, Any]
    likely_result: Dict[str, Any]
    high_result: Dict[str, Any]
    explanation: str = ""
    intent: Optional[Dict[str, Any]] = None


class CompareScenariosRequest(BaseModel):
    user_id: str
    left_id: str
    right_id: str
