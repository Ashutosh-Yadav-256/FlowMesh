"""
FlowMesh Immutable Audit Service

Records every mutating or critical operation into the append-only audit_events table.
"""

import uuid
from typing import Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.tenant import AuditEvent


async def record_audit(
    db: AsyncSession,
    tenant_id: str,
    actor: str,
    action: str,
    resource: str,
    result: str,
    metadata: Optional[Dict[str, Any]] = None,
) -> AuditEvent:
    """Appends an immutable audit row."""
    event = AuditEvent(
        id=f"aud_{uuid.uuid4().hex[:12]}",
        tenant_id=tenant_id,
        actor=actor,
        action=action,
        resource=resource,
        result=result,
        metadata_json=metadata or {},
    )
    db.add(event)
    await self_safe_commit(db)
    return event


async def self_safe_commit(db: AsyncSession) -> None:
    try:
        await db.commit()
    except Exception:
        await db.rollback()
        raise
