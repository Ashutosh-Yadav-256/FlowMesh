"""Prometheus Metrics Exporter and Telemetry Registry for FlowMesh."""
from __future__ import annotations
from typing import Optional
from prometheus_client import (
    Counter,
    Histogram,
    Gauge,
    CollectorRegistry,
    generate_latest,
    CONTENT_TYPE_LATEST,
    REGISTRY,
)

flowmesh_runs_total = Counter(
    "flowmesh_runs_total",
    "Total workflow executions partitioned by tenant, workflow, and outcome.",
    ["tenant_id", "workflow_id", "status"],
)

flowmesh_run_duration_seconds = Histogram(
    "flowmesh_run_duration_seconds",
    "Workflow run execution duration in seconds.",
    ["tenant_id", "workflow_id"],
    buckets=(0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0, 60.0),
)

flowmesh_queue_depth = Gauge(
    "flowmesh_queue_depth",
    "Current NATS JetStream queue depth and consumer lag.",
    ["tenant_id", "queue_name"],
)

flowmesh_dlq_size = Gauge(
    "flowmesh_dlq_size",
    "Current number of unprocessed dead letters in the DLQ.",
    ["tenant_id"],
)

flowmesh_agent_heartbeat_age_seconds = Gauge(
    "flowmesh_agent_heartbeat_age_seconds",
    "Seconds elapsed since last received heartbeat from edge agent.",
    ["tenant_id", "agent_id"],
)

flowmesh_circuit_breaker_state = Gauge(
    "flowmesh_circuit_breaker_state",
    "Circuit breaker operational state (0=CLOSED, 1=HALF_OPEN, 2=OPEN).",
    ["tenant_id", "connection_id"],
)

flowmesh_http_requests_total = Counter(
    "flowmesh_http_requests_total",
    "Total HTTP requests received by the FlowMesh API Gateway.",
    ["method", "endpoint", "status"],
)

flowmesh_agent_commands_total = Counter(
    "flowmesh_agent_commands_total",
    "Total commands dispatched to edge agents.",
    ["tenant_id", "agent_id", "operation", "status"],
)


def record_run_metric(
    tenant_id: str,
    workflow_id: str,
    status: str,
    duration_s: float,
) -> None:
    """Helper to atomically record run completion and duration metrics."""
    flowmesh_runs_total.labels(
        tenant_id=tenant_id,
        workflow_id=workflow_id,
        status=status.upper(),
    ).inc()
    
    flowmesh_run_duration_seconds.labels(
        tenant_id=tenant_id,
        workflow_id=workflow_id,
    ).observe(duration_s)


def record_circuit_breaker_state(
    tenant_id: str,
    connection_id: str,
    state: str,
) -> None:
    """Helper to update circuit breaker gauge: CLOSED=0, HALF_OPEN=1, OPEN=2."""
    state_map = {"CLOSED": 0, "HALF_OPEN": 1, "OPEN": 2}
    val = state_map.get(state.upper(), 0)
    flowmesh_circuit_breaker_state.labels(
        tenant_id=tenant_id,
        connection_id=connection_id,
    ).set(val)


def record_dlq_size(tenant_id: str, count: int) -> None:
    """Helper to update dead letter queue size gauge."""
    flowmesh_dlq_size.labels(tenant_id=tenant_id).set(count)


def record_agent_heartbeat(tenant_id: str, agent_id: str, age_seconds: float) -> None:
    """Helper to update agent heartbeat age gauge."""
    flowmesh_agent_heartbeat_age_seconds.labels(
        tenant_id=tenant_id,
        agent_id=agent_id,
    ).set(age_seconds)


def generate_latest_metrics(registry: Optional[CollectorRegistry] = None) -> bytes:
    """Generates Prometheus text exposition format payload."""
    reg = registry or REGISTRY
    return generate_latest(reg)
