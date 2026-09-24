"""
FlowMesh FastAPI Shared Dependencies

Encapsulates authentication, active tenant scoping, and declarative RBAC enforcement.
"""

from typing import Annotated, Optional
from fastapi import Depends, HTTPException, Header, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
import jwt

from app.config import settings
from app.database import get_db
from app.services.auth_service import decode_access_token
from flowmesh_auth.rbac import is_allowed

security = HTTPBearer(auto_error=False)


class AuthContext:
    def __init__(self, user_id: str, email: str, tenant_id: str, role: str) -> None:
        self.user_id = user_id
        self.email = email
        self.tenant_id = tenant_id
        self.role = role


async def get_auth_context(
    credentials: Annotated[Optional[HTTPAuthorizationCredentials], Depends(security)],
    x_tenant_id: Annotated[Optional[str], Header(alias="X-Tenant-ID")] = None,
) -> AuthContext:
    """Extracts authenticated user context, active tenant, and assigned role."""
    if credentials:
        try:
            payload = decode_access_token(credentials.credentials)
            tenant_id = x_tenant_id or payload.get("tenant_id", "tenant_acme")
            return AuthContext(
                user_id=payload.get("sub", "user_anon"),
                email=payload.get("email", "user@corp.local"),
                tenant_id=tenant_id,
                role=payload.get("role", "developer"),
            )
        except (jwt.PyJWTError, ValueError):
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
        detail="Authentication required. Provide a valid Bearer token.",
        headers={"WWW-Authenticate": "Bearer"},
    )


def require_permission(resource: str, action: str):
    """Dependency factory that enforces the RBAC policy matrix before endpoint execution."""
    async def permission_checker(
        auth: Annotated[AuthContext, Depends(get_auth_context)]
    ) -> AuthContext:
        if not is_allowed(auth.role, resource, action):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"RBAC Forbidden: Role '{auth.role}' cannot perform '{action}' on resource '{resource}'",
            )
        return auth

    return permission_checker


DbSession = Annotated[AsyncSession, Depends(get_db)]
CurrentAuth = Annotated[AuthContext, Depends(get_auth_context)]
