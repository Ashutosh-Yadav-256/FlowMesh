from typing import Dict, Any
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select

from app.dependencies import CurrentAuth, DbSession
from app.services.auth_service import create_access_token, hash_secret, verify_secret
from app.models.tenant import User, Membership, Tenant
from app.config import settings

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
async def login(payload: LoginRequest, db: DbSession) -> AuthResponse:
    """Issues a session token encoding verified user identity, target tenant, and RBAC role."""
    norm_email = payload.email.lower().strip()

    stmt = select(User).where(User.email == norm_email)
    res = await db.execute(stmt)
    user = res.scalar_one_or_none()

    if not user:
        if settings.environment in ("development", "test"):
            user_id = f"usr_{norm_email.split('@')[0]}"
            user = User(
                id=user_id,
                email=norm_email,
                name=norm_email.split("@")[0].capitalize(),
                hashed_password=hash_secret(payload.password),
                is_active=True,
            )
            db.add(user)
            await db.flush()
        else:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )

    if user.hashed_password:
        if not verify_secret(payload.password, user.hashed_password):
            if settings.environment in ("development", "test"):
                user.hashed_password = hash_secret(payload.password)
                await db.flush()
            else:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid email or password",
                    headers={"WWW-Authenticate": "Bearer"},
                )
    else:
        user.hashed_password = hash_secret(payload.password)
        await db.flush()

    t_stmt = select(Tenant).where(Tenant.id == payload.tenant_id)
    t_res = await db.execute(t_stmt)
    tenant = t_res.scalar_one_or_none()
    if not tenant and settings.environment in ("development", "test"):
        tenant = Tenant(id=payload.tenant_id, name=payload.tenant_id, slug=payload.tenant_id, is_active=True)
        db.add(tenant)
        await db.flush()

    m_stmt = select(Membership).where(
        Membership.user_id == user.id,
        Membership.tenant_id == payload.tenant_id,
    )
    m_res = await db.execute(m_stmt)
    membership = m_res.scalar_one_or_none()

    if not membership:
        if settings.environment in ("development", "test"):
            effective_role = payload.role if payload.role in ("owner", "operator", "developer", "viewer") else "developer"
            membership = Membership(
                id=f"mem_{user.id}_{payload.tenant_id}",
                tenant_id=payload.tenant_id,
                user_id=user.id,
                role=effective_role,
            )
            db.add(membership)
            await db.flush()
        else:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"User '{norm_email}' is not a member of tenant '{payload.tenant_id}'",
            )
    else:
        effective_role = membership.role

    await db.commit()

    token = create_access_token(
        user_id=user.id,
        tenant_id=payload.tenant_id,
        role=effective_role,
        email=norm_email,
    )

    return AuthResponse(
        access_token=token,
        user_id=user.id,
        email=norm_email,
        tenant_id=payload.tenant_id,
        role=effective_role,
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

