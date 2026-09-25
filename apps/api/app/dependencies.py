"""
FlowMesh FastAPI Shared Dependencies

Encapsulates authentication, active tenant scoping, and declarative RBAC enforcement.
"""

from typing import Annotated, Optional
from datetime import datetime, timezone
from fastapi import Depends, HTTPException, Header, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import jwt

from app.config import settings
from app.database import get_db, AsyncSessionLocal
from app.services.auth_service import decode_access_token, verify_secret
from flowmesh_auth.rbac import is_allowed

security = HTTPBearer(auto_error=False)


class AuthContext:
    def __init__(self, user_id: str, email: str, tenant_id: str, role: str) -> None:
        self.user_id = user_id
        self.email = email
        self.tenant_id = tenant_id
        self.role = role


def enforce_rbac(auth: AuthContext, resource: str, action: str) -> None:
    """Enforces the RBAC policy matrix before endpoint execution."""
    if not is_allowed(auth.role, resource, action):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"RBAC Forbidden: Role '{auth.role}' cannot perform '{action}' on resource '{resource}'",
        )


async def get_auth_context(
    credentials: Annotated[Optional[HTTPAuthorizationCredentials], Depends(security)],
    x_tenant_id: Annotated[Optional[str], Header(alias="X-Tenant-ID")] = None,
    x_api_key: Annotated[Optional[str], Header(alias="X-API-Key")] = None,
) -> AuthContext:
    """Extracts authenticated user context, active tenant, and assigned role."""
    raw_api_key = x_api_key or (credentials.credentials if credentials and credentials.credentials.startswith("flm_") else None)

    if raw_api_key:
        try:
            from app.models.tenant import ApiKey
            async with AsyncSessionLocal() as session:
                prefix = raw_api_key[:12]
                stmt = select(ApiKey).where(ApiKey.key_prefix == prefix, ApiKey.revoked == False)
                res = await session.execute(stmt)
                key_rec = res.scalar_one_or_none()
                if key_rec and verify_secret(raw_api_key, key_rec.hashed_key):
                    if key_rec.expires_at and key_rec.expires_at < datetime.now(timezone.utc):
                        raise HTTPException(
                            status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="API key has expired",
                        )
                    if x_tenant_id and x_tenant_id != key_rec.tenant_id:
                        raise HTTPException(
                            status_code=status.HTTP_403_FORBIDDEN,
                            detail=f"Cross-tenant access forbidden: X-Tenant-ID '{x_tenant_id}' does not match API key tenant '{key_rec.tenant_id}'",
                        )
                    return AuthContext(
                        user_id=f"api_key_{key_rec.id}",
                        email=f"agent-{key_rec.name}@{key_rec.tenant_id}.key",
                        tenant_id=key_rec.tenant_id,
                        role=key_rec.role,
                    )
        except HTTPException:
            raise
        except Exception:
            pass
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or revoked API key",
            headers={"WWW-Authenticate": "ApiKey"},
        )

    if credentials and not credentials.credentials.startswith("flm_"):
        try:
            payload = decode_access_token(credentials.credentials)
            token_tenant = payload.get("tenant_id", "tenant_acme")
            if x_tenant_id and x_tenant_id != token_tenant:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Cross-tenant access forbidden: X-Tenant-ID '{x_tenant_id}' does not match session credentials '{token_tenant}'",
                )
            return AuthContext(
                user_id=payload.get("sub", "user_anon"),
                email=payload.get("email", "user@corp.local"),
                tenant_id=token_tenant,
                role=payload.get("role", "developer"),
            )
        except jwt.PyJWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired authentication credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        except HTTPException:
            raise
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired authentication credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )

    from app.config import settings as _settings
    if _settings.environment in ("development", "test"):
        return AuthContext(
            user_id="user_dev_01",
            email="alex.dev@acme.corp",
            tenant_id=x_tenant_id or "tenant_acme",
            role="owner",
        )

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Authentication required. Provide a valid Bearer token or X-API-Key.",
        headers={"WWW-Authenticate": "Bearer"},
    )


def require_permission(resource: str, action: str):
    """Dependency factory that enforces the RBAC policy matrix before endpoint execution."""
    async def permission_checker(
        auth: Annotated[AuthContext, Depends(get_auth_context)]
    ) -> AuthContext:
        enforce_rbac(auth, resource, action)
        return auth

    return permission_checker


DbSession = Annotated[AsyncSession, Depends(get_db)]
CurrentAuth = Annotated[AuthContext, Depends(get_auth_context)]
