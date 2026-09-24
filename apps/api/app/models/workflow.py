"""
FlowMesh Workflow Database Models
Implements immutable workflow versioning (ADR-0004).
"""

from datetime import datetime, timezone
from typing import Optional, List, TYPE_CHECKING
from sqlalchemy import (
    String,
    Integer,
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    JSON,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base

if TYPE_CHECKING:
    from app.models.run import RunRecord


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class WorkflowRecord(Base):
    """
    Workflow record with immutable version tracking.
    Editing a workflow increments version (ADR-0004).
    """
    __tablename__ = "workflows"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(String(64), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, default="")
    status: Mapped[str] = mapped_column(String(32), default="active", nullable=False)
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    trigger_type: Mapped[str] = mapped_column(String(64), nullable=False)
    definition_json: Mapped[dict] = mapped_column(JSON, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)

    runs: Mapped[List["RunRecord"]] = relationship("RunRecord", back_populates="workflow", cascade="all, delete-orphan")
    versions: Mapped[List["WorkflowVersionRecord"]] = relationship(
        "WorkflowVersionRecord",
        back_populates="workflow",
        cascade="all, delete-orphan",
        order_by="desc(WorkflowVersionRecord.version)",
    )

    __table_args__ = (
        Index("ix_workflow_tenant_status", "tenant_id", "status"),
        Index("ix_workflow_tenant_trigger", "tenant_id", "trigger_type"),
    )


class WorkflowVersionRecord(Base):
    """
    Immutable snapshot of a deployed workflow version (ADR-0004).
    In-flight runs pin to this version. Rollbacks restore active definition.
    """
    __tablename__ = "workflow_versions"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(String(64), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    workflow_id: Mapped[str] = mapped_column(String(64), ForeignKey("workflows.id", ondelete="CASCADE"), nullable=False, index=True)
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    definition_json: Mapped[dict] = mapped_column(JSON, nullable=False)
    changelog: Mapped[str] = mapped_column(Text, default="")
    deployed_by: Mapped[str] = mapped_column(String(255), default="")
    deployed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    workflow: Mapped["WorkflowRecord"] = relationship("WorkflowRecord", back_populates="versions")

    __table_args__ = (
        Index("ix_wf_version_tenant_wf", "tenant_id", "workflow_id", "version", unique=True),
        Index("ix_wf_version_active", "tenant_id", "workflow_id", "is_active"),
    )
