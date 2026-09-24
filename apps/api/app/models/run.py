"""
FlowMesh Run and Step Database Models
Tracks immutable execution state machine progress and step input/output snapshots.
"""

from datetime import datetime, timezone
from typing import Optional, List
from sqlalchemy import (
    String,
    Integer,
    Float,
    DateTime,
    ForeignKey,
    Index,
    JSON,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base
from app.models.workflow import WorkflowRecord


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class RunRecord(Base):
    """
    Execution run instance pinned to a specific immutable workflow version.
    """
    __tablename__ = "runs"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(String(64), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    workflow_id: Mapped[str] = mapped_column(String(64), ForeignKey("workflows.id", ondelete="CASCADE"), nullable=False, index=True)
    workflow_version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="PENDING", nullable=False)
    duration_seconds: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    trigger_source: Mapped[str] = mapped_column(String(255), nullable=False)
    trace_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    idempotency_key: Mapped[Optional[str]] = mapped_column(String(128), nullable=True, index=True)
    input_payload: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    output_payload: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    finished_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    workflow: Mapped["WorkflowRecord"] = relationship("WorkflowRecord", back_populates="runs")
    steps: Mapped[List["RunStepRecord"]] = relationship(
        "RunStepRecord",
        back_populates="run",
        cascade="all, delete-orphan",
        order_by="RunStepRecord.started_at",
    )

    __table_args__ = (
        Index("ix_run_tenant_started", "tenant_id", "started_at"),
        Index("ix_run_tenant_status", "tenant_id", "status"),
        Index("ix_run_tenant_idempotency", "tenant_id", "idempotency_key"),
    )


class RunStepRecord(Base):
    """
    Step execution snapshot for a single node execution in a workflow DAG.
    """
    __tablename__ = "run_steps"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    run_id: Mapped[str] = mapped_column(String(64), ForeignKey("runs.id", ondelete="CASCADE"), nullable=False, index=True)
    tenant_id: Mapped[str] = mapped_column(String(64), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    node_id: Mapped[str] = mapped_column(String(64), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    node_type: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="PENDING", nullable=False)
    attempt: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    duration_ms: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    finished_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    input_snapshot: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    output_snapshot: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    run: Mapped["RunRecord"] = relationship("RunRecord", back_populates="steps")

    __table_args__ = (
        Index("ix_step_run_node", "run_id", "node_id"),
        Index("ix_step_tenant_run", "tenant_id", "run_id"),
    )
