"""Authentication routes."""

from fastapi import APIRouter
from pydantic import BaseModel, EmailStr

router = APIRouter(prefix="/api/auth", tags=["auth"])

class SignUpRequest(BaseModel):
    email: EmailStr
    password: str

class SignInRequest(BaseModel):
    email: EmailStr
    password: str

@router.post("/signup")
async def sign_up(request: SignUpRequest):
    """Create a new account."""

    return {
        "user": {"email": request.email},
        "session": None,
        "next_step": "/bank-linking",
        "message": "Account created. Continue to bank linking.",
    }

@router.post("/signin")
async def sign_in(request: SignInRequest):
    """Sign in to an existing account."""

    if request.email == "demo@radar.com" and request.password == "demo123":
        return {
            "user": {"email": request.email, "demo": True},
            "access_token": "demo-token",
            "next_step": "/dashboard",
        }

    return {
        "user": {"email": request.email},
        "access_token": "placeholder-token",
        "next_step": "/bank-linking",
    }

@router.get("/me")
async def get_current_user():
    """Get current user info."""

    return {"user": {"email": "demo@radar.com", "demo": True}}

@router.post("/logout")
async def logout():
    """Logout user."""

    return {"success": True}
