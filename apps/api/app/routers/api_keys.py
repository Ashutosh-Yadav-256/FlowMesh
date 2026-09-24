import secrets
from datetime import datetime, timezone
from typing import List, Optional
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import select

from app.dependencies import DbSession, CurrentAuth
from app.services.auth_service import hash_secret
from app.services.audit_service import record_audit
from app.models.tenant import ApiKey

router = APIRouter(prefix="/api/v1/api-keys", tags=["API Keys"])


class ApiKeyCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    role: str = Field(default="developer", description="owner, operator, developer, viewer")


class ApiKeyResponse(BaseModel):
    id: str
    tenant_id: str
    name: str
    key_prefix: str
    role: str
    created_at: str
    revoked: bool
    secret_key: Optional[str] = None


@router.get("", response_model=List[ApiKeyResponse])
async def list_api_keys(auth: CurrentAuth, db: DbSession) -> List[ApiKeyResponse]:
    """Lists API keys belonging strictly to the active tenant. Plaintext secrets are never returned."""
    stmt = (
        select(ApiKey)
        .where(ApiKey.tenant_id == auth.tenant_id)
        .order_by(ApiKey.created_at.desc())
    )
    result = await db.execute(stmt)
    keys = result.scalars().all()
    return [
        ApiKeyResponse(
            id=k.id,
            tenant_id=k.tenant_id,
            name=k.name,
            key_prefix=k.key_prefix,
            role=k.role,
            created_at=k.created_at.isoformat() if k.created_at else "",
            revoked=k.revoked,
            secret_key=None,
        )
        for k in keys
    ]


@router.post("", response_model=ApiKeyResponse, status_code=status.HTTP_201_CREATED)
async def create_api_key(
    payload: ApiKeyCreate,
    db: DbSession,
    auth: CurrentAuth,
) -> ApiKeyResponse:
    """Generate an API key for automated CI/CD or agent pipelines."""

    if auth.role not in ["owner", "developer"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Role '{auth.role}' is not authorized to generate API keys",
        )

    raw_token = f"flm_{secrets.token_urlsafe(32)}"
    prefix = raw_token[:12]
    new_id = f"key_{secrets.token_hex(4)}"
    now = datetime.now(timezone.utc)

    key_record = ApiKey(
        id=new_id,
        tenant_id=auth.tenant_id,
        name=payload.name,
        key_prefix=prefix,
        hashed_key=hash_secret(raw_token),
        role=payload.role,
        created_at=now,
        revoked=False,
    )
    db.add(key_record)
    await db.commit()
    await db.refresh(key_record)

    await record_audit(
        db=db,
        tenant_id=auth.tenant_id,
        actor=auth.email,
        action="api_key.create",
        resource=f"api_key:{new_id}",
        result="SUCCESS",
        metadata={"name": payload.name, "prefix": prefix, "role": payload.role},
    )

    return ApiKeyResponse(
        id=new_id,
        tenant_id=auth.tenant_id,
        name=payload.name,
        key_prefix=prefix,
        role=payload.role,
        created_at=now.isoformat(),
        revoked=False,
        secret_key=raw_token,
    )


@router.delete("/{key_id}", status_code=status.HTTP_204_NO_CONTENT)
async def revoke_api_key(
    key_id: str,
    db: DbSession,
    auth: CurrentAuth,
):
    """Revoke an API key. Returns 404 if owned by another tenant."""
    stmt = select(ApiKey).where(ApiKey.id == key_id, ApiKey.tenant_id == auth.tenant_id)
    result = await db.execute(stmt)
    target = result.scalar_one_or_none()
    if not target:
        raise HTTPException(status_code=404, detail="API key not found")

    target.revoked = True
    await db.commit()

    await record_audit(
        db=db,
        tenant_id=auth.tenant_id,
        actor=auth.email,
        action="api_key.revoke",
        resource=f"api_key:{key_id}",
        result="SUCCESS",
        metadata={"key_id": key_id},
    )
