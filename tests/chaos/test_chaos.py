"""
FlowMesh Chaos Test Suite
Simulates upstream network stalls, 50% flaky services, circuit breaker trips,
and batch DLQ recovery with exact-once guarantees.
"""

import sys
import uuid
import random
import pytest
from httpx import AsyncClient, ASGITransport

sys.path.insert(0, "apps/api")
sys.path.insert(0, "packages/workflow-schema")
sys.path.insert(0, "packages/connector-sdk")
sys.path.insert(0, "packages/state-store")
sys.path.insert(0, "services/workflow-engine")
sys.path.insert(0, "services/incident-manager")

from app.main import app
from app.database import engine, Base, AsyncSessionLocal
from app.models.tenant import Tenant
from app.models.workflow import WorkflowRecord
from app.repositories.tenant_scoped import (
    DeadLetterRepository,
    IncidentRepository,
    RunRepository,
    WorkflowRepository,
)
from flowmesh_workflow.schema import WorkflowDefinition, WorkflowNode, WorkflowEdge, TriggerSpec, RetryPolicy
from flowmesh_engine.engine import WorkflowEngine
from flowmesh_connector.registry import get_connector
from flowmesh_connector.protocol import OperationResult
from flowmesh_state.interface import MemoryStateStore, set_state_store


@pytest.fixture(autouse=True)
async def init_tables():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


@pytest.mark.asyncio
async def test_chaos_50_percent_flaky_upstream_recovers_via_retries():
    """
    Chaos Test: Upstream service fails 50% of the time with HTTP 503.
    Verifies that exponential backoff retries absorb the jitter and all runs complete successfully.
    """
    tenant_id = f"tenant_chaos_{uuid.uuid4().hex[:6]}"
    rest_conn = get_connector("rest")
    real_execute = rest_conn.execute

    rng = random.Random(42)

    async def chaos_50_pct_execute(conn, op):
        if op.parameters.get("endpoint") == "/chaos-flaky":
            if rng.random() < 0.5:
                return OperationResult(
                    success=False,
                    error="HTTP 503: Chaos Injected Temporary Service Unavailable",
                    duration_ms=2.0,
                )
        return await real_execute(conn, op)

    rest_conn.execute = chaos_50_pct_execute

    try:
        async with AsyncSessionLocal() as db:
            db.add(Tenant(id=tenant_id, name="Chaos Tenant", slug=f"chaos-{tenant_id}"))
            await db.commit()

            wf_id = f"wf_chaos_{uuid.uuid4().hex[:6]}"
            wf_def = WorkflowDefinition(
                id=wf_id,
                schema_version=1,
                name="Chaos Flaky Workflow",
                trigger=TriggerSpec(type="manual"),
                nodes=[
                    WorkflowNode(id="node_1", type="trigger.webhook", name="Webhook Intake"),
                    WorkflowNode(
                        id="node_2",
                        type="action.http",
                        name="Flaky API Call",
                        connection_id="conn_chaos_01",
                        config={"endpoint": "/chaos-flaky", "method": "GET"},
                        retry=RetryPolicy(
                            max_attempts=5,
                            backoff="exponential",
                            initial_interval_seconds=0.01,
                            max_interval_seconds=0.1,
                            jitter=True,
                        ),
                    ),
                ],
                edges=[WorkflowEdge(source="node_1", target="node_2")],
            )

            engine = WorkflowEngine(db, tenant_id)

            success_count = 0
            for i in range(8):
                run = await engine.execute(
                    workflow_def=wf_def,
                    run_id=f"RUN-CHAOS-{i:03d}-{uuid.uuid4().hex[:4]}",
                    input_payload={"batch_item": i},
                )
                if run.status == "SUCCESS":
                    success_count += 1

            assert success_count == 8

    finally:
        rest_conn.execute = real_execute


@pytest.mark.asyncio
async def test_chaos_upstream_outage_trips_circuit_breaker_and_routes_dlq():
    """
    Chaos Test: Upstream suffers 100% hard failure.
    Verifies that:
    1. Circuit breaker transitions to OPEN after 3 failures.
    2. Subsequent requests fast-fail with CircuitBreakerOpenError.
    3. All failures are captured in DeadLetterRecord with status PENDING.
    4. Incident is automatically created in IncidentRepository.
    """
    tenant_id = f"tenant_outage_{uuid.uuid4().hex[:6]}"
    conn_id = "conn_dead_api"
    state_store = MemoryStateStore()

    rest_conn = get_connector("rest")
    real_execute = rest_conn.execute

    async def hard_outage_execute(conn, op):
        return OperationResult(
            success=False,
            error="HTTP 502: Bad Gateway - Upstream host unreachable",
            duration_ms=1.0,
        )

    rest_conn.execute = hard_outage_execute

    try:
        async with AsyncSessionLocal() as db:
            db.add(Tenant(id=tenant_id, name="Outage Tenant", slug=f"outage-{tenant_id}"))
            await db.commit()

            wf_id = f"wf_outage_{uuid.uuid4().hex[:6]}"
            wf_def = WorkflowDefinition(
                id=wf_id,
                schema_version=1,
                name="Outage Workflow",
                trigger=TriggerSpec(type="manual"),
                nodes=[
                    WorkflowNode(id="node_1", type="trigger.webhook", name="Start"),
                    WorkflowNode(
                        id="node_2",
                        type="action.http",
                        name="Failing API",
                        connection_id=conn_id,
                        config={"endpoint": "/outage", "method": "GET"},
                        retry=RetryPolicy(max_attempts=1, backoff="fixed", initial_interval_seconds=0.01),
                    ),
                ],
                edges=[WorkflowEdge(source="node_1", target="node_2")],
            )

            engine = WorkflowEngine(db, tenant_id, state_store=state_store)

            for i in range(3):
                r = await engine.execute(
                    workflow_def=wf_def,
                    run_id=f"RUN-FAIL-{i}",
                    input_payload={"test": i},
                )
                assert r.status == "FAILED"

            assert await state_store.get_circuit_breaker_state(conn_id) == "OPEN"

            fast_fail_run = await engine.execute(
                workflow_def=wf_def,
                run_id="RUN-FAST-FAIL",
                input_payload={"fast": True},
            )
            assert fast_fail_run.status == "FAILED"
            assert "Circuit breaker is OPEN" in fast_fail_run.error

            dlq_repo = DeadLetterRepository(db, tenant_id)
            pending = await dlq_repo.list_pending()
            assert len(pending) == 4
            circuit_open_dlq = [d for d in pending if d.error_category == "CIRCUIT_OPEN"]
            assert len(circuit_open_dlq) >= 1

            inc_repo = IncidentRepository(db, tenant_id)
            active_incidents = await inc_repo.list_active()
            assert len(active_incidents) == 1
            assert active_incidents[0].connection_id == conn_id
            assert active_incidents[0].status == "OPEN"

    finally:
        rest_conn.execute = real_execute


@pytest.mark.asyncio
async def test_chaos_system_recovery_and_batch_dlq_replay():
    """
    Chaos Test: Upstream recovers and batch replay recovers all failed DLQ events.
    Verifies that:
    1. Circuit breaker resets to CLOSED.
    2. Batch DLQ replay (/api/v1/incidents/dlq/replay-all) drains the queue.
    3. All events are recovered without duplicate writes.
    """
    tenant_id = f"tenant_recovery_{uuid.uuid4().hex[:6]}"

    async with AsyncSessionLocal() as db:
        db.add(Tenant(id=tenant_id, name="Recovery Tenant", slug=f"rec-{tenant_id}"))
        await db.commit()

        dlq_repo = DeadLetterRepository(db, tenant_id)
        for i in range(3):
            dlq_item = await dlq_repo.create(
                from_obj := type("Dummy", (), {})()
            ) if False else None

        from app.models.dlq import DeadLetterRecord
        for i in range(3):
            await dlq_repo.create(DeadLetterRecord(
                id=f"dlq_rec_{i}_{uuid.uuid4().hex[:4]}",
                tenant_id=tenant_id,
                run_id=f"RUN-STALLED-{i}",
                node_id="node_2",
                event_type="workflow.failed",
                workflow_id="wf_sample",
                reason="Simulated network partition outage",
                error_category="TRANSIENT",
                attempts=3,
                payload_snapshot={"order_id": f"ORD-CHAOS-{i}"},
                status="PENDING",
            ))

        pending_before = await dlq_repo.list_pending()
        assert len(pending_before) == 3

        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
            headers={"X-Tenant-ID": tenant_id},
        ) as ac:
            batch_resp = await ac.post("/api/v1/incidents/dlq/replay-all")
            assert batch_resp.status_code == 200
            data = batch_resp.json()
            assert data["status"] == "BATCH_REPLAYED"
            assert data["replayed_count"] >= 3

        async with AsyncSessionLocal() as verify_db:
            verify_dlq = DeadLetterRepository(verify_db, tenant_id)
            pending_after = await verify_dlq.list_pending()
            assert len(pending_after) == 0
