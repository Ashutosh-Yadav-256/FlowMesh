"""
FlowMesh Demo Management API Router

Provides explicit control over sample demonstration data:
- POST /api/v1/demo/seed: Seeds realistic sample connections, workflows, and runs for client evaluations.
- POST /api/v1/demo/reset: Clears all demo data for a pristine clean production slate.
- GET /api/v1/demo/status: Returns whether the current workspace contains demo records.
"""

import uuid
from datetime import datetime, timezone
from typing import Dict, Any, List
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select, delete

from app.dependencies import DbSession, CurrentAuth
from app.repositories.tenant_scoped import (
    ConnectionRepository,
    ConnectionSecretRepository,
    WorkflowRepository,
    WorkflowVersionRepository,
    RunRepository,
    AuditRepository,
)
from app.models.tenant import ConnectionRecord, ConnectionSecret
from app.models.workflow import WorkflowRecord, WorkflowVersionRecord
from app.models.run import RunRecord, RunStepRecord
from app.models.incident import IncidentRecord
from flowmesh_auth.crypto import envelope_crypto
from flowmesh_auth.rbac import is_allowed

router = APIRouter(prefix="/api/v1/demo", tags=["Demo & Onboarding"])


class DemoStatusResponse(BaseModel):
    tenant_id: str
    is_demo_mode: bool
    connection_count: int
    workflow_count: int
    run_count: int


class DemoActionResponse(BaseModel):
    success: bool
    message: str
    tenant_id: str
    connections_created: int = 0
    workflows_created: int = 0
    runs_created: int = 0


CANONICAL_DEMO_CONNECTIONS = [
    {
        "id": "conn_pg_01",
        "name": "Orders DB",
        "type": "postgres",
        "status": "healthy",
        "agent_id": "agent-prod-01",
        "config": {"host": "10.0.4.12", "port": 5432, "database": "production_orders", "ssl_mode": "require"},
        "credentials": {"username": "order_svc", "password": "vault_pg_secret_pass_123"},
    },
    {
        "id": "conn_rest_01",
        "name": "Warehouse API",
        "type": "rest",
        "status": "healthy",
        "agent_id": "agent-prod-01",
        "config": {"base_url": "https://internal-warehouse.corp.local/v2", "timeout_seconds": 10},
        "credentials": {"token": "fm_tok_live_wh_98412"},
    },
    {
        "id": "conn_sap_01",
        "name": "Enterprise SAP ERP",
        "type": "sap",
        "status": "healthy",
        "agent_id": "agent-prod-01",
        "config": {"system_id": "PRD", "client": "100", "gateway_host": "10.0.8.5"},
        "credentials": {"client_cert": "cert_data_pem"},
    },
    {
        "id": "conn_redis_01",
        "name": "RediForge Cache & Lock",
        "type": "rediforge",
        "status": "healthy",
        "agent_id": None,
        "config": {"host": "localhost", "port": 6379, "tls_enabled": True},
        "credentials": {"auth_token": "rf_sec_token_9281"},
    },
    {
        "id": "conn_hook_01",
        "name": "Customer Webhook",
        "type": "webhook",
        "status": "healthy",
        "agent_id": None,
        "config": {"endpoint": "https://api.flowmesh.dev/v1/hooks/cust_982", "method": "POST"},
        "credentials": {"signing_secret": "whsec_live_9201940"},
    },
]

CANONICAL_DEMO_WORKFLOWS = [
    {
        "id": "wf_order_processing",
        "name": "Order Processing",
        "status": "active",
        "version": 3,
        "trigger_type": "webhook",
        "definition": {
            "schema_version": 1,
            "name": "Order Processing",
            "description": "End-to-end processing: Webhook Order -> Validate -> Customer Lookup -> PostgreSQL -> Warehouse Notify -> Audit",
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
        },
    },
    {
        "id": "wf_customer_sync",
        "name": "Customer Sync",
        "status": "active",
        "version": 1,
        "trigger_type": "webhook",
        "definition": {
            "schema_version": 1,
            "name": "Customer Sync",
            "description": "Sync customer updates across CRM and PostgreSQL",
            "trigger": {"type": "webhook", "config": {"path": "/customers"}},
            "nodes": [
                {"id": "n1", "type": "trigger.webhook", "name": "Customer Webhook", "config": {}},
                {"id": "n2", "type": "transform", "name": "Normalize Customer", "config": {}},
                {"id": "n3", "type": "action.db_write", "name": "Sync DB", "connection_id": "conn_pg_01", "config": {}},
                {"id": "n4", "type": "audit.log", "name": "Audit", "config": {}},
            ],
            "edges": [
                {"source": "n1", "target": "n2"},
                {"source": "n2", "target": "n3"},
                {"source": "n3", "target": "n4"},
            ],
        },
    },
    {
        "id": "wf_payment_reconciliation",
        "name": "Daily Payment Reconciliation",
        "status": "active",
        "version": 2,
        "trigger_type": "event",
        "definition": {
            "schema_version": 1,
            "name": "Daily Payment Reconciliation",
            "description": "Nightly batch matching between Stripe charges and bank ledger",
            "trigger": {"type": "event", "config": {"event_type": "reconciliation.scheduled"}},
            "nodes": [
                {"id": "i1", "type": "trigger.event", "name": "Reconciliation Schedule", "config": {}},
                {"id": "i2", "type": "action.db_write", "name": "Update Cache", "connection_id": "conn_redis_01", "config": {}},
                {"id": "i3", "type": "audit.log", "name": "Emit Audit Log", "config": {}},
            ],
            "edges": [
                {"source": "i1", "target": "i2"},
                {"source": "i2", "target": "i3"},
            ],
        },
    },
]

CANONICAL_DEMO_RUNS = [
    {
        "id": "RUN-92831",
        "workflow_id": "wf_order_processing",
        "version": 3,
        "status": "SUCCESS",
        "duration_seconds": 2.84,
        "trigger_source": "SAP Event #evt_98231",
        "trace_id": "4bf92f3577b34da6a3ce929d0e0e4736",
        "input_payload": {"order_id": "ORD-55410", "customer_id": "CUST-9821", "amount": 1420.50},
        "output_payload": {"status": "dispatched", "shipment_tracking": "TRK-98214-WH"},
        "steps": [
            {"step_id": "s1", "name": "SAP Order Event Ingress", "node_id": "node_1", "node_type": "trigger.event", "status": "SUCCESS", "attempt": 1, "duration_ms": 42.1, "input": {"event": "order.created"}, "output": {"order_id": "ORD-55410"}},
            {"step_id": "s2", "name": "Schema Validation", "node_id": "node_2", "node_type": "control.condition", "status": "SUCCESS", "attempt": 1, "duration_ms": 18.4, "input": {"schema": "order_v2"}, "output": {"valid": True}},
            {"step_id": "s3", "name": "Customer Lookup (PostgreSQL)", "node_id": "node_3", "node_type": "action.db_query", "status": "SUCCESS", "attempt": 1, "duration_ms": 120.5, "input": {"customer_id": "CUST-9821"}, "output": {"tier": "ENTERPRISE_GOLD"}},
            {"step_id": "s4", "name": "Update Orders DB (PostgreSQL)", "node_id": "node_4", "node_type": "action.db_write", "status": "SUCCESS", "attempt": 1, "duration_ms": 210.2, "input": {"table": "orders"}, "output": {"rows_affected": 1}},
            {"step_id": "s5", "name": "Notify Warehouse API (REST)", "node_id": "node_5", "node_type": "action.http", "status": "SUCCESS", "attempt": 1, "duration_ms": 850.3, "input": {"endpoint": "/shipments"}, "output": {"tracking_number": "TRK-98214-WH"}},
            {"step_id": "s6", "name": "Audit Event (Immutable Log)", "node_id": "node_6", "node_type": "audit.log", "status": "SUCCESS", "attempt": 1, "duration_ms": 45.0, "input": {"action": "order_processed"}, "output": {"audit_id": "aud_99214"}},
        ],
    },
    {
        "id": "RUN-92830",
        "workflow_id": "wf_order_processing",
        "version": 3,
        "status": "FAILED",
        "duration_seconds": 4.12,
        "trigger_source": "SAP Event #evt_98233",
        "trace_id": "8cf92f3577b34da6a3ce929d0e0e9981",
        "input_payload": {"order_id": "ORD-55409", "customer_id": "CUST-1002"},
        "output_payload": None,
        "steps": [
            {"step_id": "f1", "name": "SAP Order Event Ingress", "node_id": "node_1", "node_type": "trigger.event", "status": "SUCCESS", "attempt": 1, "duration_ms": 40.0, "input": {}, "output": {"order_id": "ORD-55409"}},
            {"step_id": "f2", "name": "Schema Validation", "node_id": "node_2", "node_type": "control.condition", "status": "SUCCESS", "attempt": 1, "duration_ms": 15.0, "input": {}, "output": {"valid": True}},
            {"step_id": "f3", "name": "Customer Lookup", "node_id": "node_3", "node_type": "action.db_query", "status": "SUCCESS", "attempt": 1, "duration_ms": 115.0, "input": {}, "output": {"customer": "CUST-1002"}},
            {"step_id": "f4", "name": "Update Orders DB", "node_id": "node_4", "node_type": "action.db_write", "status": "SUCCESS", "attempt": 1, "duration_ms": 205.0, "input": {}, "output": {"updated": True}},
            {"step_id": "f5", "name": "Notify Warehouse API", "node_id": "node_5", "node_type": "action.http", "status": "FAILED", "attempt": 3, "duration_ms": 3000.0, "input": {"endpoint": "/shipments"}, "output": None, "error": "HTTP 503 Service Unavailable: Warehouse API Gateway Down"},
        ],
    },
]


@router.get("/status", response_model=DemoStatusResponse)
async def get_demo_status(
    db: DbSession,
    auth: CurrentAuth,
) -> DemoStatusResponse:
    """Check whether the active tenant has demo records or is in fresh clean mode."""
    conn_repo = ConnectionRepository(db, auth.tenant_id)
    wf_repo = WorkflowRepository(db, auth.tenant_id)
    run_repo = RunRepository(db, auth.tenant_id)

    conn_count = await conn_repo.count()
    wf_count = await wf_repo.count()
    run_count = await run_repo.count()

    return DemoStatusResponse(
        tenant_id=auth.tenant_id,
        is_demo_mode=(conn_count > 0 or wf_count > 0 or run_count > 0),
        connection_count=conn_count,
        workflow_count=wf_count,
        run_count=run_count,
    )


@router.post("/seed", response_model=DemoActionResponse)
async def seed_demo_data(
    db: DbSession,
    auth: CurrentAuth,
) -> DemoActionResponse:
    """One-click seed for client demonstrations, pitches, and walkthroughs."""
    conn_repo = ConnectionRepository(db, auth.tenant_id)
    secret_repo = ConnectionSecretRepository(db, auth.tenant_id)
    wf_repo = WorkflowRepository(db, auth.tenant_id)
    wf_version_repo = WorkflowVersionRepository(db, auth.tenant_id)
    run_repo = RunRepository(db, auth.tenant_id)
    audit_repo = AuditRepository(db, auth.tenant_id)

    now = datetime.now(timezone.utc)

    conns_created = 0
    conn_id_map = {}
    for sc in CANONICAL_DEMO_CONNECTIONS:
        raw_id = sc["id"]
        conn_id = raw_id if auth.tenant_id == "tenant_acme" else f"{raw_id}_{auth.tenant_id}"
        conn_id_map[raw_id] = conn_id
        existing = await conn_repo.get_by_id(conn_id)
        if not existing:
            conn = ConnectionRecord(
                id=conn_id,
                tenant_id=auth.tenant_id,
                name=sc["name"],
                type=sc["type"],
                status=sc["status"],
                agent_id=sc["agent_id"],
                config_json=sc["config"],
                created_at=now,
            )
            await conn_repo.create(conn)

            if sc.get("credentials"):
                dek = envelope_crypto.generate_dek()
                wrapped_dek = envelope_crypto.wrap_dek(dek, auth.tenant_id)
                ciphertext = envelope_crypto.encrypt_secret(dek, sc["credentials"], conn_id)
                sec = ConnectionSecret(
                    id=f"sec_{uuid.uuid4().hex[:12]}",
                    connection_id=conn_id,
                    tenant_id=auth.tenant_id,
                    ciphertext=ciphertext,
                    wrapped_dek=wrapped_dek,
                    dek_id=f"dek_{uuid.uuid4().hex[:8]}",
                    version=1,
                    created_at=now,
                )
                await secret_repo.create(sec)
            conns_created += 1

    wfs_created = 0
    wf_id_map = {}
    for item in CANONICAL_DEMO_WORKFLOWS:
        raw_wf_id = item["id"]
        wf_id = raw_wf_id if auth.tenant_id == "tenant_acme" else f"{raw_wf_id}_{auth.tenant_id}"
        wf_id_map[raw_wf_id] = wf_id
        existing_wf = await wf_repo.get_by_id(wf_id)
        if not existing_wf:
            import copy
            def_json = copy.deepcopy(item["definition"])
            for node in def_json.get("nodes", []):
                if "connection_id" in node and node["connection_id"] in conn_id_map:
                    node["connection_id"] = conn_id_map[node["connection_id"]]

            wf = WorkflowRecord(
                id=wf_id,
                tenant_id=auth.tenant_id,
                name=item["name"],
                description=def_json["description"],
                status=item["status"],
                version=item["version"],
                trigger_type=item["trigger_type"],
                definition_json=def_json,
                created_at=now,
                updated_at=now,
            )
            await wf_repo.create(wf)

            wf_version = WorkflowVersionRecord(
                id=f"wfv_{wf_id}_v{item['version']}",
                workflow_id=wf_id,
                tenant_id=auth.tenant_id,
                version=item["version"],
                definition_json=def_json,
                deployed_by=auth.email,
                deployed_at=now,
                changelog=f"Deployed canonical {item['name']} v{item['version']}",
            )
            await wf_version_repo.create(wf_version)
            wfs_created += 1

    runs_created = 0
    for item in CANONICAL_DEMO_RUNS:
        raw_run_id = item["id"]
        run_id = raw_run_id if auth.tenant_id == "tenant_acme" else f"{raw_run_id}_{auth.tenant_id}"
        target_wf_id = wf_id_map.get(item["workflow_id"], item["workflow_id"])
        existing_run = await run_repo.get_by_id(run_id)
        if not existing_run:
            run = RunRecord(
                id=run_id,
                tenant_id=auth.tenant_id,
                workflow_id=target_wf_id,
                workflow_version=item["version"],
                status=item["status"],
                duration_seconds=item["duration_seconds"],
                trigger_source=item["trigger_source"],
                trace_id=item["trace_id"],
                input_payload=item["input_payload"],
                output_payload=item["output_payload"],
                started_at=now,
                finished_at=now,
            )
            await run_repo.create(run)

            for s in item["steps"]:
                step = RunStepRecord(
                    id=f"step_{run_id}_{s['step_id']}",
                    run_id=run_id,
                    tenant_id=auth.tenant_id,
                    node_id=s["node_id"],
                    name=s["name"],
                    node_type=s.get("node_type", "action"),
                    status=s["status"],
                    attempt=s["attempt"],
                    duration_ms=s["duration_ms"],
                    started_at=now,
                    finished_at=now,
                    input_snapshot=s.get("input", {}),
                    output_snapshot=s.get("output"),
                    error=s.get("error"),
                )
                await run_repo.record_step(step)
            runs_created += 1

    await audit_repo.record(
        actor=auth.email,
        action="demo.seed",
        resource=f"tenants/{auth.tenant_id}/demo",
        result="SUCCESS",
        metadata={
            "connections": conns_created,
            "workflows": wfs_created,
            "runs": runs_created,
        },
    )

    from app.routers.search import sync_tenant_search_index
    await sync_tenant_search_index(db, auth.tenant_id)

    return DemoActionResponse(
        success=True,
        message=f"Demo workspace initialized with {conns_created} connections, {wfs_created} workflows, and {runs_created} runs.",
        tenant_id=auth.tenant_id,
        connections_created=conns_created,
        workflows_created=wfs_created,
        runs_created=runs_created,
    )


@router.post("/reset", response_model=DemoActionResponse)
async def reset_demo_data(
    db: DbSession,
    auth: CurrentAuth,
) -> DemoActionResponse:
    """Clears all records for the current active tenant, leaving a 100% clean production slate."""
    conn_repo = ConnectionRepository(db, auth.tenant_id)
    secret_repo = ConnectionSecretRepository(db, auth.tenant_id)
    wf_repo = WorkflowRepository(db, auth.tenant_id)
    wf_version_repo = WorkflowVersionRepository(db, auth.tenant_id)
    run_repo = RunRepository(db, auth.tenant_id)
    audit_repo = AuditRepository(db, auth.tenant_id)

    await db.execute(delete(RunStepRecord).where(RunStepRecord.tenant_id == auth.tenant_id))
    runs = await run_repo.list_all()
    for r in runs:
        await run_repo.delete(r.id)

    await db.execute(delete(WorkflowVersionRecord).where(WorkflowVersionRecord.tenant_id == auth.tenant_id))
    wfs = await wf_repo.list_all()
    for w in wfs:
        await wf_repo.delete(w.id)

    await db.execute(delete(ConnectionSecret).where(ConnectionSecret.tenant_id == auth.tenant_id))
    conns = await conn_repo.list_all()
    for c in conns:
        await conn_repo.delete(c.id)

    await db.execute(delete(IncidentRecord).where(IncidentRecord.tenant_id == auth.tenant_id))
    await db.commit()

    from flowmesh_search.engine import get_search_engine
    get_search_engine().clear_tenant(auth.tenant_id)

    await audit_repo.record(
        actor=auth.email,
        action="demo.reset",
        resource=f"tenants/{auth.tenant_id}",
        result="SUCCESS",
        metadata={"status": "clean_production_slate"},
    )

    return DemoActionResponse(
        success=True,
        message="Workspace reset successfully to clean production state (0 records).",
        tenant_id=auth.tenant_id,
        connections_created=0,
        workflows_created=0,
        runs_created=0,
    )
