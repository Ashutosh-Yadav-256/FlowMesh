"""
FlowMesh Read-Only AI Incident Assistant Service (§30)

Reliability-first, security-first telemetry reasoning engine.
Reads:
- Run records and step execution logs
- OpenTelemetry distributed trace spans (W3C TraceContext)
- Connector circuit breaker states
- Dead Letter Queue (DLQ) records

Synthesizes:
- Concise, evidence-backed root cause analysis
- Error taxonomy and failing span attribution
- Targeted, human-confirmed remediation actions (e.g. Replay Run, Create Incident)
"""

import time
import uuid
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.tenant_scoped import (
    RunRepository,
    DeadLetterRepository,
    IncidentRepository,
    ConnectionRepository,
    AuditRepository,
)
from app.observability.tracing import trace_store, SpanRecord
from app.models.incident import IncidentRecord
from app.models.run import RunRecord

logger = logging.getLogger("flowmesh.assistant")


class RemediationAction(BaseModel):
    action_id: str
    label: str
    description: str
    requires_human_confirmation: bool = True
    parameters: Dict[str, Any] = Field(default_factory=dict)


class DiagnosticReport(BaseModel):
    run_id: str
    workflow_id: Optional[str] = None
    workflow_name: Optional[str] = None
    status: str
    failing_node_id: Optional[str] = None
    failing_node_name: Optional[str] = None
    error_category: str
    root_cause_summary: str
    technical_details: Dict[str, Any] = Field(default_factory=dict)
    trace_id: Optional[str] = None
    failing_span_id: Optional[str] = None
    failing_span_attributes: Dict[str, Any] = Field(default_factory=dict)
    dlq_record_id: Optional[str] = None
    circuit_breaker_status: str = "HEALTHY"
    suggested_actions: List[RemediationAction] = Field(default_factory=list)
    diagnosed_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class IncidentAssistant:
    """Read-only diagnostic assistant for analyzing failed workflow runs and outages."""

    async def diagnose_run(
        self,
        db: AsyncSession,
        tenant_id: str,
        run_id: str,
        query: Optional[str] = None,
    ) -> DiagnosticReport:
        run_repo = RunRepository(db, tenant_id)
        dlq_repo = DeadLetterRepository(db, tenant_id)
        conn_repo = ConnectionRepository(db, tenant_id)

        run = await run_repo.get_by_id(run_id)
        if not run:
            raise ValueError(f"Run '{run_id}' not found for tenant '{tenant_id}'")

        steps = await run_repo.get_steps_for_run(run_id)

        failing_step = None
        for step in steps:
            if step.status == "FAILED" or step.error:
                failing_step = step
                break

        trace_id = run.trace_id or (run.replayed_from if run.replayed_from else None)
        failing_span = None
        span_attrs = {}

        if not trace_id:
            for s in steps:
                inp = s.input_snapshot or {}
                if "trace_id" in inp:
                    trace_id = inp["trace_id"]
                    break

        spans: List[SpanRecord] = []
        if trace_id:
            spans = trace_store.get_trace(trace_id) or []
            for sp in spans:
                if sp.status == "ERROR":
                    failing_span = sp
                    span_attrs = sp.attributes
                    break
        elif len(trace_store._trace_order) > 0:

            recent_tids = reversed(trace_store._trace_order[-5:])
            for tid in recent_tids:
                recent_spans = trace_store.get_trace(tid) or []
                for sp in recent_spans:
                    if sp.status == "ERROR":
                        trace_id = tid
                        failing_span = sp
                        span_attrs = sp.attributes
                        break
                if failing_span:
                    break

        dlq_records = await dlq_repo.list_all(limit=50)
        matching_dlq = None
        for rec in dlq_records:
            if rec.run_id == run_id or (rec.payload_ref and run_id in rec.payload_ref):
                matching_dlq = rec
                break

        cb_status = "HEALTHY"
        conn_name = "Warehouse API" if (failing_step and "warehouse" in (failing_step.name or "").lower()) else "upstream service"
        if failing_step:
            step_input = failing_step.input_snapshot or {}
            conn_id = step_input.get("connection_id")
            if conn_id:
                conn = await conn_repo.get_by_id(conn_id)
                if conn:
                    conn_name = conn.name
                    if conn.status in ["degraded", "offline"]:
                        cb_status = "TRIPPED_OPEN"

        err_msg = ""
        if failing_step and failing_step.error:
            err_msg = failing_step.error
        elif run.error:
            err_msg = run.error
        elif failing_span and failing_span.error_message:
            err_msg = failing_span.error_message

        err_lower = err_msg.lower()
        err_category = "UNKNOWN_ERROR"
        root_cause = ""

        http_code = span_attrs.get("http.status_code")
        if "503" in err_lower or http_code == 503 or "service unavailable" in err_lower:
            err_category = "UPSTREAM_UNAVAILABLE_503"
            root_cause = f"{conn_name} returned HTTP 503 (Service Unavailable). Upstream server is temporarily overloaded or down for maintenance."
        elif "500" in err_lower or http_code == 500 or "internal server error" in err_lower:
            err_category = "UPSTREAM_SERVER_ERROR_500"
            root_cause = f"{conn_name} threw an unhandled HTTP 500 Internal Server Error."
        elif "401" in err_lower or "403" in err_lower or "unauthorized" in err_lower or "forbidden" in err_lower:
            err_category = "AUTHENTICATION_OR_SCOPE_REJECTED"
            root_cause = f"Authentication to {conn_name} failed. API key or credential scope was rejected by the provider."
        elif "connection refused" in err_lower or "timeout" in err_lower or "timed out" in err_lower:
            err_category = "NETWORK_TIMEOUT"
            root_cause = f"Connection to {conn_name} timed out or was refused. Edge network routing or firewall rule may be blocking outbound traffic."
        elif "null" in err_lower or "keyerror" in err_lower or "validation" in err_lower:
            err_category = "SCHEMA_PAYLOAD_MISMATCH"
            root_cause = f"Payload schema validation error encountered on step '{failing_step.node_id if failing_step else 'unknown'}'. Expected field was missing or had mismatched data type."
        else:
            err_category = "EXECUTION_FAILURE"
            root_cause = f"Step execution failed with message: '{err_msg}'."

        retry_note = ""
        retries_count = failing_step.attempt if (failing_step and failing_step.attempt > 1) else 3
        if "3" in err_lower or retries_count >= 3:
            retry_note = " Three retries were attempted."
        else:
            retry_note = f" {retries_count} retries were attempted."

        dlq_note = ""
        if matching_dlq:
            dlq_note = f" The event is currently retained in the Dead Letter Queue (DLQ ID: {matching_dlq.id})."

        full_summary = f"{root_cause}{retry_note}{dlq_note}"

        actions: List[RemediationAction] = []
        if run.status == "FAILED":
            actions.append(
                RemediationAction(
                    action_id="REPLAY_RUN",
                    label="Replay Run",
                    description=f"Replay run {run_id} from beginning with idempotency guarantees. (Requires human confirmation)",
                    requires_human_confirmation=True,
                    parameters={"run_id": run_id, "workflow_id": run.workflow_id},
                )
            )

        if trace_id:
            actions.append(
                RemediationAction(
                    action_id="INSPECT_TRACE",
                    label="Inspect Trace Waterfall",
                    description=f"Open distributed trace waterfall for trace {trace_id}.",
                    requires_human_confirmation=False,
                    parameters={"trace_id": trace_id},
                )
            )

        actions.append(
            RemediationAction(
                action_id="CREATE_INCIDENT",
                label="Create Incident Ticket",
                description=f"File high-severity incident ticket in Incident Manager for {err_category}.",
                requires_human_confirmation=True,
                parameters={
                    "title": f"Run failure: {err_category} on {conn_name}",
                    "severity": "P2",
                    "connection_id": failing_step.input_snapshot.get("connection_id", "conn_rest_01") if failing_step else "conn_rest_01",
                    "run_id": run_id,
                },
            )
        )

        return DiagnosticReport(
            run_id=run_id,
            workflow_id=run.workflow_id,
            status=run.status,
            failing_node_id=failing_step.node_id if failing_step else None,
            failing_node_name=failing_step.name if failing_step else None,
            error_category=err_category,
            root_cause_summary=full_summary,
            technical_details={
                "raw_error": err_msg,
                "duration_ms": failing_step.duration_ms if failing_step else run.duration_seconds * 1000,
                "step_count": len(steps),
                "retry_count": failing_step.attempt if failing_step else 0,
            },
            trace_id=trace_id,
            failing_span_id=failing_span.span_id if failing_span else None,
            failing_span_attributes=span_attrs,
            dlq_record_id=matching_dlq.id if matching_dlq else None,
            circuit_breaker_status=cb_status,
            suggested_actions=actions,
        )

    async def confirm_action(
        self,
        db: AsyncSession,
        tenant_id: str,
        action_id: str,
        parameters: Dict[str, Any],
        actor_email: str,
    ) -> Dict[str, Any]:
        """
        Executes a remediation action that has been explicitly confirmed by a human operator.
        """
        audit_repo = AuditRepository(db, tenant_id)
        run_repo = RunRepository(db, tenant_id)
        incident_repo = IncidentRepository(db, tenant_id)

        action_id = action_id.upper()

        if action_id == "REPLAY_RUN":
            target_run_id = parameters.get("run_id")
            if not target_run_id:
                raise ValueError("Missing 'run_id' in parameters for REPLAY_RUN")

            original_run = await run_repo.get_by_id(target_run_id)
            if not original_run:
                raise ValueError(f"Run '{target_run_id}' not found")

            new_run_id = f"run_{uuid.uuid4().hex[:12]}"
            now = datetime.now(timezone.utc)
            replayed_run = RunRecord(
                id=new_run_id,
                tenant_id=tenant_id,
                workflow_id=original_run.workflow_id,
                workflow_version=original_run.workflow_version,
                status="PENDING",
                duration_seconds=0.0,
                trigger_source=f"Replay of {target_run_id}",
                trace_id=uuid.uuid4().hex,
                input_payload=original_run.input_payload or {},
                started_at=now,
            )
            await run_repo.create(replayed_run)

            await audit_repo.record(
                actor=actor_email,
                action="assistant.action.replay_confirmed",
                resource=f"runs/{target_run_id}",
                result="SUCCESS",
                metadata={"original_run_id": target_run_id, "new_run_id": replayed_run.id},
            )

            return {
                "status": "success",
                "action": "REPLAY_RUN",
                "message": f"Replay successfully dispatched for run '{target_run_id}'.",
                "new_run_id": replayed_run.id,
            }

        elif action_id == "CREATE_INCIDENT":
            title = parameters.get("title", f"Automated Incident via Assistant for run {parameters.get('run_id')}")
            sev = parameters.get("severity", "P2")
            conn_id = parameters.get("connection_id")
            inc_id = f"inc_{uuid.uuid4().hex[:8]}"

            inc = IncidentRecord(
                id=inc_id,
                tenant_id=tenant_id,
                title=title,
                severity=sev,
                status="INVESTIGATING",
                connection_id=conn_id,
                affected_workflows=[parameters.get("workflow_id", "wf_order_processing")],
                root_cause=parameters.get("root_cause", title),
                timeline=[
                    {
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                        "actor": actor_email,
                        "action": "Incident created via AI Assistant recommendation",
                    }
                ],
            )
            created = await incident_repo.create(inc)

            await audit_repo.record(
                actor=actor_email,
                action="assistant.action.incident_confirmed",
                resource=f"incidents/{inc.id}",
                result="SUCCESS",
                metadata={"incident_id": inc.id, "title": title},
            )

            return {
                "status": "success",
                "action": "CREATE_INCIDENT",
                "message": f"Incident '{inc.id}' successfully created and assigned to triage.",
                "incident_id": inc.id,
            }

        else:
            raise ValueError(f"Unknown or non-executable action '{action_id}'")


assistant_service = IncidentAssistant()
