"""
Unit Tests for Human Approval Gates & Extended Node Types

Tests:
1. Execution halts and parks in WAITING_APPROVAL at action.approval node.
2. Step and Run state are persisted in SQLite/PostgreSQL with WAITING_APPROVAL.
3. Approving via engine.resume_approval() resumes downstream execution to SUCCESS.
4. Rejecting via engine.resume_approval() marks step and run as REJECTED.
5. Concurrent branch execution via control.parallel node.
6. Execution pausing via control.delay and dispatching via action.event_publish & action.notification.
7. API endpoints POST /api/v1/runs/{id}/approve and /reject.
"""

import sys
import uuid
import pytest
from httpx import AsyncClient, ASGITransport

sys.path.insert(0, "apps/api")
sys.path.insert(0, "packages/auth")
sys.path.insert(0, "services/workflow-engine")
from app.main import app
from app.database import AsyncSessionLocal, engine as db_engine, Base
from app.models.tenant import Tenant
from app.models.workflow import WorkflowRecord, WorkflowVersionRecord
from app.repositories.tenant_scoped import WorkflowRepository, RunRepository
from app.services.auth_service import create_access_token
from flowmesh_workflow.schema import WorkflowDefinition
from flowmesh_engine.engine import WorkflowEngine
import pytest_asyncio


@pytest_asyncio.fixture(autouse=True)
async def init_tables():
    async with db_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield


@pytest.fixture
async def setup_tenants():
    async with AsyncSessionLocal() as db:
        existing = await db.get(Tenant, "tenant_acme")
        if not existing:
            db.add(Tenant(id="tenant_acme", name="Acme Corp", slug="acme"))
            await db.commit()


def make_auth_header(tenant_id: str = "tenant_acme", role: str = "operator") -> dict:
    token = create_access_token(
        user_id=f"user_{role}",
        tenant_id=tenant_id,
        role=role,
        email=f"{role}@acme.com",
    )
    return {"Authorization": f"Bearer {token}", "X-Tenant-ID": tenant_id}


@pytest.mark.asyncio
async def test_human_approval_gate_lifecycle(setup_tenants):
    async with AsyncSessionLocal() as db:
        tenant_id = "tenant_acme"
        wf_repo = WorkflowRepository(db, tenant_id)

        wf_def = WorkflowDefinition(
            name="Expense Approval DAG",
            schema_version=1,
            trigger={"type": "webhook", "config": {"path": "/expenses"}},
            nodes=[
                {"id": "n1", "type": "trigger.webhook", "name": "Expense Ingress", "config": {}},
                {"id": "n2", "type": "action.approval", "name": "Manager Review Gate", "config": {"threshold": 5000}},
                {"id": "n3", "type": "action.notification", "name": "Notify Finance", "config": {"message": "Expense approved for {{ input.amount }}"}},
                {"id": "n4", "type": "audit.log", "name": "Audit", "config": {}},
            ],
            edges=[
                {"source": "n1", "target": "n2"},
                {"source": "n2", "target": "n3"},
                {"source": "n3", "target": "n4"},
            ],
        )

        wf_id = f"wf_{uuid.uuid4().hex[:8]}"
        wf_def.id = wf_id
        wf_rec = WorkflowRecord(
            id=wf_id,
            tenant_id=tenant_id,
            name=wf_def.name,
            description="Expense pipeline with approval gate",
            status="active",
            version=1,
            trigger_type="webhook",
            definition_json=wf_def.model_dump(),
        )
        await wf_repo.create(wf_rec)

        engine = WorkflowEngine(db, tenant_id)
        run_id = f"RUN-APPR-{uuid.uuid4().hex[:6].upper()}"

        run = await engine.execute(
            workflow_def=wf_def,
            run_id=run_id,
            input_payload={"expense_id": "EXP-9901", "amount": 8500},
        )

        assert run.status == "WAITING_APPROVAL"
        appr_step = next((s for s in run.steps if s.node_id == "n2"), None)
        assert appr_step is not None
        assert appr_step.status == "WAITING_APPROVAL"

        downstream_steps = [s for s in run.steps if s.node_id in ("n3", "n4")]
        assert len(downstream_steps) == 0

        resumed_run = await engine.resume_approval(
            run_id=run_id,
            approved=True,
            approver_email="finance_director@acme.com",
            comment="Approved budget expenditure",
        )

        assert resumed_run.status == "SUCCESS"
        appr_step_updated = next(s for s in resumed_run.steps if s.node_id == "n2")
        assert appr_step_updated.status == "SUCCESS"
        assert appr_step_updated.output_snapshot["approved"] is True
        assert appr_step_updated.output_snapshot["approver"] == "finance_director@acme.com"

        n3_step = next((s for s in resumed_run.steps if s.node_id == "n3"), None)
        assert n3_step is not None
        assert n3_step.status == "SUCCESS"
        assert n3_step.output_snapshot["delivered"] is True


@pytest.mark.asyncio
async def test_human_approval_gate_rejection(setup_tenants):
    async with AsyncSessionLocal() as db:
        tenant_id = "tenant_acme"
        wf_repo = WorkflowRepository(db, tenant_id)

        wf_def = WorkflowDefinition(
            name="Sensitive Export DAG",
            schema_version=1,
            trigger={"type": "webhook", "config": {}},
            nodes=[
                {"id": "t1", "type": "trigger.webhook", "name": "Export Request", "config": {}},
                {"id": "gate", "type": "action.approval", "name": "Security Signoff", "config": {}},
                {"id": "act", "type": "action.notification", "name": "Send Data", "config": {}},
            ],
            edges=[
                {"source": "t1", "target": "gate"},
                {"source": "gate", "target": "act"},
            ],
        )

        wf_id = f"wf_{uuid.uuid4().hex[:8]}"
        wf_def.id = wf_id
        wf_rec = WorkflowRecord(
            id=wf_id,
            tenant_id=tenant_id,
            name=wf_def.name,
            status="active",
            version=1,
            trigger_type="webhook",
            definition_json=wf_def.model_dump(),
        )
        await wf_repo.create(wf_rec)

        engine = WorkflowEngine(db, tenant_id)
        run_id = f"RUN-REJ-{uuid.uuid4().hex[:6].upper()}"

        run = await engine.execute(
            workflow_def=wf_def,
            run_id=run_id,
            input_payload={"dataset": "user_pii"},
        )
        assert run.status == "WAITING_APPROVAL"

        rejected_run = await engine.resume_approval(
            run_id=run_id,
            approved=False,
            approver_email="cso@acme.com",
            comment="Unauthorized PII export",
        )

        assert rejected_run.status == "REJECTED"
        assert "Rejected by cso@acme.com" in rejected_run.error
        gate_step = next(s for s in rejected_run.steps if s.node_id == "gate")
        assert gate_step.status == "REJECTED"

        act_step = next((s for s in rejected_run.steps if s.node_id == "act"), None)
        assert act_step is None


@pytest.mark.asyncio
async def test_extended_node_execution(setup_tenants):
    async with AsyncSessionLocal() as db:
        tenant_id = "tenant_acme"
        wf_repo = WorkflowRepository(db, tenant_id)

        wf_def = WorkflowDefinition(
            name="Extended Nodes Pipeline",
            schema_version=1,
            trigger={"type": "event", "config": {"event_type": "batch.ready"}},
            nodes=[
                {"id": "n1", "type": "trigger.event", "name": "Event Ingress", "config": {}},
                {"id": "n2", "type": "control.delay", "name": "Backpressure Delay", "config": {"seconds": 0.05}},
                {
                    "id": "n3",
                    "type": "control.parallel",
                    "name": "Sync External Systems",
                    "config": {
                        "branches": [
                            {"name": "branch_sap", "output": {"sap_synced": True}},
                            {"name": "branch_salesforce", "output": {"crm_synced": True}},
                        ]
                    },
                },
                {"id": "n4", "type": "action.event_publish", "name": "Emit Routed Event", "config": {"topic": "orders.synced"}},
                {"id": "n5", "type": "action.notification", "name": "Alert Teams", "config": {"channel": "teams", "message": "Batch complete"}},
            ],
            edges=[
                {"source": "n1", "target": "n2"},
                {"source": "n2", "target": "n3"},
                {"source": "n3", "target": "n4"},
                {"source": "n4", "target": "n5"},
            ],
        )

        wf_id = f"wf_{uuid.uuid4().hex[:8]}"
        wf_rec = WorkflowRecord(
            id=wf_id,
            tenant_id=tenant_id,
            name=wf_def.name,
            status="active",
            version=1,
            trigger_type="event",
            definition_json=wf_def.model_dump(),
        )
        await wf_repo.create(wf_rec)

        engine = WorkflowEngine(db, tenant_id)
        run_id = f"RUN-EXT-{uuid.uuid4().hex[:6].upper()}"

        run = await engine.execute(
            workflow_def=wf_def,
            run_id=run_id,
            input_payload={"batch_id": "B-9921"},
        )

        assert run.status == "SUCCESS"
        steps_by_node = {s.node_id: s for s in run.steps}

        assert steps_by_node["n2"].status == "SUCCESS"
        assert steps_by_node["n2"].output_snapshot["delayed_seconds"] == 0.05

        assert steps_by_node["n3"].status == "SUCCESS"
        assert steps_by_node["n3"].output_snapshot["parallel_executed"] is True
        assert steps_by_node["n3"].output_snapshot["branch_count"] == 2

        assert steps_by_node["n4"].status == "SUCCESS"
        assert steps_by_node["n4"].output_snapshot["published"] is True
        assert steps_by_node["n4"].output_snapshot["topic"] == "orders.synced"

        assert steps_by_node["n5"].status == "SUCCESS"
        assert steps_by_node["n5"].output_snapshot["delivered"] is True
        assert steps_by_node["n5"].output_snapshot["channel"] == "teams"


@pytest.mark.asyncio
async def test_approval_api_endpoints(setup_tenants):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        dev_headers = make_auth_header("tenant_acme", "developer")
        op_headers = make_auth_header("tenant_acme", "operator")

        wf_payload = {
            "name": "API Approval Pipeline",
            "schema_version": 1,
            "trigger": {"type": "webhook", "config": {}},
            "nodes": [
                {"id": "t1", "type": "trigger.webhook", "name": "Start", "config": {}},
                {"id": "appr", "type": "action.approval", "name": "Gate", "config": {}},
                {"id": "fin", "type": "audit.log", "name": "End", "config": {}},
            ],
            "edges": [
                {"source": "t1", "target": "appr"},
                {"source": "appr", "target": "fin"},
            ],
        }

        wf_res = await ac.post("/api/v1/workflows", json=wf_payload, headers=dev_headers)
        assert wf_res.status_code == 201
        wf_id = wf_res.json()["id"]

        await ac.post(f"/api/v1/workflows/{wf_id}/deploy", json={"changelog": "deploy"}, headers=dev_headers)

        async with AsyncSessionLocal() as db:
            engine = WorkflowEngine(db, "tenant_acme")
            run_id = f"RUN-API-APPR-{uuid.uuid4().hex[:6].upper()}"
            wf_payload["id"] = wf_id
            await engine.execute(
                workflow_def=WorkflowDefinition(**wf_payload),
                run_id=run_id,
                input_payload={"item": "desk"},
            )

        run_res = await ac.get(f"/api/v1/runs/{run_id}", headers=op_headers)
        assert run_res.status_code == 200
        assert run_res.json()["status"] == "WAITING_APPROVAL"

        appr_res = await ac.post(
            f"/api/v1/runs/{run_id}/approve",
            json={"comment": "Approved via Webhook Review"},
            headers=op_headers,
        )
        assert appr_res.status_code == 200, appr_res.text
        updated_run = appr_res.json()
        assert updated_run["status"] == "SUCCESS"
        appr_step = next(s for s in updated_run["steps"] if s["node_id"] == "appr")
        assert appr_step["status"] == "SUCCESS"
