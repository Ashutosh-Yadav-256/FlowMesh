"""
FlowMesh Workflows API Router

Features:
- Tenant-scoped workflow management backed by database repository.
- Immutable workflow versioning (ADR-0004).
- DAG cycle detection and contract validation.
- Declarative RBAC enforcement.
"""

import uuid
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from app.dependencies import DbSession, CurrentAuth
from flowmesh_auth.rbac import is_allowed
from sqlalchemy import select as sa_select, func as sa_func
from app.models.workflow import WorkflowRecord, WorkflowVersionRecord
from app.models.run import RunRecord
from app.repositories.tenant_scoped import (
    WorkflowRepository,
    WorkflowVersionRepository,
    AuditRepository,
    ConnectionRepository,
    RunRepository,
)
from flowmesh_workflow.schema import WorkflowDefinition, WorkflowNode, WorkflowEdge
from flowmesh_engine.validation import WorkflowValidator, ValidationResult
from app.policy.engine import (
    default_policy_engine,
    PolicyMode,
    PolicySeverity,
    PolicyEvaluationResult,
)

router = APIRouter(prefix="/api/v1/workflows", tags=["Workflows"])


def enforce_rbac(auth: CurrentAuth, resource: str, action: str) -> None:
    if not is_allowed(auth.role, resource, action):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"RBAC Forbidden: Role '{auth.role}' cannot perform '{action}' on resource '{resource}'",
        )


class WorkflowSummary(BaseModel):
    id: str
    name: str
    status: str
    version: int
    trigger_type: str
    node_count: int
    runs_24h: int
    success_rate: float
    updated_at: str


class WorkflowDetail(WorkflowSummary):
    definition: WorkflowDefinition


class DeployWorkflowRequest(BaseModel):
    changelog: str = Field(default="Production deployment")
    definition: Optional[Dict[str, Any]] = None


class RollbackWorkflowRequest(BaseModel):
    target_version: int
    reason: Optional[str] = "Operator rollback"


class WorkflowVersionSummary(BaseModel):
    id: str
    workflow_id: str
    version: int
    changelog: str
    deployed_by: str
    deployed_at: str
    is_active: bool
    node_count: int


from typing import Annotated
from fastapi import Depends, Response
from app.pagination import PaginationParams, paginate_items


@router.get("", response_model=List[WorkflowSummary])
async def list_workflows(
    db: DbSession,
    auth: CurrentAuth,
    pagination: Annotated[PaginationParams, Depends()],
    response: Response,
) -> List[WorkflowSummary]:
    """List all configured workflows with version and activity metrics."""
    enforce_rbac(auth, "workflow", "read")
    repo = WorkflowRepository(db, auth.tenant_id)

    total = await repo.count()
    records = await repo.list_all(skip=pagination.offset, limit=pagination.limit)

    from app.repositories.tenant_scoped import RunRepository
    from sqlalchemy import select as sa_select, func as sa_func
    from app.models.run import RunRecord
    from datetime import timedelta

    run_repo = RunRepository(db, auth.tenant_id)
    cutoff = datetime.now(timezone.utc) - timedelta(hours=24)

    results = []
    for r in records:

        count_stmt = (
            sa_select(sa_func.count())
            .select_from(RunRecord)
            .where(RunRecord.tenant_id == auth.tenant_id)
            .where(RunRecord.workflow_id == r.id)
            .where(RunRecord.started_at >= cutoff)
        )
        runs_24h = (await db.execute(count_stmt)).scalar_one() or 0

        success_stmt = (
            sa_select(sa_func.count())
            .select_from(RunRecord)
            .where(RunRecord.tenant_id == auth.tenant_id)
            .where(RunRecord.workflow_id == r.id)
            .where(RunRecord.started_at >= cutoff)
            .where(RunRecord.status == "SUCCESS")
        )
        success_count = (await db.execute(success_stmt)).scalar_one() or 0
        success_rate = round((success_count / runs_24h * 100), 2) if runs_24h > 0 else 100.0

        results.append(
            WorkflowSummary(
                id=r.id,
                name=r.name,
                status=r.status,
                version=r.version,
                trigger_type=r.trigger_type,
                node_count=len(r.definition_json.get("nodes", [])),
                runs_24h=runs_24h,
                success_rate=success_rate,
                updated_at=r.updated_at.isoformat(),
            )
        )
    return paginate_items(results, total=total, params=pagination, response=response)


@router.post("/validate", response_model=ValidationResult)
async def validate_workflow(
    payload: WorkflowDefinition,
    db: DbSession,
    auth: CurrentAuth,
) -> ValidationResult:
    """Runs pre-flight topological, cycle, reachability, and tenant-connection validation."""
    enforce_rbac(auth, "workflow", "read")
    conn_repo = ConnectionRepository(db, auth.tenant_id)
    conns = await conn_repo.list_all()
    available_conn_ids = {c.id for c in conns}
    return WorkflowValidator.validate(payload.model_dump(), available_connection_ids=available_conn_ids)


@router.get("/{workflow_id}", response_model=WorkflowDetail)
async def get_workflow(
    workflow_id: str,
    db: DbSession,
    auth: CurrentAuth,
) -> WorkflowDetail:
    """Get workflow specification and DAG graph nodes."""
    enforce_rbac(auth, "workflow", "read")
    repo = WorkflowRepository(db, auth.tenant_id)

    wf = await repo.get_by_id(workflow_id)
    if not wf:
        raise HTTPException(status_code=404, detail="Workflow not found")

    cutoff = datetime.now(timezone.utc) - timedelta(hours=24)
    count_stmt = (
        sa_select(sa_func.count())
        .select_from(RunRecord)
        .where(RunRecord.tenant_id == auth.tenant_id)
        .where(RunRecord.workflow_id == wf.id)
        .where(RunRecord.started_at >= cutoff)
    )
    runs_24h = (await db.execute(count_stmt)).scalar_one() or 0

    success_stmt = (
        sa_select(sa_func.count())
        .select_from(RunRecord)
        .where(RunRecord.tenant_id == auth.tenant_id)
        .where(RunRecord.workflow_id == wf.id)
        .where(RunRecord.started_at >= cutoff)
        .where(RunRecord.status == "SUCCESS")
    )
    success_count = (await db.execute(success_stmt)).scalar_one() or 0
    success_rate = round((success_count / runs_24h * 100), 2) if runs_24h > 0 else 100.0

    return WorkflowDetail(
        id=wf.id,
        name=wf.name,
        status=wf.status,
        version=wf.version,
        trigger_type=wf.trigger_type,
        node_count=len(wf.definition_json.get("nodes", [])),
        runs_24h=runs_24h,
        success_rate=success_rate,
        updated_at=wf.updated_at.isoformat(),
        definition=WorkflowDefinition(**wf.definition_json),
    )


@router.post("", response_model=WorkflowDetail, status_code=status.HTTP_201_CREATED)
async def create_workflow(
    payload: WorkflowDefinition,
    db: DbSession,
    auth: CurrentAuth,
) -> WorkflowDetail:
    """Create a new draft workflow with DAG validation."""
    enforce_rbac(auth, "workflow", "create")
    repo = WorkflowRepository(db, auth.tenant_id)
    audit_repo = AuditRepository(db, auth.tenant_id)

    now = datetime.now(timezone.utc)
    new_id = f"wf_{uuid.uuid4().hex[:8]}"

    wf = WorkflowRecord(
        id=new_id,
        tenant_id=auth.tenant_id,
        name=payload.name,
        description=payload.description,
        status="draft",
        version=1,
        trigger_type=payload.trigger.type,
        definition_json=payload.model_dump(),
        created_at=now,
        updated_at=now,
    )
    await repo.create(wf)

    await audit_repo.record(
        actor=auth.email,
        action="workflow.create",
        resource=f"workflow/{new_id}",
        result="SUCCESS",
        metadata={"name": payload.name, "version": 1},
    )

    v1 = WorkflowVersionRecord(
        id=f"wfv_{new_id}_v1",
        tenant_id=auth.tenant_id,
        workflow_id=new_id,
        version=1,
        definition_json=payload.model_dump(),
        changelog="Initial draft creation",
        deployed_by=auth.email,
        deployed_at=now,
        is_active=False,
    )
    db.add(v1)
    await db.commit()

    return WorkflowDetail(
        id=wf.id,
        name=wf.name,
        status=wf.status,
        version=wf.version,
        trigger_type=wf.trigger_type,
        node_count=len(payload.nodes),
        runs_24h=0,
        success_rate=100.0,
        updated_at=wf.updated_at.isoformat(),
        definition=payload,
    )


@router.post("/{workflow_id}/deploy", response_model=WorkflowDetail)
async def deploy_workflow(
    workflow_id: str,
    payload: DeployWorkflowRequest,
    db: DbSession,
    auth: CurrentAuth,
) -> WorkflowDetail:
    """
    Deploys a workflow as an immutable version N+1 (ADR-0004).
    Validates definition before deployment.
    """
    enforce_rbac(auth, "workflow", "update")
    repo = WorkflowRepository(db, auth.tenant_id)
    audit_repo = AuditRepository(db, auth.tenant_id)
    conn_repo = ConnectionRepository(db, auth.tenant_id)

    wf = await repo.get_by_id(workflow_id)
    if not wf:
        raise HTTPException(status_code=404, detail="Workflow not found")

    target_def_dict = payload.definition if payload.definition else wf.definition_json

    conns = await conn_repo.list_all()
    val_res = WorkflowValidator.validate(target_def_dict, available_connection_ids={c.id for c in conns})
    if not val_res.is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"message": "Pre-flight validation failed", "errors": val_res.errors},
        )

    policy_res = default_policy_engine.evaluate(target_def_dict, mode=PolicyMode.ENFORCE)
    if not policy_res.allowed:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "message": "Policy-as-Code violation: deployment blocked by organization governance policy",
                "violations": [v.model_dump() for v in policy_res.violations if v.severity == PolicySeverity.ERROR],
            },
        )

    version_record = await repo.deploy_version(
        workflow_id=workflow_id,
        definition_json=target_def_dict,
        changelog=payload.changelog,
        deployed_by=auth.email,
    )

    await audit_repo.record(
        actor=auth.email,
        action="workflow.deploy",
        resource=f"workflow/{workflow_id}",
        result="SUCCESS",
        metadata={"version": version_record.version, "changelog": payload.changelog},
    )

    refreshed_wf = await repo.get_by_id(workflow_id)
    return WorkflowDetail(
        id=refreshed_wf.id,
        name=refreshed_wf.name,
        status=refreshed_wf.status,
        version=refreshed_wf.version,
        trigger_type=refreshed_wf.trigger_type,
        node_count=len(refreshed_wf.definition_json.get("nodes", [])),
        runs_24h=0,
        success_rate=100.0,
        updated_at=refreshed_wf.updated_at.isoformat(),
        definition=WorkflowDefinition(**refreshed_wf.definition_json),
    )


@router.post("/{workflow_id}/validate-policy", response_model=PolicyEvaluationResult)
async def validate_workflow_policy(
    workflow_id: str,
    db: DbSession,
    auth: CurrentAuth,
    definition: Optional[Dict[str, Any]] = None,
    mode: PolicyMode = PolicyMode.ENFORCE,
) -> PolicyEvaluationResult:
    """Evaluates Policy-as-Code rules against the workflow definition without deploying."""
    enforce_rbac(auth, "workflow", "read")
    repo = WorkflowRepository(db, auth.tenant_id)
    wf = await repo.get_by_id(workflow_id)
    if not wf:
        raise HTTPException(status_code=404, detail="Workflow not found")
    target_def = definition or wf.definition_json
    return default_policy_engine.evaluate(target_def, mode=mode)


@router.post("/{workflow_id}/rollback", response_model=WorkflowDetail)
async def rollback_workflow(
    workflow_id: str,
    payload: RollbackWorkflowRequest,
    db: DbSession,
    auth: CurrentAuth,
) -> WorkflowDetail:
    """
    Rolls back active workflow to a prior immutable version (ADR-0004).
    Points active pointer to target version without altering historical run telemetry.
    """
    enforce_rbac(auth, "workflow", "update")
    repo = WorkflowRepository(db, auth.tenant_id)
    audit_repo = AuditRepository(db, auth.tenant_id)

    wf = await repo.get_by_id(workflow_id)
    if not wf:
        raise HTTPException(status_code=404, detail="Workflow not found")

    try:
        rolled_back_ver = await repo.rollback_to_version(
            workflow_id=workflow_id,
            target_version=payload.target_version,
            deployed_by=auth.email,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    await audit_repo.record(
        actor=auth.email,
        action="workflow.rollback",
        resource=f"workflow/{workflow_id}",
        result="SUCCESS",
        metadata={"target_version": payload.target_version, "reason": payload.reason},
    )

    refreshed_wf = await repo.get_by_id(workflow_id)
    return WorkflowDetail(
        id=refreshed_wf.id,
        name=refreshed_wf.name,
        status=refreshed_wf.status,
        version=refreshed_wf.version,
        trigger_type=refreshed_wf.trigger_type,
        node_count=len(refreshed_wf.definition_json.get("nodes", [])),
        runs_24h=0,
        success_rate=100.0,
        updated_at=refreshed_wf.updated_at.isoformat(),
        definition=WorkflowDefinition(**refreshed_wf.definition_json),
    )


@router.get("/{workflow_id}/versions", response_model=List[WorkflowVersionSummary])
async def list_workflow_versions(
    workflow_id: str,
    db: DbSession,
    auth: CurrentAuth,
) -> List[WorkflowVersionSummary]:
    """Retrieves immutable historical deployment versions for a workflow (ADR-0004)."""
    enforce_rbac(auth, "workflow", "read")
    repo = WorkflowRepository(db, auth.tenant_id)
    ver_repo = WorkflowVersionRepository(db, auth.tenant_id)

    wf = await repo.get_by_id(workflow_id)
    if not wf:
        raise HTTPException(status_code=404, detail="Workflow not found")

    versions = await ver_repo.list_for_workflow(workflow_id)
    if not versions:

        v1 = WorkflowVersionRecord(
            id=f"wfv_{wf.id}_v{wf.version}",
            tenant_id=auth.tenant_id,
            workflow_id=wf.id,
            version=wf.version,
            definition_json=wf.definition_json,
            changelog="Base version release",
            deployed_by=auth.email,
            deployed_at=wf.created_at,
            is_active=True,
        )
        await ver_repo.create(v1)
        versions = [v1]

    return [
        WorkflowVersionSummary(
            id=v.id,
            workflow_id=v.workflow_id,
            version=v.version,
            changelog=v.changelog,
            deployed_by=v.deployed_by or "system",
            deployed_at=v.deployed_at.isoformat(),
            is_active=v.is_active,
            node_count=len(v.definition_json.get("nodes", [])),
        )
        for v in versions
    ]
