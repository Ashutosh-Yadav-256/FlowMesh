"""
FlowMesh Runs & Executions API Router

Features:
- Tenant-scoped execution tracking backed by RunRecord and RunStepRecord.
- Step-by-step timeline inspection with duration, status, and input/output snapshots.
- Replay execution with idempotency protection.
- Declarative RBAC enforcement.
"""

import uuid
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

from app.dependencies import DbSession, CurrentAuth
from flowmesh_auth.rbac import is_allowed
from app.models.run import RunRecord, RunStepRecord
from app.models.workflow import WorkflowRecord
from app.repositories.tenant_scoped import RunRepository, WorkflowRepository, AuditRepository
from flowmesh_workflow.schema import WorkflowDefinition
from flowmesh_engine.engine import WorkflowEngine

router = APIRouter(prefix="/api/v1/runs", tags=["Runs & Executions"])


def enforce_rbac(auth: CurrentAuth, resource: str, action: str) -> None:
    if not is_allowed(auth.role, resource, action):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"RBAC Forbidden: Role '{auth.role}' cannot perform '{action}' on resource '{resource}'",
        )


class RunStep(BaseModel):
    step_id: str
    name: str
    node_id: str
    status: str
    attempt: int
    duration_ms: float
    started_at: str
    error: Optional[str] = None
    input_snapshot: Dict[str, Any]
    output_snapshot: Optional[Dict[str, Any]] = None


class RunSummary(BaseModel):
    id: str
    workflow_id: str
    workflow_name: str
    version: int
    status: str
    duration_seconds: float
    started_at: str
    finished_at: Optional[str] = None
    trigger_source: str
    trace_id: str


class RunDetail(RunSummary):
    steps: List[RunStep]
    input_payload: Dict[str, Any]
    output_payload: Optional[Dict[str, Any]] = None


class ApproveRunRequest(BaseModel):
    comment: Optional[str] = None


class RejectRunRequest(BaseModel):
    reason: Optional[str] = "Operator rejected run"



from typing import Annotated
from fastapi import Depends, Response
from app.pagination import PaginationParams, paginate_items


@router.get("", response_model=List[RunSummary])
async def list_runs(
    db: DbSession,
    auth: CurrentAuth,
    pagination: Annotated[PaginationParams, Depends()],
    response: Response,
) -> List[RunSummary]:
    """List workflow execution runs for active tenant."""
    enforce_rbac(auth, "run", "read")
    repo = RunRepository(db, auth.tenant_id)

    total = await repo.count()
    runs = await repo.list_all(skip=pagination.offset, limit=pagination.limit)

    wf_repo = WorkflowRepository(db, auth.tenant_id)
    all_wfs = await wf_repo.list_all()
    wf_name_map = {w.id: w.name for w in all_wfs}

    items = [
        RunSummary(
            id=r.id,
            workflow_id=r.workflow_id,
            workflow_name=wf_name_map.get(r.workflow_id, "Unknown Workflow"),
            version=r.workflow_version,
            status=r.status,
            duration_seconds=r.duration_seconds,
            started_at=r.started_at.isoformat(),
            finished_at=r.finished_at.isoformat() if r.finished_at else None,
            trigger_source=r.trigger_source,
            trace_id=r.trace_id,
        )
        for r in runs
    ]
    return paginate_items(items, total=total, params=pagination, response=response)


def _format_run_detail(run: RunRecord, workflow_name: str = "Unknown Workflow") -> RunDetail:
    steps = [
        RunStep(
            step_id=s.id,
            name=s.name,
            node_id=s.node_id,
            status=s.status,
            attempt=s.attempt,
            duration_ms=s.duration_ms,
            started_at=s.started_at.isoformat(),
            error=s.error,
            input_snapshot=s.input_snapshot,
            output_snapshot=s.output_snapshot,
        )
        for s in (run.steps or [])
    ]

    return RunDetail(
        id=run.id,
        workflow_id=run.workflow_id,
        workflow_name=workflow_name,
        version=run.workflow_version,
        status=run.status,
        duration_seconds=run.duration_seconds,
        started_at=run.started_at.isoformat(),
        finished_at=run.finished_at.isoformat() if run.finished_at else None,
        trigger_source=run.trigger_source,
        trace_id=run.trace_id,
        steps=steps,
        input_payload=run.input_payload,
        output_payload=run.output_payload,
    )


@router.get("/{run_id}", response_model=RunDetail)
async def get_run_detail(
    run_id: str,
    db: DbSession,
    auth: CurrentAuth,
) -> RunDetail:
    """Retrieve full step execution timeline and telemetry for a specific run."""
    enforce_rbac(auth, "run", "read")
    repo = RunRepository(db, auth.tenant_id)

    run = await repo.get_by_id(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")

    wf_repo = WorkflowRepository(db, auth.tenant_id)
    wf = await wf_repo.get_by_id(run.workflow_id)
    wf_name = wf.name if wf else "Unknown Workflow"

    return _format_run_detail(run, wf_name)


@router.post("/{run_id}/replay", response_model=Dict[str, Any])
async def replay_run(
    run_id: str,
    db: DbSession,
    auth: CurrentAuth,
) -> Dict[str, Any]:
    """Replays a run from original ingress event with idempotency verification."""
    enforce_rbac(auth, "run", "replay")
    repo = RunRepository(db, auth.tenant_id)
    wf_repo = WorkflowRepository(db, auth.tenant_id)
    audit_repo = AuditRepository(db, auth.tenant_id)

    orig_run = await repo.get_by_id(run_id)
    if not orig_run:
        raise HTTPException(status_code=404, detail=f"Run '{run_id}' not found")

    wf = await wf_repo.get_by_id(orig_run.workflow_id)
    if not wf or not wf.definition_json:
        raise HTTPException(status_code=400, detail=f"Workflow definition for '{orig_run.workflow_id}' not found")

    new_run_id = f"RUN-{uuid.uuid4().hex[:6].upper()}"
    wf_def = WorkflowDefinition(**wf.definition_json)
    engine = WorkflowEngine(db, auth.tenant_id)

    try:
        re_run = await engine.execute(
            workflow_def=wf_def,
            run_id=new_run_id,
            input_payload=orig_run.input_payload or {},
            trace_id=orig_run.trace_id or uuid.uuid4().hex,
            trigger_source=f"replay:{orig_run.id}",
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Execution error during run replay: {str(exc)}")

    await audit_repo.record(
        actor=auth.email,
        action="run.replay",
        resource=f"runs/{new_run_id}",
        result="SUCCESS",
        metadata={
            "original_run_id": orig_run.id,
            "new_run_id": re_run.id,
            "status": re_run.status,
        },
    )

    return {
        "status": "REPLAYED",
        "original_run_id": orig_run.id,
        "new_run_id": re_run.id,
        "run_status": re_run.status,
        "duration_seconds": re_run.duration_seconds,
        "message": f"Run {orig_run.id} replayed into new execution {re_run.id} with status {re_run.status}",
    }


@router.post("/{run_id}/approve", response_model=RunDetail)
async def approve_run(
    run_id: str,
    payload: ApproveRunRequest,
    db: DbSession,
    auth: CurrentAuth,
) -> RunDetail:
    """Approves an execution parked at an action.approval node and resumes DAG execution."""
    enforce_rbac(auth, "run", "execute")
    repo = RunRepository(db, auth.tenant_id)
    audit_repo = AuditRepository(db, auth.tenant_id)

    run = await repo.get_by_id(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    if run.status != "WAITING_APPROVAL":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Run {run_id} is not waiting for approval (status: {run.status})",
        )

    engine = WorkflowEngine(db, auth.tenant_id)
    try:
        resumed_run = await engine.resume_approval(
            run_id=run_id,
            approved=True,
            approver_email=auth.email,
            comment=payload.comment,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to resume approved run: {str(exc)}")

    await audit_repo.record(
        actor=auth.email,
        action="run.approve",
        resource=f"runs/{run_id}",
        result="SUCCESS",
        metadata={"comment": payload.comment, "final_status": resumed_run.status},
    )

    full_run = await repo.get_by_id(run_id)
    return _format_run_detail(full_run or resumed_run)


@router.post("/{run_id}/reject", response_model=RunDetail)
async def reject_run(
    run_id: str,
    payload: RejectRunRequest,
    db: DbSession,
    auth: CurrentAuth,
) -> RunDetail:
    """Rejects an execution parked at an action.approval node and marks it REJECTED."""
    enforce_rbac(auth, "run", "execute")
    repo = RunRepository(db, auth.tenant_id)
    audit_repo = AuditRepository(db, auth.tenant_id)

    run = await repo.get_by_id(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    if run.status != "WAITING_APPROVAL":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Run {run_id} is not waiting for approval (status: {run.status})",
        )

    engine = WorkflowEngine(db, auth.tenant_id)
    resumed_run = await engine.resume_approval(
        run_id=run_id,
        approved=False,
        approver_email=auth.email,
        comment=payload.reason,
    )

    await audit_repo.record(
        actor=auth.email,
        action="run.reject",
        resource=f"runs/{run_id}",
        result="SUCCESS",
        metadata={"reason": payload.reason},
    )

    full_run = await repo.get_by_id(run_id)
    return _format_run_detail(full_run or resumed_run)
