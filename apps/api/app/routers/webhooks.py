"""
FlowMesh Webhook Ingress Router

Accepts external webhooks and executes matching workflow DAGs:
- Idempotency key deduplication (ADR-0004).
- OpenTelemetry trace ID propagation.
- Event publishing to NATS JetStream event bus.
- Direct execution via resumable WorkflowEngine.
"""

import uuid
from typing import Dict, Any, Optional
from fastapi import APIRouter, Request, Header, HTTPException, status
from pydantic import BaseModel

from app.database import AsyncSessionLocal
from app.dependencies import DbSession
from app.repositories.tenant_scoped import (
    WorkflowRepository,
    RunRepository,
)
from flowmesh_workflow.schema import WorkflowDefinition
from flowmesh_engine.engine import WorkflowEngine
from flowmesh_events.event_bus import event_bus, EventMessage

router = APIRouter(prefix="/api/v1/webhooks", tags=["Webhook Ingress"])


class WebhookIngressResponse(BaseModel):
    success: bool
    run_id: str
    status: str
    trace_id: str
    duration_seconds: float
    output: Optional[Dict[str, Any]] = None


_DEFAULT_DEMO_WORKFLOW = {
    "schema_version": 1,
    "name": "Order Ingress Processing",
    "description": "Auto-processes webhook order -> customer lookup -> warehouse notify -> audit",
    "trigger": {"type": "webhook", "config": {"path": "/orders"}},
    "nodes": [
        {"id": "node_1", "type": "trigger.webhook", "name": "Webhook Order Ingress", "config": {}},
        {"id": "node_2", "type": "control.condition", "name": "Validate Order Payload", "config": {"schema_ref": "order_v1"}},
        {"id": "node_3", "type": "action.db_query", "name": "Customer Lookup", "connection_id": "conn_pg_01", "config": {"sql": "SELECT * FROM customers WHERE id = :customer_id"}},
        {"id": "node_4", "type": "action.http", "name": "Notify Warehouse", "connection_id": "conn_rest_01", "config": {"method": "POST", "endpoint": "/shipments"}},
        {"id": "node_5", "type": "audit.log", "name": "Audit Order Record", "config": {"action": "order.dispatched"}},
    ],
    "edges": [
        {"source": "node_1", "target": "node_2"},
        {"source": "node_2", "target": "node_3"},
        {"source": "node_3", "target": "node_4"},
        {"source": "node_4", "target": "node_5"},
    ],
}


@router.post("/{tenant_id}/{webhook_path:path}", response_model=WebhookIngressResponse, status_code=status.HTTP_200_OK)
async def handle_webhook_ingress(
    tenant_id: str,
    webhook_path: str,
    request: Request,
    db: DbSession,
    x_trace_id: Optional[str] = Header(None, alias="X-Trace-ID"),
    x_idempotency_key: Optional[str] = Header(None, alias="Idempotency-Key"),
) -> WebhookIngressResponse:
    """
    Ingests an incoming webhook, publishes to NATS JetStream, and executes matching workflow.
    """
    trace_id = x_trace_id or uuid.uuid4().hex
    clean_path = "/" + webhook_path.strip("/")

    try:
        payload = await request.json()
    except Exception:
        payload = {}

    run_repo = RunRepository(db, tenant_id)
    wf_repo = WorkflowRepository(db, tenant_id)

    if x_idempotency_key:
        existing = await run_repo.get_by_idempotency_key(x_idempotency_key)
        if existing:
            return WebhookIngressResponse(
                success=existing.status == "SUCCESS",
                run_id=existing.id,
                status=existing.status,
                trace_id=existing.trace_id,
                duration_seconds=existing.duration_seconds,
                output=existing.output_payload,
            )

    event = EventMessage(
        tenant_id=tenant_id,
        subject=f"events.{tenant_id}.webhook",
        type="webhook.received",
        source=f"webhook:{clean_path}",
        trace_id=trace_id,
        idempotency_key=x_idempotency_key,
        payload=payload,
    )
    await event_bus.publish(event.subject, event)

    wf = await wf_repo.get_by_trigger_path(clean_path)
    if not wf:
        from app.models.workflow import WorkflowRecord
        wf = WorkflowRecord(
            id=f"wf_{uuid.uuid4().hex[:8]}",
            tenant_id=tenant_id,
            name="Order Ingress Processing",
            description="Auto-created webhook processing workflow",
            status="active",
            version=1,
            trigger_type="webhook",
            definition_json=_DEFAULT_DEMO_WORKFLOW,
        )
        await wf_repo.create(wf)

    workflow_def = WorkflowDefinition(**wf.definition_json)
    run_id = f"RUN-{uuid.uuid4().hex[:6].upper()}"

    engine = WorkflowEngine(db, tenant_id)
    run = await engine.execute(
        workflow_def=workflow_def,
        run_id=run_id,
        input_payload=payload,
        trace_id=trace_id,
        trigger_source=f"webhook:{clean_path}",
        idempotency_key=x_idempotency_key,
    )

    return WebhookIngressResponse(
        success=run.status == "SUCCESS",
        run_id=run.id,
        status=run.status,
        trace_id=trace_id,
        duration_seconds=run.duration_seconds,
        output=run.output_payload,
    )
