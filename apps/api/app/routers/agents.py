"""
FlowMesh Edge Agent Management API Router

Features:
- Multi-tenant edge agent lifecycle management backed by PostgreSQL/SQLite.
- Zero-touch enrollment token generation and registration handshake.
- Periodic telemetry heartbeat ingestion (CPU, Memory, queue depth, connector health).
- Dynamic staleness detection: agents with no heartbeat in > 15s are automatically marked OFFLINE.
- Cryptographically signed command dispatching using Control Plane Ed25519 key.
- Outbound command polling and execution result recording.
"""

import uuid
import secrets
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException, status, Header
from pydantic import BaseModel, Field

from app.dependencies import DbSession, CurrentAuth
from flowmesh_auth.rbac import is_allowed
from flowmesh_auth.signing import get_control_plane_signer
from app.repositories.tenant_scoped import (
    AgentRepository,
    AgentCommandRepository,
)
from app.services.audit_service import record_audit

router = APIRouter(prefix="/api/v1/agents", tags=["Edge Agents"])


def enforce_rbac(auth: CurrentAuth, resource: str, action: str) -> None:
    if not is_allowed(auth.role, resource, action):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"RBAC Forbidden: Role '{auth.role}' cannot perform '{action}' on resource '{resource}'",
        )


class AgentConnectorHealth(BaseModel):
    name: str
    status: str
    type: str


class AgentDetail(BaseModel):
    id: str
    name: str
    version: str
    status: str
    last_heartbeat_seconds_ago: int
    cpu_percent: float
    memory_percent: float
    queue_depth: int
    cert_valid: bool = True
    cert_expires_days: int = 90
    policy_status: str = "enforced"
    connectors: List[AgentConnectorHealth] = Field(default_factory=list)


class EnrollmentTokenResponse(BaseModel):
    enrollment_token: str
    expires_in_seconds: int = 3600
    install_command: str


class AgentEnrollRequest(BaseModel):
    enrollment_token: str
    name: str
    version: str = "v0.5.0"
    public_key: Optional[str] = None


class AgentEnrollResponse(BaseModel):
    agent_id: str
    tenant_id: str
    control_plane_public_key: str
    status: str


class AgentHeartbeatRequest(BaseModel):
    cpu_percent: float = Field(..., ge=0.0, le=100.0)
    memory_percent: float = Field(..., ge=0.0, le=100.0)
    queue_depth: int = Field(default=0, ge=0)
    connectors: List[AgentConnectorHealth] = Field(default_factory=list)


class DispatchCommandRequest(BaseModel):
    connector: str
    connection_id: str
    operation: str
    resource: Optional[str] = None
    limit: Optional[int] = None
    payload: Dict[str, Any] = Field(default_factory=dict)


class DispatchedCommandResponse(BaseModel):
    command_id: str
    agent_id: str
    status: str
    signature: str


class CommandResultRequest(BaseModel):
    status: str
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    duration_ms: float = 0.0



@router.post("/enrollment-token", response_model=EnrollmentTokenResponse)
async def generate_enrollment_token(
    db: DbSession,
    auth: CurrentAuth,
) -> EnrollmentTokenResponse:
    """Generates a single-use token for registering a new customer Edge Agent."""
    enforce_rbac(auth, "agent", "create")
    agent_repo = AgentRepository(db, auth.tenant_id)

    token = f"flm_enroll_{secrets.token_urlsafe(24)}"
    temp_agent_id = f"agent-{uuid.uuid4().hex[:8]}"

    await agent_repo.create_agent(
        agent_id=temp_agent_id,
        name=f"Pending Agent ({temp_agent_id})",
        version="v0.5.0",
        enrollment_token=token,
    )

    await record_audit(
        db=db,
        tenant_id=auth.tenant_id,
        actor=auth.email,
        action="agent.generate_enrollment_token",
        resource=f"agent:{temp_agent_id}",
        result="success",
        metadata={"token_prefix": token[:14]},
    )

    return EnrollmentTokenResponse(
        enrollment_token=token,
        expires_in_seconds=3600,
        install_command=f"curl -fsSL https://install.flowmesh.dev | sh -s -- --token {token}",
    )


@router.post("/enroll", response_model=AgentEnrollResponse)
async def enroll_agent(
    payload: AgentEnrollRequest,
    db: DbSession,
) -> AgentEnrollResponse:
    """
    Public/agent enrollment endpoint called by Edge Agent on zero-touch boot.
    Validates enrollment token, activates agent, and registers Ed25519 keys.
    """
    from sqlalchemy import select
    from app.models.agent import AgentRecord

    stmt = select(AgentRecord).where(AgentRecord.enrollment_token == payload.enrollment_token)
    res = await db.execute(stmt)
    agent = res.scalar_one_or_none()

    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invalid or expired enrollment token",
        )

    agent_repo = AgentRepository(db, agent.tenant_id)
    enrolled = await agent_repo.enroll_agent(
        token=payload.enrollment_token,
        name=payload.name,
        version=payload.version,
        public_key=payload.public_key,
    )

    if not enrolled:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Failed to enroll agent")

    signer = get_control_plane_signer()

    return AgentEnrollResponse(
        agent_id=enrolled.id,
        tenant_id=enrolled.tenant_id,
        control_plane_public_key=signer.public_key_b64,
        status=enrolled.status,
    )



def _format_agent_detail(agent) -> AgentDetail:
    now = datetime.now(timezone.utc)
    seconds_ago = 999999
    if agent.last_heartbeat_at:
        seconds_ago = int((now - agent.last_heartbeat_at.replace(tzinfo=timezone.utc)).total_seconds())

    effective_status = "offline" if seconds_ago > 15 else agent.status.lower()

    connectors = [
        AgentConnectorHealth(name=c.get("name", "Unknown"), status=c.get("status", "unknown"), type=c.get("type", "unknown"))
        for c in (agent.connectors or [])
    ]

    return AgentDetail(
        id=agent.id,
        name=agent.name,
        version=agent.version,
        status=effective_status,
        last_heartbeat_seconds_ago=seconds_ago,
        cpu_percent=agent.cpu_percent,
        memory_percent=agent.memory_percent,
        queue_depth=agent.queue_depth,
        cert_valid=True,
        cert_expires_days=85,
        policy_status=agent.policy_status,
        connectors=connectors,
    )


_DEFAULT_AGENTS: List[AgentDetail] = [
    AgentDetail(
        id="agent-prod-01",
        name="production-01",
        version="v0.4.2",
        status="healthy",
        last_heartbeat_seconds_ago=3,
        cpu_percent=12.4,
        memory_percent=31.2,
        queue_depth=14,
        cert_valid=True,
        cert_expires_days=82,
        policy_status="enforced",
        connectors=[
            AgentConnectorHealth(name="Orders PostgreSQL", status="healthy", type="postgres"),
            AgentConnectorHealth(name="Enterprise SAP ERP", status="healthy", type="sap"),
            AgentConnectorHealth(name="Internal Warehouse API", status="healthy", type="rest"),
            AgentConnectorHealth(name="SFTP Bank Gateway", status="healthy", type="sftp"),
        ],
    ),
    AgentDetail(
        id="agent-wh-01",
        name="warehouse-01",
        version="v0.4.2",
        status="healthy",
        last_heartbeat_seconds_ago=4,
        cpu_percent=8.1,
        memory_percent=22.5,
        queue_depth=2,
        cert_valid=True,
        cert_expires_days=82,
        policy_status="enforced",
        connectors=[
            AgentConnectorHealth(name="Warehouse Inventory DB", status="healthy", type="postgres"),
            AgentConnectorHealth(name="Barcode Scanner Ingress", status="healthy", type="rest"),
        ],
    ),
    AgentDetail(
        id="agent-stg-01",
        name="staging-01",
        version="v0.4.2",
        status="offline",
        last_heartbeat_seconds_ago=1420,
        cpu_percent=0.0,
        memory_percent=0.0,
        queue_depth=0,
        cert_valid=True,
        cert_expires_days=45,
        policy_status="offline",
        connectors=[
            AgentConnectorHealth(name="Staging DB", status="offline", type="postgres"),
        ],
    ),
]


@router.get("", response_model=List[AgentDetail])
async def list_agents(
    db: DbSession,
    auth: CurrentAuth,
) -> List[AgentDetail]:
    """List all registered Edge Agents for the active tenant."""
    enforce_rbac(auth, "agent", "read")
    agent_repo = AgentRepository(db, auth.tenant_id)
    agents = await agent_repo.list_all()
    from app.config import settings as _cfg
    if len(agents) == 0 and _cfg.seed_demo_data and _cfg.environment == "development" and auth.tenant_id == "tenant_acme":
        return _DEFAULT_AGENTS
    return [_format_agent_detail(a) for a in agents]


@router.get("/{agent_id}", response_model=AgentDetail)
async def get_agent(
    agent_id: str,
    db: DbSession,
    auth: CurrentAuth,
) -> AgentDetail:
    """Get detailed telemetry and connector status for an Edge Agent."""
    enforce_rbac(auth, "agent", "read")
    agent_repo = AgentRepository(db, auth.tenant_id)
    agent = await agent_repo.get_by_id(agent_id)
    if agent:
        return _format_agent_detail(agent)
    from app.config import settings as _cfg
    if _cfg.seed_demo_data and _cfg.environment == "development" and auth.tenant_id == "tenant_acme":
        default_match = next((a for a in _DEFAULT_AGENTS if a.id == agent_id), None)
        if default_match:
            return default_match
    raise HTTPException(status_code=404, detail="Agent not found")


@router.post("/{agent_id}/heartbeat")
async def receive_heartbeat(
    agent_id: str,
    payload: AgentHeartbeatRequest,
    db: DbSession,
    x_tenant_id: Optional[str] = Header(None, alias="X-Tenant-ID"),
) -> Dict[str, Any]:
    """Receives periodic outbound telemetry heartbeat from an Edge Agent."""
    from sqlalchemy import select
    from app.models.agent import AgentRecord

    stmt = select(AgentRecord).where(AgentRecord.id == agent_id)
    if x_tenant_id:
        stmt = stmt.where(AgentRecord.tenant_id == x_tenant_id)
    res = await db.execute(stmt)
    agent = res.scalar_one_or_none()

    if not agent:
        raise HTTPException(status_code=404, detail=f"Agent '{agent_id}' not found")

    agent_repo = AgentRepository(db, agent.tenant_id)
    updated = await agent_repo.update_heartbeat(
        agent_id=agent.id,
        cpu_percent=payload.cpu_percent,
        memory_percent=payload.memory_percent,
        queue_depth=payload.queue_depth,
        connectors=[c.model_dump() for c in payload.connectors],
    )

    return {
        "status": "acknowledged",
        "agent_id": agent.id,
        "timestamp": updated.last_heartbeat_at.isoformat() if updated and updated.last_heartbeat_at else None,
    }



@router.post("/{agent_id}/commands", response_model=DispatchedCommandResponse)
async def dispatch_command(
    agent_id: str,
    req: DispatchCommandRequest,
    db: DbSession,
    auth: CurrentAuth,
) -> DispatchedCommandResponse:
    """Dispatches a cryptographically signed structural command to an Edge Agent."""
    enforce_rbac(auth, "agent", "execute")
    agent_repo = AgentRepository(db, auth.tenant_id)
    cmd_repo = AgentCommandRepository(db, auth.tenant_id)

    agent = await agent_repo.get_by_id(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail=f"Agent '{agent_id}' not found")

    cmd_id = f"cmd-{uuid.uuid4().hex[:12]}"
    command_dict = {
        "id": cmd_id,
        "type": "connector.execute",
        "connector": req.connector,
        "connection_id": req.connection_id,
        "operation": req.operation,
        "resource": req.resource or "",
        "limit": req.limit or 0,
        "payload": req.payload,
    }

    signer = get_control_plane_signer()
    signature_b64, _ = signer.sign_payload(command_dict)

    created_cmd = await cmd_repo.create_command(
        command_id=cmd_id,
        agent_id=agent.id,
        connector=req.connector,
        connection_id=req.connection_id,
        operation=req.operation,
        resource=req.resource,
        limit=req.limit,
        payload=req.payload,
        signature=signature_b64,
    )

    return DispatchedCommandResponse(
        command_id=created_cmd.id,
        agent_id=agent.id,
        status=created_cmd.status,
        signature=signature_b64,
    )


@router.get("/{agent_id}/commands/poll")
async def poll_commands(
    agent_id: str,
    db: DbSession,
    x_tenant_id: Optional[str] = Header(None, alias="X-Tenant-ID"),
) -> List[Dict[str, Any]]:
    """Outbound long-poll endpoint for Edge Agent to receive pending signed commands."""
    from sqlalchemy import select
    from app.models.agent import AgentRecord

    stmt = select(AgentRecord).where(AgentRecord.id == agent_id)
    if x_tenant_id:
        stmt = stmt.where(AgentRecord.tenant_id == x_tenant_id)
    res = await db.execute(stmt)
    agent = res.scalar_one_or_none()

    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    cmd_repo = AgentCommandRepository(db, agent.tenant_id)
    pending = await cmd_repo.get_pending_commands(agent_id=agent.id, limit=10)

    results = []
    for cmd in pending:
        await cmd_repo.mark_dispatched(cmd.id)
        results.append({
            "command": {
                "id": cmd.id,
                "type": cmd.type,
                "connector": cmd.connector,
                "connection_id": cmd.connection_id,
                "operation": cmd.operation,
                "resource": cmd.resource or "",
                "limit": cmd.limit or 0,
                "payload": cmd.payload or {},
            },
            "signature": cmd.signature,
        })

    return results


@router.post("/{agent_id}/commands/{command_id}/result")
async def record_command_result(
    agent_id: str,
    command_id: str,
    payload: CommandResultRequest,
    db: DbSession,
    x_tenant_id: Optional[str] = Header(None, alias="X-Tenant-ID"),
) -> Dict[str, Any]:
    """Records the execution result sent back by the Edge Agent."""
    from sqlalchemy import select
    from app.models.agent import AgentRecord

    stmt = select(AgentRecord).where(AgentRecord.id == agent_id)
    if x_tenant_id:
        stmt = stmt.where(AgentRecord.tenant_id == x_tenant_id)
    res = await db.execute(stmt)
    agent = res.scalar_one_or_none()

    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    cmd_repo = AgentCommandRepository(db, agent.tenant_id)
    updated = await cmd_repo.record_result(
        command_id=command_id,
        status=payload.status,
        result=payload.result,
        error=payload.error,
    )

    if not updated:
        raise HTTPException(status_code=404, detail="Command not found")

    return {
        "status": "recorded",
        "command_id": command_id,
        "execution_status": updated.status,
    }
