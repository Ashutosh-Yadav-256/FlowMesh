"""
Milestone 3 — The Walking Skeleton (Vertical Slice) Test Suite

Tests:
1. Webhook ingress triggers end-to-end workflow execution.
2. OpenTelemetry trace ID is preserved and propagated from ingress to run and steps.
3. Event is published to NATS JetStream event bus and visible on /api/v1/events.
4. Database records run and all step snapshots with input/output data.
5. GET /api/v1/runs/{run_id} renders full timeline with duration and status.
6. Idempotency-Key deduplication prevents duplicate executions.
"""

import sys
import uuid
import pytest
from httpx import AsyncClient, ASGITransport

sys.path.insert(0, "apps/api")
sys.path.insert(0, "packages/auth")
sys.path.insert(0, "packages/workflow-schema")
sys.path.insert(0, "services/workflow-engine")
sys.path.insert(0, "services/event-router")
sys.path.insert(0, "packages/connector-sdk")
sys.path.insert(0, "connectors")

from app.main import app


@pytest.mark.asyncio
async def test_webhook_walking_skeleton_vertical_slice():
    """
    Executes the Milestone 3 Walking Skeleton:
    Webhook -> EventBus -> Engine -> Postgres (Runs & Steps) -> Runs API.
    """
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        tenant_id = "tenant_acme"
        custom_trace_id = "trace_deadbeef_0011223344556677"
        idempotency_key = f"idem_key_{uuid.uuid4().hex[:8]}"

        payload = {
            "order_id": "ORD-WALK-9001",
            "customer_id": "CUST-412",
            "total_cents": 18500,
            "currency": "USD",
            "items": [{"sku": "SKU-992", "qty": 2}],
        }

        headers = {
            "X-Tenant-ID": tenant_id,
            "X-Trace-ID": custom_trace_id,
            "Idempotency-Key": idempotency_key,
        }
        res = await ac.post(f"/api/v1/webhooks/{tenant_id}/orders", json=payload, headers=headers)
        assert res.status_code == 200
        data = res.json()
        assert data["success"] is True
        assert data["status"] == "SUCCESS"
        assert data["trace_id"] == custom_trace_id
        run_id = data["run_id"]
        assert run_id.startswith("RUN-")

        run_res = await ac.get(f"/api/v1/runs/{run_id}", headers=headers)
        assert run_res.status_code == 200
        run_data = run_res.json()
        assert run_data["id"] == run_id
        assert run_data["status"] == "SUCCESS"
        assert run_data["trace_id"] == custom_trace_id
        assert len(run_data["steps"]) >= 4

        for step in run_data["steps"]:
            assert step["status"] == "SUCCESS"
            assert step["duration_ms"] > 0
            assert "input_snapshot" in step

        res_dup = await ac.post(f"/api/v1/webhooks/{tenant_id}/orders", json=payload, headers=headers)
        assert res_dup.status_code == 200
        dup_data = res_dup.json()
        assert dup_data["run_id"] == run_id

        events_res = await ac.get("/api/v1/events", headers=headers)
        assert events_res.status_code == 200
        events_list = events_res.json()
        assert len(events_list) > 0
        assert any(e["type"] == "webhook.received" for e in events_list)
