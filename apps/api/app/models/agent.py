"""
FlowMesh Edge Agent Models

Represents customer Edge Agents running inside private networks and
structured, signed commands dispatched to them by the Control Plane.
"""

from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
from sqlalchemy import (
    Column,
    String,
    Float,
    Integer,
    DateTime,
    ForeignKey,
    Index,
    JSON,
    Text,
)
from sqlalchemy.orm import relationship

from app.database import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class AgentRecord(Base):
    __tablename__ = "agents"

    id = Column(String(64), primary_key=True)
    tenant_id = Column(String(64), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(128), nullable=False)
    version = Column(String(32), nullable=False, default="v0.4.2")
    status = Column(String(32), nullable=False, default="OFFLINE")
    public_key = Column(String(256), nullable=True)
    cpu_percent = Column(Float, nullable=False, default=0.0)
    memory_percent = Column(Float, nullable=False, default=0.0)
    queue_depth = Column(Integer, nullable=False, default=0)
    policy_status = Column(String(32), nullable=False, default="enforced")
    connectors = Column(JSON, nullable=False, default=list)
    last_heartbeat_at = Column(DateTime(timezone=True), nullable=True)
    registered_at = Column(DateTime(timezone=True), nullable=False, default=utcnow)
    enrollment_token = Column(String(128), nullable=True, unique=True, index=True)

    commands = relationship("AgentCommandRecord", back_populates="agent", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_agents_tenant_status", "tenant_id", "status"),
        Index("ix_agents_tenant_name", "tenant_id", "name"),
    )


class AgentCommandRecord(Base):
    __tablename__ = "agent_commands"

    id = Column(String(64), primary_key=True)
    tenant_id = Column(String(64), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    agent_id = Column(String(64), ForeignKey("agents.id", ondelete="CASCADE"), nullable=False, index=True)
    type = Column(String(64), nullable=False, default="connector.execute")
    connector = Column(String(64), nullable=False)
    connection_id = Column(String(64), nullable=False)
    operation = Column(String(64), nullable=False)
    resource = Column(String(256), nullable=True)
    limit = Column(Integer, nullable=True)
    payload = Column(JSON, nullable=False, default=dict)
    signature = Column(Text, nullable=True)
    status = Column(String(32), nullable=False, default="QUEUED")
    result = Column(JSON, nullable=True)
    error = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=utcnow)
    dispatched_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)

    agent = relationship("AgentRecord", back_populates="commands")

    __table_args__ = (
        Index("ix_agent_commands_tenant_agent", "tenant_id", "agent_id", "status"),
        Index("ix_agent_commands_created", "created_at"),
    )
