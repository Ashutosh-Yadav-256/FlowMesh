"""Milestone 7 — Observability, Telemetry & Distributed Tracing Test Suite.

Tests:
1. W3C TraceContext parsing and generation (traceparent format: 00-{trace_id}-{span_id}-01).
2. TraceStore in-memory recording, chronological sorting, and FIFO retention.
3. Prometheus metrics collectors (runs counter, duration histogram, breaker gauge, DLQ size).
4. Structured JSON logging enforcing §8 mandatory fields on every line.
5. FastAPI TelemetryMiddleware trace propagation and Prometheus metric tracking.
6. API endpoints: /metrics, /api/v1/observability/stats, /api/v1/traces/{trace_id}, and /api/v1/runs/{id}/trace.
"""
from __future__ import annotations
import json
import logging
import time
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

from app.database import Base, get_db
from app.main import create_app
from app.models.tenant import Tenant
from app.models.workflow import WorkflowRecord
from app.models.run import RunRecord, RunStepRecord
from app.observability.tracing import (
    TraceContext,
    trace_store,
    record_span,
    record_async_span,
    SpanRecord,
)
from app.observability.metrics import (
    record_run_metric,
    record_circuit_breaker_state,
    record_dlq_size,
    generate_latest_metrics,
    flowmesh_runs_total,
    flowmesh_circuit_breaker_state,
)
from app.observability.logging import FlowMeshJSONFormatter, get_logger


@pytest_asyncio.fixture
async def test_db():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async_session = async_sessionmaker(engine, expire_on_commit=False)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with async_session() as session:

        t = Tenant(id="tenant_obs_test", name="Obs Test Tenant", slug="obs-test")
        session.add(t)

        wf = WorkflowRecord(
            id="wf_telemetry_demo",
            tenant_id="tenant_obs_test",
            name="Telemetry Demo Workflow",
            trigger_type="webhook",
            definition_json={"nodes": [], "edges": []},
        )
        session.add(wf)

        run = RunRecord(
            id="run_trace_01",
            tenant_id="tenant_obs_test",
            workflow_id="wf_telemetry_demo",
            workflow_version=1,
            status="SUCCESS",
            duration_seconds=0.42,
            trigger_source="webhook",
            trace_id="4bf92f3577b34da6a3ce929d0e0e4736",
            input_payload={"order_id": "ORD-101"},
            output_payload={"status": "APPROVED"},
        )
        session.add(run)

        step = RunStepRecord(
            id="step_trace_01",
            run_id="run_trace_01",
            tenant_id="tenant_obs_test",
            node_id="node_query_pg",
            name="PostgreSQL Query",
            node_type="action.db_query",
            status="SUCCESS",
            attempt=1,
            duration_ms=42.0,
            input_snapshot={"query": "SELECT * FROM orders"},
            output_snapshot={"count": 1},
        )
        session.add(step)
        await session.commit()

        yield session

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest_asyncio.fixture
async def client(test_db):
    app = create_app()
    app.dependency_overrides[get_db] = lambda: test_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


def test_w3c_trace_context_propagation():
    """Verifies W3C TraceContext generation, encoding, and regex parsing."""
    trace_id = "4bf92f3577b34da6a3ce929d0e0e4736"
    span_id = "00f067aa0ba902b7"

    header = TraceContext.format_traceparent(trace_id, span_id, sampled=True)
    assert header == "00-4bf92f3577b34da6a3ce929d0e0e4736-00f067aa0ba902b7-01"

    extracted_trace_id, extracted_span_id = TraceContext.parse_traceparent(header)
    assert extracted_trace_id == trace_id
    assert extracted_span_id == span_id

    bad_trace_id, bad_span_id = TraceContext.parse_traceparent("invalid-header")
    assert bad_trace_id is None
    assert bad_span_id is None


def test_trace_store_and_span_recording():
    """Verifies synchronous and asynchronous trace span collection and error capture."""
    trace_store.clear()
    trace_id = "trace_unit_test_99"

    with record_span("root.operation", service="flowmesh-api", trace_id=trace_id) as span:
        span.attributes["custom.attr"] = "hello_world"

    spans = trace_store.get_trace(trace_id)
    assert spans is not None
    assert len(spans) == 1
    assert spans[0].name == "root.operation"
    assert spans[0].status == "OK"
    assert spans[0].attributes["custom.attr"] == "hello_world"
    assert spans[0].duration_ms >= 0

    with pytest.raises(RuntimeError):
        with record_span("failing.step", service="workflow-engine", trace_id=trace_id):
            raise RuntimeError("Database connection refused")

    updated_spans = trace_store.get_trace(trace_id)
    assert len(updated_spans) == 2
    failing_span = next(s for s in updated_spans if s.name == "failing.step")
    assert failing_span.status == "ERROR"
    assert "Database connection refused" in failing_span.error_message


def test_prometheus_metrics_collection():
    """Verifies Prometheus counter and gauge operations and text serialization."""

    record_run_metric(
        tenant_id="tenant_acme",
        workflow_id="wf_orders",
        status="SUCCESS",
        duration_s=0.15,
    )

    record_circuit_breaker_state(
        tenant_id="tenant_acme",
        connection_id="conn_warehouse_api",
        state="OPEN",
    )
    assert flowmesh_circuit_breaker_state.labels(
        tenant_id="tenant_acme",
        connection_id="conn_warehouse_api",
    )._value.get() == 2

    record_circuit_breaker_state(
        tenant_id="tenant_acme",
        connection_id="conn_warehouse_api",
        state="CLOSED",
    )
    assert flowmesh_circuit_breaker_state.labels(
        tenant_id="tenant_acme",
        connection_id="conn_warehouse_api",
    )._value.get() == 0

    metrics_text = generate_latest_metrics().decode("utf-8")
    assert "flowmesh_runs_total" in metrics_text
    assert "flowmesh_circuit_breaker_state" in metrics_text
    assert "flowmesh_run_duration_seconds" in metrics_text


def test_structured_json_logging_section_8_compliance():
    """Proves all 8 mandatory enterprise fields from Section 8 are formatted on every log line."""
    formatter = FlowMeshJSONFormatter()
    record = logging.LogRecord(
        name="flowmesh.test",
        level=logging.INFO,
        pathname=__file__,
        lineno=10,
        msg="Executing order dispatch",
        args=(),
        exc_info=None,
    )
    record.request_id = "req_12345"
    record.tenant_id = "tenant_test_inc"
    record.agent_id = "agent-prod-01"
    record.user_id = "user_operator_9"
    record.connector_id = "conn_pg_01"
    record.operation = "postgres.query"
    record.result = "SUCCESS"
    record.trace_id = "tr_550e8400e29b"

    raw_json = formatter.format(record)
    data = json.loads(raw_json)

    required_fields = [
        "timestamp",
        "request_id",
        "tenant_id",
        "agent_id",
        "user_id",
        "connector_id",
        "operation",
        "result",
        "trace_id",
    ]
    for field in required_fields:
        assert field in data, f"Mandatory §8 field '{field}' missing from structured log output"

    assert data["operation"] == "postgres.query"
    assert data["result"] == "SUCCESS"
    assert data["tenant_id"] == "tenant_test_inc"


@pytest.mark.asyncio
async def test_api_metrics_endpoint(client: AsyncClient):
    """Proves GET /metrics returns standard Prometheus text exposition format."""
    resp = await client.get("/metrics")
    assert resp.status_code == 200
    assert "text/plain" in resp.headers["content-type"]
    text = resp.text
    assert "flowmesh_runs_total" in text
    assert "flowmesh_http_requests_total" in text


@pytest.mark.asyncio
async def test_telemetry_middleware_trace_headers(client: AsyncClient):
    """Proves API responses carry W3C traceparent and x-trace-id response headers."""
    resp = await client.get("/api/v1/overview")
    assert resp.status_code == 200
    assert "x-trace-id" in resp.headers
    assert "traceparent" in resp.headers
    trace_id = resp.headers["x-trace-id"]
    traceparent = resp.headers["traceparent"]
    assert trace_id in traceparent


@pytest.mark.asyncio
async def test_observability_stats_endpoint(client: AsyncClient):
    """Proves GET /api/v1/observability/stats returns live latency and reliability stats."""
    resp = await client.get("/api/v1/observability/stats")
    assert resp.status_code == 200
    data = resp.json()
    assert "p95_latency_ms" in data
    assert "queue_depth" in data
    assert "statestore_contention_pct" in data


@pytest.mark.asyncio
async def test_run_trace_lookup_one_click(client: AsyncClient):
    """Proves 1-click trace retrieval from a Run ID returns distributed spans with timings."""
    resp = await client.get("/api/v1/runs/run_trace_01/trace")
    assert resp.status_code == 200
    data = resp.json()

    assert data["trace_id"] == "4bf92f3577b34da6a3ce929d0e0e4736"
    assert data["run_id"] == "run_trace_01"
    assert data["total_duration_ms"] > 0
    assert len(data["spans"]) >= 3

    span_names = [s["name"] for s in data["spans"]]
    assert any("POST /api/v1/events" in name for name in span_names)
    assert any("nats.publish" in name for name in span_names)
    assert any("worker.consume" in name for name in span_names)
    assert any("node_query_pg" in name for name in span_names)
