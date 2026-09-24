"""
FlowMesh Incident Management Database Model
Tracks automatic and operator incidents, affected workflows, root causes, and resolution timelines.
"""

from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from sqlalchemy import String, DateTime, ForeignKey, Index, JSON, Text
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class IncidentRecord(Base):
    """
    Persisted operational incident triggered by circuit breaker trips or critical failure thresholds.
    """
    __tablename__ = "incidents"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(String(64), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    severity: Mapped[str] = mapped_column(String(32), default="HIGH", nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="OPEN", nullable=False)
    connection_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True, index=True)
    affected_workflows: Mapped[List[str]] = mapped_column(JSON, default=list, nullable=False)
    root_cause: Mapped[str] = mapped_column(Text, nullable=False)
    timeline: Mapped[List[Dict[str, str]]] = mapped_column(JSON, default=list, nullable=False)
    opened_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    resolved_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        Index("ix_incident_tenant_status", "tenant_id", "status"),
        Index("ix_incident_tenant_conn", "tenant_id", "connection_id"),
        Index("ix_incident_tenant_opened", "tenant_id", "opened_at"),
    )
