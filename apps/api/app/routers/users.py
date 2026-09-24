from typing import Dict, Any
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

from app.dependencies import CurrentAuth
from app.services.auth_service import create_access_token

router = APIRouter(prefix="/api/v1/auth", tags=["Authentication & Identity"])


class LoginRequest(BaseModel):
    email: str
    password: str
    tenant_id: str = "tenant_acme"
    role: str = "owner"


class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: str
    email: str
    tenant_id: str
    role: str


class UserProfile(BaseModel):
    user_id: str
    email: str
    tenant_id: str
    role: str


@router.post("/token", response_model=AuthResponse)
async def login(payload: LoginRequest) -> AuthResponse:
    """Issues a session token encoding user identity, target tenant, and RBAC role."""
    user_id = f"usr_{payload.email.split('@')[0]}"
    token = create_access_token(
        user_id=user_id,
        tenant_id=payload.tenant_id,
        role=payload.role,
        email=payload.email,
    )

    return AuthResponse(
        access_token=token,
        user_id=user_id,
        email=payload.email,
        tenant_id=payload.tenant_id,
        role=payload.role,
    )


@router.get("/me", response_model=UserProfile)
async def get_current_user_profile(auth: CurrentAuth) -> UserProfile:
    """Returns the authenticated identity and current tenant/role scope."""
    return UserProfile(
        user_id=auth.user_id,
        email=auth.email,
        tenant_id=auth.tenant_id,
        role=auth.role,
    )
