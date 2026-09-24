import uuid
from typing import List, Optional
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from app.dependencies import DbSession, CurrentAuth, require_permission
from app.services.audit_service import record_audit
from app.services.auth_service import create_access_token
from app.models.tenant import Tenant
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/api/v1/tenants", tags=["Tenancy & Organizations"])


class TenantCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    slug: str = Field(..., min_length=2, max_length=50)


class TenantResponse(BaseModel):
    id: str
    name: str
    slug: str
    is_active: bool
    role: str


class SwitchTenantRequest(BaseModel):
    target_tenant_id: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    active_tenant_id: str
    role: str


async def _ensure_default_tenants(db: AsyncSession) -> None:
    """In development or test mode, ensures initial default tenants exist in DB."""
    from app.config import settings
    if settings.environment in ("development", "test"):
        defaults = [
            ("tenant_acme", "Acme Global Corp (Demo)", "acme-corp"),
            ("tenant_prod", "Production Workspace (Clean)", "production-workspace"),
            ("tenant_beta", "Beta Logistics Inc", "beta-logistics"),
        ]
        for tid, tname, tslug in defaults:
            stmt = select(Tenant).where(Tenant.id == tid)
            res = await db.execute(stmt)
            if not res.scalar_one_or_none():
                db.add(Tenant(id=tid, name=tname, slug=tslug, is_active=True))
        await db.commit()


@router.get("/current", response_model=TenantResponse)
async def get_current_tenant(auth: CurrentAuth, db: DbSession) -> TenantResponse:
    """Returns the currently active tenant from the session context."""
    await _ensure_default_tenants(db)
    stmt = select(Tenant).where(Tenant.id == auth.tenant_id)
    result = await db.execute(stmt)
    tenant = result.scalar_one_or_none()
    if not tenant:
        return TenantResponse(
            id=auth.tenant_id,
            name="Active Tenant",
            slug=auth.tenant_id,
            is_active=True,
            role=auth.role,
        )
    return TenantResponse(
        id=tenant.id,
        name=tenant.name,
        slug=tenant.slug,
        is_active=tenant.is_active,
        role=auth.role,
    )


@router.get("", response_model=List[TenantResponse])
async def list_user_tenants(auth: CurrentAuth, db: DbSession) -> List[TenantResponse]:
    """List all tenants the authenticated user belongs to."""
    await _ensure_default_tenants(db)
    stmt = select(Tenant).where(Tenant.is_active == True).order_by(Tenant.created_at)
    result = await db.execute(stmt)
    tenants = result.scalars().all()
    return [
        TenantResponse(
            id=t.id,
            name=t.name,
            slug=t.slug,
            is_active=t.is_active,
            role=auth.role,
        )
        for t in tenants
    ]


@router.post("", response_model=TenantResponse, status_code=status.HTTP_201_CREATED)
async def create_tenant(
    payload: TenantCreate,
    db: DbSession,
    auth: CurrentAuth,
) -> TenantResponse:
    """Create a new enterprise tenant. Enforces OWNER permission and records an audit event."""
    if auth.role != "owner":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only Organization Owners can provision new tenants",
        )

    new_id = f"tenant_{payload.slug.replace('-', '_')}"

    existing_stmt = select(Tenant).where(Tenant.id == new_id)
    existing = (await db.execute(existing_stmt)).scalar_one_or_none()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Tenant '{new_id}' already exists",
        )

    new_tenant = Tenant(
        id=new_id,
        name=payload.name,
        slug=payload.slug,
        is_active=True,
    )
    db.add(new_tenant)
    await db.commit()
    await db.refresh(new_tenant)

    await record_audit(
        db=db,
        tenant_id=new_id,
        actor=auth.email,
        action="tenant.create",
        resource=f"tenant:{new_id}",
        result="SUCCESS",
        metadata={"slug": payload.slug, "name": payload.name},
    )

    return TenantResponse(
        id=new_tenant.id,
        name=new_tenant.name,
        slug=new_tenant.slug,
        is_active=new_tenant.is_active,
        role="owner",
    )


@router.post("/switch", response_model=TokenResponse)
async def switch_active_tenant(
    payload: SwitchTenantRequest,
    auth: CurrentAuth,
    db: DbSession,
) -> TokenResponse:
    """Switch active tenant and issue updated JWT credentials."""
    await _ensure_default_tenants(db)
    stmt = select(Tenant).where(Tenant.id == payload.target_tenant_id)
    result = await db.execute(stmt)
    target = result.scalar_one_or_none()
    if not target:
        raise HTTPException(status_code=404, detail="Tenant not found or membership not granted")

    token = create_access_token(
        user_id=auth.user_id,
        tenant_id=target.id,
        role=auth.role,
        email=auth.email,
    )

    return TokenResponse(
        access_token=token,
        active_tenant_id=target.id,
        role=auth.role,
    )
