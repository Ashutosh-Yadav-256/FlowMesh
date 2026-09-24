"""
FlowMesh Tenant-Scoped Repository Layer

Enforces strict tenant boundaries at the database query abstraction layer.
Every read, write, and delete query is explicitly filtered by tenant_id.
If an entity exists under Tenant A but is requested by Tenant B, the repository
returns None (causing a clean HTTP 404), ensuring entity existence is NEVER leaked.
"""

from datetime import datetime, timezone
from typing import TypeVar, Generic, Type, Optional, List, Sequence, Any
from sqlalchemy import select, delete, func, update
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.tenant import ConnectionRecord, ConnectionSecret, AuditEvent, ApiKey
from app.models.schema_snapshot import SchemaSnapshot
from app.models.workflow import WorkflowRecord, WorkflowVersionRecord
from app.models.run import RunRecord, RunStepRecord
from app.models.dlq import DeadLetterRecord
from app.models.incident import IncidentRecord
from app.models.agent import AgentRecord, AgentCommandRecord

T = TypeVar("T")


class TenantScopedRepository(Generic[T]):
    """Generic repository enforcing mandatory tenant isolation on all operations."""

    def __init__(self, model: Type[T], db: AsyncSession, tenant_id: str) -> None:
        if not tenant_id:
            raise ValueError("TenantScopedRepository requires an explicit non-empty tenant_id")
        self.model = model
        self.db = db
        self.tenant_id = tenant_id

    async def get_by_id(self, entity_id: str) -> Optional[T]:
        """Fetch an entity by ID strictly within the active tenant scope. Returns None if owned by another tenant."""
        stmt = (
            select(self.model)
            .where(self.model.id == entity_id)  # type: ignore
            .where(self.model.tenant_id == self.tenant_id)  # type: ignore
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def list_all(self, skip: int = 0, limit: int = 100) -> Sequence[T]:
        """List entities strictly belonging to the active tenant."""
        order_col = getattr(self.model, "created_at", getattr(self.model, "timestamp", getattr(self.model, "id", None)))
        stmt = (
            select(self.model)
            .where(self.model.tenant_id == self.tenant_id)  # type: ignore
        )
        if order_col is not None:
            stmt = stmt.order_by(order_col.desc())
        stmt = stmt.offset(skip).limit(limit)
        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def count(self) -> int:
        """Count total entities for this tenant."""
        stmt = (
            select(func.count())
            .select_from(self.model)
            .where(self.model.tenant_id == self.tenant_id)  # type: ignore
        )
        result = await self.db.execute(stmt)
        return result.scalar_one() or 0

    async def create(self, entity: T) -> T:
        """Persists a new entity, strictly enforcing tenant_id assignment."""
        setattr(entity, "tenant_id", self.tenant_id)
        self.db.add(entity)
        await self.db.commit()
        await self.db.refresh(entity)
        return entity

    async def delete(self, entity_id: str) -> bool:
        """Deletes an entity only if it belongs to the active tenant."""
        stmt = (
            delete(self.model)
            .where(self.model.id == entity_id)  # type: ignore
            .where(self.model.tenant_id == self.tenant_id)  # type: ignore
        )
        result = await self.db.execute(stmt)
        await self.db.commit()
        return result.rowcount > 0


class ConnectionRepository(TenantScopedRepository[ConnectionRecord]):
    def __init__(self, db: AsyncSession, tenant_id: str) -> None:
        super().__init__(ConnectionRecord, db, tenant_id)

    async def get_by_type(self, conn_type: str) -> Sequence[ConnectionRecord]:
        stmt = (
            select(ConnectionRecord)
            .where(ConnectionRecord.tenant_id == self.tenant_id)
            .where(ConnectionRecord.type == conn_type)
        )
        result = await self.db.execute(stmt)
        return result.scalars().all()


class AuditRepository(TenantScopedRepository[AuditEvent]):
    def __init__(self, db: AsyncSession, tenant_id: str) -> None:
        super().__init__(AuditEvent, db, tenant_id)

    async def record(self, actor: str, action: str, resource: str, result: str, metadata: dict) -> AuditEvent:
        """Appends an immutable audit event for this tenant."""
        import uuid
        event = AuditEvent(
            id=f"aud_{uuid.uuid4().hex[:12]}",
            tenant_id=self.tenant_id,
            actor=actor,
            action=action,
            resource=resource,
            result=result,
            metadata_json=metadata,
        )
        self.db.add(event)
        await self.db.commit()
        await self.db.refresh(event)
        return event


class ConnectionSecretRepository(TenantScopedRepository[ConnectionSecret]):
    def __init__(self, db: AsyncSession, tenant_id: str) -> None:
        super().__init__(ConnectionSecret, db, tenant_id)

    async def get_latest_for_connection(self, connection_id: str) -> Optional[ConnectionSecret]:
        """Fetch the highest-version secret for a connection belonging to this tenant."""
        stmt = (
            select(ConnectionSecret)
            .where(ConnectionSecret.tenant_id == self.tenant_id)
            .where(ConnectionSecret.connection_id == connection_id)
            .order_by(ConnectionSecret.version.desc())
            .limit(1)
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_version(self, connection_id: str, version: int) -> Optional[ConnectionSecret]:
        """Fetch a specific secret version for a connection belonging to this tenant."""
        stmt = (
            select(ConnectionSecret)
            .where(ConnectionSecret.tenant_id == self.tenant_id)
            .where(ConnectionSecret.connection_id == connection_id)
            .where(ConnectionSecret.version == version)
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def purge_previous_versions(self, connection_id: str, keep_version: int) -> int:
        """Purges older ciphertext for forward secrecy upon credential rotation."""
        stmt = (
            delete(ConnectionSecret)
            .where(ConnectionSecret.tenant_id == self.tenant_id)
            .where(ConnectionSecret.connection_id == connection_id)
            .where(ConnectionSecret.version < keep_version)
        )
        result = await self.db.execute(stmt)
        await self.db.commit()
        return result.rowcount


class WorkflowVersionRepository(TenantScopedRepository[WorkflowVersionRecord]):
    def __init__(self, db: AsyncSession, tenant_id: str) -> None:
        super().__init__(WorkflowVersionRecord, db, tenant_id)

    async def list_for_workflow(self, workflow_id: str) -> Sequence[WorkflowVersionRecord]:
        """Lists all immutable versions for a workflow, newest first."""
        stmt = (
            select(WorkflowVersionRecord)
            .where(WorkflowVersionRecord.tenant_id == self.tenant_id)
            .where(WorkflowVersionRecord.workflow_id == workflow_id)
            .order_by(WorkflowVersionRecord.version.desc())
        )
        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def get_by_version(self, workflow_id: str, version: int) -> Optional[WorkflowVersionRecord]:
        """Fetch a specific immutable version record for a workflow."""
        stmt = (
            select(WorkflowVersionRecord)
            .where(WorkflowVersionRecord.tenant_id == self.tenant_id)
            .where(WorkflowVersionRecord.workflow_id == workflow_id)
            .where(WorkflowVersionRecord.version == version)
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_active_version(self, workflow_id: str) -> Optional[WorkflowVersionRecord]:
        """Fetch the currently active deployed version record for a workflow."""
        stmt = (
            select(WorkflowVersionRecord)
            .where(WorkflowVersionRecord.tenant_id == self.tenant_id)
            .where(WorkflowVersionRecord.workflow_id == workflow_id)
            .where(WorkflowVersionRecord.is_active.is_(True))
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()


class WorkflowRepository(TenantScopedRepository[WorkflowRecord]):
    def __init__(self, db: AsyncSession, tenant_id: str) -> None:
        super().__init__(WorkflowRecord, db, tenant_id)

    async def get_by_trigger_path(self, path: str) -> Optional[WorkflowRecord]:
        """Finds active workflow triggered by a webhook path."""
        normalized = "/" + path.strip("/")
        stmt = (
            select(WorkflowRecord)
            .where(WorkflowRecord.tenant_id == self.tenant_id)
            .where(WorkflowRecord.status == "active")
        )
        result = await self.db.execute(stmt)
        workflows = result.scalars().all()
        for wf in workflows:
            trigger = wf.definition_json.get("trigger", {})
            t_type = trigger.get("type", "")
            t_path = trigger.get("config", {}).get("path") or trigger.get("path")
            if t_type == "webhook" and (t_path == normalized or t_path == path or not t_path):
                return wf
        return None

    async def get_with_versions(self, workflow_id: str) -> Optional[WorkflowRecord]:
        stmt = (
            select(WorkflowRecord)
            .options(selectinload(WorkflowRecord.versions))
            .where(WorkflowRecord.id == workflow_id)
            .where(WorkflowRecord.tenant_id == self.tenant_id)
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def deploy_version(
        self,
        workflow_id: str,
        definition_json: dict,
        changelog: str,
        deployed_by: str,
    ) -> WorkflowVersionRecord:
        """
        Deploys a new immutable version (N+1) of a workflow (ADR-0004).
        Marks previous versions as inactive and updates the active workflow record.
        """
        import uuid
        wf = await self.get_by_id(workflow_id)
        if not wf:
            raise ValueError(f"Workflow {workflow_id} not found")

        new_version_num = wf.version + 1
        now = datetime.now(timezone.utc)

        deactivate_stmt = (
            update(WorkflowVersionRecord)
            .where(WorkflowVersionRecord.tenant_id == self.tenant_id)
            .where(WorkflowVersionRecord.workflow_id == workflow_id)
            .values(is_active=False)
        )
        await self.db.execute(deactivate_stmt)

        version_record = WorkflowVersionRecord(
            id=f"wfv_{uuid.uuid4().hex[:10]}",
            tenant_id=self.tenant_id,
            workflow_id=workflow_id,
            version=new_version_num,
            definition_json=definition_json,
            changelog=changelog or f"Deployed version {new_version_num}",
            deployed_by=deployed_by,
            deployed_at=now,
            is_active=True,
        )
        self.db.add(version_record)

        wf.version = new_version_num
        wf.definition_json = definition_json
        wf.status = "active"
        wf.updated_at = now

        await self.db.commit()
        await self.db.refresh(version_record)
        await self.db.refresh(wf)
        return version_record

    async def rollback_to_version(
        self,
        workflow_id: str,
        target_version: int,
        deployed_by: str,
    ) -> WorkflowVersionRecord:
        """
        Rolls back active workflow definition to an earlier immutable version (ADR-0004).
        Points current_version pointer back to target version without altering historical run telemetry.
        """
        wf = await self.get_by_id(workflow_id)
        if not wf:
            raise ValueError(f"Workflow {workflow_id} not found")

        target_stmt = (
            select(WorkflowVersionRecord)
            .where(WorkflowVersionRecord.tenant_id == self.tenant_id)
            .where(WorkflowVersionRecord.workflow_id == workflow_id)
            .where(WorkflowVersionRecord.version == target_version)
        )
        res = await self.db.execute(target_stmt)
        target_ver = res.scalar_one_or_none()
        if not target_ver:
            raise ValueError(f"Target version {target_version} does not exist for workflow {workflow_id}")

        now = datetime.now(timezone.utc)

        deactivate_stmt = (
            update(WorkflowVersionRecord)
            .where(WorkflowVersionRecord.tenant_id == self.tenant_id)
            .where(WorkflowVersionRecord.workflow_id == workflow_id)
            .values(is_active=False)
        )
        await self.db.execute(deactivate_stmt)

        target_ver.is_active = True

        wf.version = target_ver.version
        wf.definition_json = target_ver.definition_json
        wf.status = "active"
        wf.updated_at = now

        await self.db.commit()
        await self.db.refresh(target_ver)
        await self.db.refresh(wf)
        return target_ver



class RunRepository(TenantScopedRepository[RunRecord]):
    def __init__(self, db: AsyncSession, tenant_id: str) -> None:
        super().__init__(RunRecord, db, tenant_id)

    async def get_by_id(self, entity_id: str) -> Optional[RunRecord]:
        """Fetch a run including all of its steps strictly within tenant scope."""
        stmt = (
            select(RunRecord)
            .options(selectinload(RunRecord.steps))
            .where(RunRecord.id == entity_id)
            .where(RunRecord.tenant_id == self.tenant_id)
        )
        result = await self.db.execute(stmt)
        run = result.scalar_one_or_none()
        if run:
            steps_stmt = (
                select(RunStepRecord)
                .where(RunStepRecord.run_id == entity_id)
                .where(RunStepRecord.tenant_id == self.tenant_id)
                .order_by(RunStepRecord.started_at)
            )
            steps_res = await self.db.execute(steps_stmt)
            run.steps = list(steps_res.scalars().all())
        return run

    async def get_steps_for_run(self, run_id: str) -> List[RunStepRecord]:
        """Fetch all execution steps for a given run."""
        stmt = (
            select(RunStepRecord)
            .where(RunStepRecord.run_id == run_id)
            .where(RunStepRecord.tenant_id == self.tenant_id)
            .order_by(RunStepRecord.started_at)
        )
        res = await self.db.execute(stmt)
        return list(res.scalars().all())

    async def get_by_idempotency_key(self, idempotency_key: str) -> Optional[RunRecord]:
        """Check for existing execution under the same idempotency key."""
        stmt = (
            select(RunRecord)
            .options(selectinload(RunRecord.steps))
            .where(RunRecord.tenant_id == self.tenant_id)
            .where(RunRecord.idempotency_key == idempotency_key)
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def list_all(self, skip: int = 0, limit: int = 100) -> Sequence[RunRecord]:
        stmt = (
            select(RunRecord)
            .options(selectinload(RunRecord.steps))
            .where(RunRecord.tenant_id == self.tenant_id)
            .order_by(RunRecord.started_at.desc())
            .offset(skip)
            .limit(limit)
        )
        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def record_step(self, step: RunStepRecord) -> RunStepRecord:
        """Persists a new execution step."""
        step.tenant_id = self.tenant_id
        self.db.add(step)
        await self.db.commit()
        await self.db.refresh(step)
        return step

    async def update_step(
        self,
        step_id: str,
        status: str,
        duration_ms: float,
        output_snapshot: Optional[dict] = None,
        error: Optional[str] = None,
    ) -> None:
        """Updates a step upon completion or failure."""
        now = datetime.now(timezone.utc)
        stmt = (
            update(RunStepRecord)
            .where(RunStepRecord.id == step_id)
            .where(RunStepRecord.tenant_id == self.tenant_id)
            .values(
                status=status,
                duration_ms=duration_ms,
                output_snapshot=output_snapshot,
                error=error,
                finished_at=now,
            )
        )
        await self.db.execute(stmt)
        await self.db.commit()

    async def update_run_status(
        self,
        run_id: str,
        status: str,
        duration_seconds: float,
        output_payload: Optional[dict] = None,
        error: Optional[str] = None,
    ) -> None:
        """Updates run state machine terminal status."""
        now = datetime.now(timezone.utc)
        stmt = (
            update(RunRecord)
            .where(RunRecord.id == run_id)
            .where(RunRecord.tenant_id == self.tenant_id)
            .values(
                status=status,
                duration_seconds=duration_seconds,
                output_payload=output_payload,
                error=error,
                finished_at=now,
            )
        )
        await self.db.execute(stmt)
        await self.db.commit()


class DeadLetterRepository(TenantScopedRepository[DeadLetterRecord]):
    """Tenant-scoped repository for Dead Letter Queue records."""

    def __init__(self, db: AsyncSession, tenant_id: str) -> None:
        super().__init__(DeadLetterRecord, db, tenant_id)

    async def list_pending(self, limit: int = 100) -> Sequence[DeadLetterRecord]:
        """Fetch pending DLQ records requiring review or replay."""
        stmt = (
            select(DeadLetterRecord)
            .where(DeadLetterRecord.tenant_id == self.tenant_id)
            .where(DeadLetterRecord.status == "PENDING")
            .order_by(DeadLetterRecord.created_at.desc())
            .limit(limit)
        )
        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def mark_replayed(self, dlq_id: str) -> bool:
        """Marks a DLQ entry as successfully replayed."""
        now = datetime.now(timezone.utc)
        stmt = (
            update(DeadLetterRecord)
            .where(DeadLetterRecord.id == dlq_id)
            .where(DeadLetterRecord.tenant_id == self.tenant_id)
            .values(status="REPLAYED", replayed_at=now)
        )
        result = await self.db.execute(stmt)
        await self.db.commit()
        return result.rowcount > 0

    async def mark_discarded(self, dlq_id: str) -> bool:
        """Marks a DLQ entry as discarded by operator."""
        stmt = (
            update(DeadLetterRecord)
            .where(DeadLetterRecord.id == dlq_id)
            .where(DeadLetterRecord.tenant_id == self.tenant_id)
            .values(status="DISCARDED")
        )
        result = await self.db.execute(stmt)
        await self.db.commit()
        return result.rowcount > 0


class IncidentRepository(TenantScopedRepository[IncidentRecord]):
    """Tenant-scoped repository for operational incidents and root-cause timelines."""

    def __init__(self, db: AsyncSession, tenant_id: str) -> None:
        super().__init__(IncidentRecord, db, tenant_id)

    async def list_active(self) -> Sequence[IncidentRecord]:
        """Lists currently open or investigating incidents."""
        stmt = (
            select(IncidentRecord)
            .where(IncidentRecord.tenant_id == self.tenant_id)
            .where(IncidentRecord.status.in_(["OPEN", "INVESTIGATING"]))
            .order_by(IncidentRecord.opened_at.desc())
        )
        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def get_open_for_connection(self, connection_id: str) -> Optional[IncidentRecord]:
        """Finds any active open incident attached to a specific degraded connection."""
        stmt = (
            select(IncidentRecord)
            .where(IncidentRecord.tenant_id == self.tenant_id)
            .where(IncidentRecord.connection_id == connection_id)
            .where(IncidentRecord.status.in_(["OPEN", "INVESTIGATING", "RECOVERED"]))
            .order_by(IncidentRecord.opened_at.desc())
            .limit(1)
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def add_timeline_event(self, incident_id: str, message: str) -> None:
        """Appends an event timestamp to the incident timeline."""
        incident = await self.get_by_id(incident_id)
        if not incident:
            return
        now_str = datetime.now(timezone.utc).strftime("%H:%M:%S")
        updated_timeline = list(incident.timeline or [])
        updated_timeline.append({"timestamp": now_str, "message": message})
        stmt = (
            update(IncidentRecord)
            .where(IncidentRecord.id == incident_id)
            .where(IncidentRecord.tenant_id == self.tenant_id)
            .values(timeline=updated_timeline)
        )
        await self.db.execute(stmt)
        await self.db.commit()

    async def update_status(self, incident_id: str, status: str, resolved: bool = False) -> None:
        """Transitions incident status with optional resolved_at timestamp."""
        now = datetime.now(timezone.utc) if resolved else None
        stmt = (
            update(IncidentRecord)
            .where(IncidentRecord.id == incident_id)
            .where(IncidentRecord.tenant_id == self.tenant_id)
            .values(status=status, resolved_at=now)
        )
        await self.db.execute(stmt)
        await self.db.commit()


class AgentRepository(TenantScopedRepository[AgentRecord]):
    """Tenant-scoped repository for FlowMesh Edge Agents."""

    def __init__(self, db: AsyncSession, tenant_id: str) -> None:
        super().__init__(AgentRecord, db, tenant_id)

    async def create_agent(
        self,
        agent_id: str,
        name: str,
        version: str = "v0.5.0",
        enrollment_token: Optional[str] = None,
        public_key: Optional[str] = None,
        connectors: Optional[List[dict]] = None,
    ) -> AgentRecord:
        record = AgentRecord(
            id=agent_id,
            tenant_id=self.tenant_id,
            name=name,
            version=version,
            status="OFFLINE" if enrollment_token else "ONLINE",
            enrollment_token=enrollment_token,
            public_key=public_key,
            connectors=connectors or [],
            last_heartbeat_at=datetime.now(timezone.utc) if not enrollment_token else None,
        )
        self.db.add(record)
        await self.db.commit()
        await self.db.refresh(record)
        return record

    async def get_by_enrollment_token(self, token: str) -> Optional[AgentRecord]:
        stmt = (
            select(AgentRecord)
            .where(AgentRecord.enrollment_token == token)
            .where(AgentRecord.tenant_id == self.tenant_id)
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def enroll_agent(
        self,
        token: str,
        name: str,
        version: str,
        public_key: Optional[str] = None,
    ) -> Optional[AgentRecord]:
        agent = await self.get_by_enrollment_token(token)
        if not agent:
            return None
        agent.name = name or agent.name
        agent.version = version or agent.version
        if public_key:
            agent.public_key = public_key
        agent.status = "ONLINE"
        agent.last_heartbeat_at = datetime.now(timezone.utc)
        agent.enrollment_token = None
        await self.db.commit()
        await self.db.refresh(agent)
        return agent

    async def update_heartbeat(
        self,
        agent_id: str,
        cpu_percent: float,
        memory_percent: float,
        queue_depth: int,
        connectors: Optional[List[dict]] = None,
    ) -> Optional[AgentRecord]:
        agent = await self.get_by_id(agent_id)
        if not agent:
            return None
        agent.cpu_percent = cpu_percent
        agent.memory_percent = memory_percent
        agent.queue_depth = queue_depth
        agent.status = "ONLINE"
        agent.last_heartbeat_at = datetime.now(timezone.utc)
        if connectors is not None:
            agent.connectors = connectors
        await self.db.commit()
        await self.db.refresh(agent)
        return agent


class AgentCommandRepository(TenantScopedRepository[AgentCommandRecord]):
    """Tenant-scoped repository for dispatched and buffered edge commands."""

    def __init__(self, db: AsyncSession, tenant_id: str) -> None:
        super().__init__(AgentCommandRecord, db, tenant_id)

    async def create_command(
        self,
        command_id: str,
        agent_id: str,
        connector: str,
        connection_id: str,
        operation: str,
        resource: Optional[str] = None,
        limit: Optional[int] = None,
        payload: Optional[dict] = None,
        signature: Optional[str] = None,
        cmd_type: str = "connector.execute",
    ) -> AgentCommandRecord:
        cmd = AgentCommandRecord(
            id=command_id,
            tenant_id=self.tenant_id,
            agent_id=agent_id,
            type=cmd_type,
            connector=connector,
            connection_id=connection_id,
            operation=operation,
            resource=resource,
            limit=limit,
            payload=payload or {},
            signature=signature,
            status="QUEUED",
        )
        self.db.add(cmd)
        await self.db.commit()
        await self.db.refresh(cmd)
        return cmd

    async def get_pending_commands(self, agent_id: str, limit: int = 10) -> Sequence[AgentCommandRecord]:
        stmt = (
            select(AgentCommandRecord)
            .where(AgentCommandRecord.tenant_id == self.tenant_id)
            .where(AgentCommandRecord.agent_id == agent_id)
            .where(AgentCommandRecord.status == "QUEUED")
            .order_by(AgentCommandRecord.created_at.asc())
            .limit(limit)
        )
        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def mark_dispatched(self, command_id: str) -> None:
        stmt = (
            update(AgentCommandRecord)
            .where(AgentCommandRecord.id == command_id)
            .where(AgentCommandRecord.tenant_id == self.tenant_id)
            .values(status="DISPATCHED", dispatched_at=datetime.now(timezone.utc))
        )
        await self.db.execute(stmt)
        await self.db.commit()

    async def record_result(
        self,
        command_id: str,
        status: str,
        result: Optional[dict] = None,
        error: Optional[str] = None,
    ) -> Optional[AgentCommandRecord]:
        cmd = await self.get_by_id(command_id)
        if not cmd:
            return None
        cmd.status = status
        cmd.result = result
        cmd.error = error
        cmd.completed_at = datetime.now(timezone.utc)
        await self.db.commit()
        await self.db.refresh(cmd)
        return cmd


class SchemaSnapshotRepository(TenantScopedRepository[SchemaSnapshot]):
    """Tenant-isolated repository for connection schema snapshots and baseline tracking."""

    def __init__(self, db: AsyncSession, tenant_id: str) -> None:
        super().__init__(SchemaSnapshot, db, tenant_id)

    async def get_baseline(self, connection_id: str) -> Optional[SchemaSnapshot]:
        stmt = (
            select(SchemaSnapshot)
            .where(SchemaSnapshot.tenant_id == self.tenant_id)
            .where(SchemaSnapshot.connection_id == connection_id)
            .where(SchemaSnapshot.is_baseline == True)
            .order_by(SchemaSnapshot.version.desc())
        )
        result = await self.db.execute(stmt)
        return result.scalars().first()

    async def get_latest(self, connection_id: str) -> Optional[SchemaSnapshot]:
        stmt = (
            select(SchemaSnapshot)
            .where(SchemaSnapshot.tenant_id == self.tenant_id)
            .where(SchemaSnapshot.connection_id == connection_id)
            .order_by(SchemaSnapshot.version.desc())
        )
        result = await self.db.execute(stmt)
        return result.scalars().first()

    async def list_history(self, connection_id: str) -> Sequence[SchemaSnapshot]:
        stmt = (
            select(SchemaSnapshot)
            .where(SchemaSnapshot.tenant_id == self.tenant_id)
            .where(SchemaSnapshot.connection_id == connection_id)
            .order_by(SchemaSnapshot.version.desc())
        )
        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def set_baseline(self, connection_id: str, snapshot_id: str) -> Optional[SchemaSnapshot]:

        stmt_unset = (
            update(SchemaSnapshot)
            .where(SchemaSnapshot.tenant_id == self.tenant_id)
            .where(SchemaSnapshot.connection_id == connection_id)
            .values(is_baseline=False)
        )
        await self.db.execute(stmt_unset)

        stmt_set = (
            update(SchemaSnapshot)
            .where(SchemaSnapshot.tenant_id == self.tenant_id)
            .where(SchemaSnapshot.id == snapshot_id)
            .values(is_baseline=True)
        )
        await self.db.execute(stmt_set)
        await self.db.commit()
        return await self.get_by_id(snapshot_id)



