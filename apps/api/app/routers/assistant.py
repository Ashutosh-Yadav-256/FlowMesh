"""
FlowMesh AI Incident Assistant API Router (§30)

Exposes read-only diagnostic telemetry analysis and human-confirmed remediation actions.
"""

from typing import Optional, Dict, Any
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from app.dependencies import DbSession, CurrentAuth
from flowmesh_auth.rbac import is_allowed
from app.repositories.tenant_scoped import RunRepository
from app.assistant.service import (
    DiagnosticReport,
    assistant_service,
)

router = APIRouter(prefix="/api/v1/assistant", tags=["AI Incident Assistant"])


def enforce_rbac(auth: CurrentAuth, resource: str, action: str) -> None:
    if not is_allowed(auth.role, resource, action):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"RBAC Forbidden: Role '{auth.role}' cannot perform '{action}' on resource '{resource}'",
        )


class DiagnoseRequest(BaseModel):
    run_id: str = Field(..., description="ID of the workflow run to diagnose")
    query: Optional[str] = Field(None, description="Optional natural language question, e.g. 'Why did order #1932 fail?'")


class ConfirmActionRequest(BaseModel):
    action_id: str = Field(..., description="Action to confirm: 'REPLAY_RUN' or 'CREATE_INCIDENT'")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Action parameters")


@router.post("/diagnose", response_model=DiagnosticReport)
async def diagnose_run_failure(
    payload: DiagnoseRequest,
    db: DbSession,
    auth: CurrentAuth,
) -> DiagnosticReport:
    """
    Read-only incident diagnosis across logs, traces, runs, and circuit breakers (§30).
    Produces root-cause analysis and proposed human-confirmed remediation actions.
    """
    enforce_rbac(auth, "run", "read")
    try:
        return await assistant_service.diagnose_run(
            db=db,
            tenant_id=auth.tenant_id,
            run_id=payload.run_id,
            query=payload.query,
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Diagnostic analysis error: {str(e)}")


@router.post("/actions/confirm")
async def confirm_remediation_action(
    payload: ConfirmActionRequest,
    db: DbSession,
    auth: CurrentAuth,
) -> Dict[str, Any]:
    """
    Executes a proposed remediation action after explicit confirmation by a human operator.
    Guarantees no autonomous mutations without operator signoff.
    """

    enforce_rbac(auth, "run", "update")
    try:
        return await assistant_service.confirm_action(
            db=db,
            tenant_id=auth.tenant_id,
            action_id=payload.action_id,
            parameters=payload.parameters,
            actor_email=auth.email,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Action execution failure: {str(e)}")
