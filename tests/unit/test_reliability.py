"""
FlowMesh Reliability, Error Categorization, Circuit Breaker, and DLQ Unit Tests
Verifies fault-tolerance, retry backoff with jitter, StateStore circuit breakers,
automatic incident creation, and Dead Letter Queue exact-once replay recovery.
"""

import sys
import uuid
import time
import pytest
from httpx import AsyncClient, ASGITransport

sys.path.insert(0, "apps/api")
sys.path.insert(0, "packages/workflow-schema")
sys.path.insert(0, "packages/connector-sdk")
sys.path.insert(0, "packages/state-store")
sys.path.insert(0, "services/workflow-engine")
sys.path.insert(0, "services/incident-manager")

from app.main import app
from app.database import AsyncSessionLocal
from app.models.tenant import Tenant
from app.repositories.tenant_scoped import (
    DeadLetterRepository,
    IncidentRepository,
    RunRepository,
    WorkflowRepository,
)
from flowmesh_state.interface import MemoryStateStore
import pytest_asyncio
from app.database import engine, Base
from flowmesh_workflow.schema import WorkflowDefinition, WorkflowNode, WorkflowEdge, TriggerSpec, RetryPolicy
from flowmesh_engine.errors import (
    ErrorCategory,
    CircuitBreakerOpenError,
    categorize_error,
    calculate_backoff,
)
from flowmesh_engine.engine import WorkflowEngine
from flowmesh_connector.registry import register_connector
from flowmesh_connector.protocol import Connector, ConnectionSpec, Operation, OperationResult, TestResult, DiscoveryGraph


@pytest_asyncio.fixture(autouse=True)
async def init_tables():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


def test_error_categorization():
    """Verifies that transient, permanent, and circuit-breaker errors are accurately categorized."""

    assert categorize_error("HTTP 503: Service Unavailable") == ErrorCategory.TRANSIENT
    assert categorize_error("HTTP 502: Bad Gateway") == ErrorCategory.TRANSIENT
    assert categorize_error("HTTP 504: Gateway Timeout") == ErrorCategory.TRANSIENT
    assert categorize_error("HTTP 429: Rate Limit Exceeded") == ErrorCategory.TRANSIENT
    assert categorize_error(TimeoutError("Socket read timeout")) == ErrorCategory.TRANSIENT
    assert categorize_error(ConnectionError("Connection refused")) == ErrorCategory.TRANSIENT
    assert categorize_error("getaddrinfo failed: temporary failure in name resolution") == ErrorCategory.TRANSIENT

    assert categorize_error("HTTP 400: Bad Request") == ErrorCategory.PERMANENT
    assert categorize_error("HTTP 401: Unauthorized") == ErrorCategory.PERMANENT
    assert categorize_error("HTTP 403: Forbidden") == ErrorCategory.PERMANENT
    assert categorize_error("HTTP 404: Not Found") == ErrorCategory.PERMANENT
    assert categorize_error("HTTP 422: Unprocessable Entity") == ErrorCategory.PERMANENT
    assert categorize_error("Schema validation error: Missing tax_id") == ErrorCategory.PERMANENT
    assert categorize_error("Cycle detected in DAG") == ErrorCategory.PERMANENT

    assert categorize_error(CircuitBreakerOpenError("conn_rest_01")) == ErrorCategory.CIRCUIT_OPEN
    assert categorize_error("Circuit breaker is OPEN for connection 'conn_rest_01'") == ErrorCategory.CIRCUIT_OPEN


def test_calculate_backoff():
    """Verifies backoff calculation and jitter bounds."""
    policy = RetryPolicy(
        max_attempts=4,
        backoff="exponential",
        initial_interval_seconds=0.2,
        max_interval_seconds=2.0,
        jitter=False,
    )
    assert calculate_backoff(1, policy) == 0.2
    assert calculate_backoff(2, policy) == 0.4
    assert calculate_backoff(3, policy) == 0.8
    assert calculate_backoff(4, policy) == 1.6

    policy_jitter = RetryPolicy(
        max_attempts=3,
        backoff="exponential",
        initial_interval_seconds=1.0,
        max_interval_seconds=10.0,
        jitter=True,
    )
    b2 = calculate_backoff(2, policy_jitter)
    assert 1.0 <= b2 <= 2.0


@pytest.mark.asyncio
async def test_statestore_circuit_breaker_full_lifecycle():
    """
    Verifies the 3-state circuit breaker state machine:
    CLOSED -> (failures >= threshold) -> OPEN -> (cooldown elapsed) -> HALF-OPEN -> (canary success) -> CLOSED.
    """
    store = MemoryStateStore(default_cooldown_seconds=0.05)
    conn_id = "conn_flake_api"

    assert await store.get_circuit_breaker_state(conn_id) == "CLOSED"

    assert await store.record_circuit_failure(conn_id, threshold=3) == "CLOSED"
    assert await store.record_circuit_failure(conn_id, threshold=3) == "CLOSED"

    assert await store.record_circuit_failure(conn_id, threshold=3) == "OPEN"
    assert await store.get_circuit_breaker_state(conn_id) == "OPEN"

    time.sleep(0.06)
    assert await store.get_circuit_breaker_state(conn_id) == "HALF-OPEN"

    assert await store.record_circuit_failure(conn_id, threshold=3) == "OPEN"
    assert await store.get_circuit_breaker_state(conn_id) == "OPEN"

    time.sleep(0.06)
    assert await store.get_circuit_breaker_state(conn_id) == "HALF-OPEN"
    assert await store.record_circuit_success(conn_id) == "CLOSED"
    assert await store.get_circuit_breaker_state(conn_id) == "CLOSED"


class FlakyConnector:
    """Mock connector that fails N times with HTTP 503 then succeeds."""
    def __init__(self, fail_count: int = 2):
        self.fail_count = fail_count
        self.attempts = 0

    async def test(self, conn: ConnectionSpec) -> TestResult:
        return TestResult(success=True, connection_id=conn.id, steps=[])

    async def discover(self, conn: ConnectionSpec) -> DiscoveryGraph:
        return DiscoveryGraph(connection_id=conn.id, entities=[])

    async def execute(self, conn: ConnectionSpec, op: Operation) -> OperationResult:
        self.attempts += 1
        if self.attempts <= self.fail_count:
            return OperationResult(
                success=False,
                error="HTTP 503: Service Unavailable from upstream service",
                duration_ms=5.0,
            )
        return OperationResult(
            success=True,
            data={"status": "ok", "delivered": True, "attempt": self.attempts},
            duration_ms=5.0,
        )

    def operations(self):
        return []


@pytest.mark.asyncio
async def test_workflow_engine_retry_recovers_transient_failure():
    """Verifies that transient errors trigger exponential backoff retries and succeed without failing the run."""
    tenant_id = f"tenant_retry_{uuid.uuid4().hex[:6]}"
    flaky = FlakyConnector(fail_count=2)
    register_connector("flaky_mock", flaky)

    async with AsyncSessionLocal() as db:
        db.add(Tenant(id=tenant_id, name="Retry Tenant", slug=f"retry-{tenant_id}"))
        await db.commit()

        wf_def = WorkflowDefinition(
            id="wf_retry_test",
            schema_version=1,
            name="Retry Test Workflow",
            trigger=TriggerSpec(type="manual"),
            nodes=[
                WorkflowNode(id="node_1", type="trigger.webhook", name="Ingress"),
                WorkflowNode(
                    id="node_2",
                    type="action.http",
                    name="Flaky Upstream",
                    connection_id="conn_flaky",
                    config={"endpoint": "/test"},
                    retry=RetryPolicy(
                        max_attempts=3,
                        backoff="fixed",
                        initial_interval_seconds=0.01,
                        jitter=False,
                    ),
                ),
            ],
            edges=[WorkflowEdge(source="node_1", target="node_2")],
        )

        engine = WorkflowEngine(db, tenant_id)
        orig_dispatch = engine._dispatch_node_type

        async def mock_dispatch(node, config, ctx):
            if node.id == "node_2":
                res = await flaky.execute(
                    ConnectionSpec(
                        id="conn_flaky",
                        tenant_id=tenant_id,
                        type="flaky_mock",
                        name="Flaky",
                        config={"base_url": "https://api.flowmesh.dev"},
                    ),
                    Operation(id="1", name="call", parameters={})
                )
                if not res.success:
                    raise RuntimeError(res.error)
                return res.data
            return await orig_dispatch(node, config, ctx)

        engine._dispatch_node_type = mock_dispatch

        run = await engine.execute(
            workflow_def=wf_def,
            run_id=f"RUN-{uuid.uuid4().hex[:6].upper()}",
            input_payload={"order_id": "ORD-1234"},
        )

        assert run.status == "SUCCESS"
        assert flaky.attempts == 3


@pytest.mark.asyncio
async def test_workflow_engine_fast_fails_when_circuit_breaker_open():
    """Verifies that an OPEN circuit breaker fast-fails executions and routes directly to DLQ."""
    tenant_id = f"tenant_cb_{uuid.uuid4().hex[:6]}"
    state_store = MemoryStateStore()
    conn_id = "conn_degraded_service"

    await state_store.record_circuit_failure(conn_id, threshold=1)
    assert await state_store.get_circuit_breaker_state(conn_id) == "OPEN"

    async with AsyncSessionLocal() as db:
        db.add(Tenant(id=tenant_id, name="CB Tenant", slug=f"cb-{tenant_id}"))
        await db.commit()

        wf_def = WorkflowDefinition(
            id="wf_cb_test",
            schema_version=1,
            name="Circuit Breaker Test",
            trigger=TriggerSpec(type="manual"),
            nodes=[
                WorkflowNode(id="node_1", type="trigger.webhook", name="Ingress"),
                WorkflowNode(
                    id="node_2",
                    type="action.http",
                    name="Call Degraded Service",
                    connection_id=conn_id,
                    config={"endpoint": "/fast-fail"},
                ),
            ],
            edges=[WorkflowEdge(source="node_1", target="node_2")],
        )

        engine = WorkflowEngine(db, tenant_id, state_store=state_store)
        run = await engine.execute(
            workflow_def=wf_def,
            run_id=f"RUN-{uuid.uuid4().hex[:6].upper()}",
            input_payload={"data": "test"},
        )

        assert run.status == "FAILED"
        assert "Circuit breaker is OPEN" in run.error

        dlq_repo = DeadLetterRepository(db, tenant_id)
        dlqs = await dlq_repo.list_pending()
        assert len(dlqs) == 1
        assert dlqs[0].run_id == run.id
        assert dlqs[0].error_category == "CIRCUIT_OPEN"

        inc_repo = IncidentRepository(db, tenant_id)
        incidents = await inc_repo.list_active()
        assert len(incidents) == 1
        assert incidents[0].connection_id == conn_id
        assert "Degraded Connection" in incidents[0].title


@pytest.mark.asyncio
async def test_dlq_replay_exact_once_recovery():
    """
    Verifies that when an execution fails and routes to DLQ:
    1. DLQ records the failure with input payload and status PENDING.
    2. Calling DLQ replay resumes the run via WorkflowEngine.
    3. Already completed steps are NOT re-executed.
    4. DLQ item transitions to REPLAYED.
    """
    tenant_id = f"tenant_dlq_{uuid.uuid4().hex[:6]}"
    from flowmesh_connector.registry import get_connector
    from app.models.workflow import WorkflowRecord

    rest_conn = get_connector("rest")
    real_execute = rest_conn.execute

    fail_upstream = True

    async def flaky_rest_execute(conn, op):
        nonlocal fail_upstream
        if fail_upstream and op.parameters.get("endpoint") == "/flaky-endpoint":
            return OperationResult(
                success=False,
                error="HTTP 503: Upstream Service Outage",
                execution_time_ms=5.0,
            )
        return await real_execute(conn, op)

    rest_conn.execute = flaky_rest_execute

    try:
        async with AsyncSessionLocal() as db:
            db.add(Tenant(id=tenant_id, name="DLQ Tenant", slug=f"dlq-{tenant_id}"))
            await db.commit()

            wf_id = f"wf_{uuid.uuid4().hex[:8]}"
            wf_record = WorkflowRecord(
                id=wf_id,
                tenant_id=tenant_id,
                name="DLQ Workflow",
                description="Testing DLQ exact-once replay",
                status="active",
                version=1,
                trigger_type="manual",
                definition_json={
                    "id": wf_id,
                    "schema_version": 1,
                    "name": "DLQ Workflow",
                    "trigger": {"type": "manual", "config": {}},
                    "nodes": [
                        {"id": "node_1", "type": "trigger.webhook", "name": "Step 1 (Safe)"},
                        {
                            "id": "node_2",
                            "type": "action.http",
                            "name": "Step 2 (Flaky)",
                            "connection_id": "conn_rest_01",
                            "config": {"endpoint": "/flaky-endpoint", "method": "GET"},
                        },
                    ],
                    "edges": [{"source": "node_1", "target": "node_2"}],
                },
            )
            wf_repo = WorkflowRepository(db, tenant_id)
            await wf_repo.create(wf_record)

            wf_def = WorkflowDefinition(**wf_record.definition_json)
            run_id = f"RUN-{uuid.uuid4().hex[:6].upper()}"

            engine = WorkflowEngine(db, tenant_id)

            initial_run = await engine.execute(
                workflow_def=wf_def,
                run_id=run_id,
                input_payload={"order_num": 9988},
            )
            assert initial_run.status == "FAILED"

            run_repo = RunRepository(db, tenant_id)
            recorded_run = await run_repo.get_by_id(run_id)
            assert recorded_run is not None
            assert len(recorded_run.steps) == 2
            assert recorded_run.steps[0].status == "SUCCESS"
            assert recorded_run.steps[1].status == "FAILED"

            dlq_repo = DeadLetterRepository(db, tenant_id)
            pending_dlqs = await dlq_repo.list_pending()
            assert len(pending_dlqs) == 1
            dlq_item = pending_dlqs[0]
            dlq_id = dlq_item.id
            assert dlq_item.status == "PENDING"
            assert dlq_item.run_id == run_id

            fail_upstream = False

            async with AsyncClient(
                transport=ASGITransport(app=app),
                base_url="http://test",
                headers={"X-Tenant-ID": tenant_id},
            ) as ac:
                replay_resp = await ac.post(f"/api/v1/incidents/dlq/{dlq_id}/replay")
                assert replay_resp.status_code == 200
                resp_data = replay_resp.json()
                assert resp_data["status"] == "REPLAYED"
                assert resp_data["run_status"] == "SUCCESS"

        async with AsyncSessionLocal() as verify_db:
            verify_run_repo = RunRepository(verify_db, tenant_id)
            verify_dlq_repo = DeadLetterRepository(verify_db, tenant_id)

            refreshed_run = await verify_run_repo.get_by_id(run_id)
            assert refreshed_run.status == "SUCCESS"

            step1_records = [s for s in refreshed_run.steps if s.node_id == "node_1"]
            assert len(step1_records) == 1

            replayed_item = await verify_dlq_repo.get_by_id(dlq_id)
            assert replayed_item.status == "REPLAYED"
            assert replayed_item.replayed_at is not None

    finally:
        rest_conn.execute = real_execute
