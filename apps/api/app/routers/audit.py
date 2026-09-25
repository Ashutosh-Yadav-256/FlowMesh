from typing import List, Dict, Any, Annotated
from fastapi import APIRouter, Depends, Response
from pydantic import BaseModel

from app.dependencies import DbSession, CurrentAuth, enforce_rbac
from app.repositories.tenant_scoped import AuditRepository
from app.pagination import PaginationParams, paginate_items

router = APIRouter(prefix="/api/v1/audit", tags=["Audit Trail"])


class AuditRecord(BaseModel):
    id: str
    timestamp: str
    actor: str
    action: str
    resource: str
    result: str
    tenant_id: str
    metadata: Dict[str, Any]


@router.get("", response_model=List[AuditRecord])
async def list_audit_events(
    db: DbSession,
    auth: CurrentAuth,
    pagination: Annotated[PaginationParams, Depends()],
    response: Response,
) -> List[AuditRecord]:
    """Retrieve immutable audit events log scoped to the active tenant."""
    enforce_rbac(auth, "audit", "read")
    audit_repo = AuditRepository(db, auth.tenant_id)
    total = await audit_repo.count()
    events = await audit_repo.list_all(skip=pagination.offset, limit=pagination.limit)

    items = [
        AuditRecord(
            id=e.id,
            timestamp=e.timestamp.isoformat() if e.timestamp else "",
            actor=e.actor,
            action=e.action,
            resource=e.resource,
            result=e.result,
            tenant_id=e.tenant_id,
            metadata=e.metadata_json or {},
        )
        for e in events
    ]
    return paginate_items(items, total=total, params=pagination, response=response)
