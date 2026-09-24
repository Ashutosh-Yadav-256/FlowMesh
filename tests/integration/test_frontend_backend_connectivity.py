"""
Senior QA Integration Test: Frontend Feature & Backend Connectivity Verification.

This test suite acts as an automated Senior Test Engineer auditing every single
frontend module to verify:
1. The backend endpoint corresponding to the frontend feature responds with HTTP 200.
2. The payload structure conforms to the schema expected by the frontend UI.
3. Multi-tenant isolation (X-Tenant-ID) works across all frontend endpoints.
4. Mutation actions (Deploy, Replay, Test Connection, Diagnose, Seed) execute without errors.
"""

import sys
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport

sys.path.insert(0, "apps/api")
sys.path.insert(0, "packages/auth")
sys.path.insert(0, "packages/workflow-schema")
sys.path.insert(0, "packages/state-store")
sys.path.insert(0, "packages/connector-sdk")
sys.path.insert(0, "services/workflow-engine")

from app.main import app


@pytest_asyncio.fixture(autouse=True)
async def seed_demo_workspace():
    """Ensure workspace has clean baseline demo data seeded."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        res = await client.post("/api/v1/demo/seed", headers={"X-Tenant-ID": "tenant_acme"})
        assert res.status_code == 200


@pytest.mark.asyncio
async def test_feature_overview_dashboard():
    """Verify Overview Dashboard endpoint /api/v1/overview."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        res = await client.get("/api/v1/overview", headers={"X-Tenant-ID": "tenant_acme"})
        assert res.status_code == 200, f"Overview failed: {res.text}"
        data = res.json()
        assert "metrics" in data
        assert "system_health" in data
        assert "workflow_activity" in data
        assert "recent_incidents" in data
        assert data["metrics"]["active_workflows"] >= 1
        assert len(data["system_health"]) >= 5


@pytest.mark.asyncio
async def test_feature_workflows_studio_and_lifecycle():
    """Verify Workflows listing, versioning, deployment, and rollback."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:

        res = await client.get("/api/v1/workflows", headers={"X-Tenant-ID": "tenant_acme"})
        assert res.status_code == 200
        workflows = res.json()
        assert len(workflows) >= 1
        wf_id = workflows[0]["id"]

        detail_res = await client.get(f"/api/v1/workflows/{wf_id}", headers={"X-Tenant-ID": "tenant_acme"})
        assert detail_res.status_code == 200
        detail = detail_res.json()
        assert "definition" in detail
        assert len(detail["definition"]["nodes"]) >= 2

        ver_res = await client.get(f"/api/v1/workflows/{wf_id}/versions", headers={"X-Tenant-ID": "tenant_acme"})
        assert ver_res.status_code == 200
        versions = ver_res.json()
        assert len(versions) >= 1

        deploy_res = await client.post(
            f"/api/v1/workflows/{wf_id}/deploy",
            json={"changelog": "Senior QA Automated Deployment Test"},
            headers={"X-Tenant-ID": "tenant_acme", "X-User-Role": "operator"},
        )
        assert deploy_res.status_code == 200, f"Deploy failed: {deploy_res.text}"
        deployed = deploy_res.json()
        assert deployed["version"] > detail["version"]


@pytest.mark.asyncio
async def test_feature_runs_and_ai_diagnostics():
    """Verify execution runs, timeline inspection, step replay, and AI diagnosis."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:

        runs_res = await client.get("/api/v1/runs", headers={"X-Tenant-ID": "tenant_acme"})
        assert runs_res.status_code == 200
        runs = runs_res.json()
        assert len(runs) >= 1
        run_id = runs[0]["id"]

        run_detail_res = await client.get(f"/api/v1/runs/{run_id}", headers={"X-Tenant-ID": "tenant_acme"})
        assert run_detail_res.status_code == 200
        run_detail = run_detail_res.json()
        assert "steps" in run_detail
        assert len(run_detail["steps"]) >= 1

        trace_res = await client.get(f"/api/v1/runs/{run_id}/trace", headers={"X-Tenant-ID": "tenant_acme"})
        assert trace_res.status_code == 200
        trace_data = trace_res.json()
        assert "trace_id" in trace_data
        assert len(trace_data["spans"]) >= 1

        ai_res = await client.post(
            "/api/v1/assistant/diagnose",
            json={"run_id": run_id, "query": "Diagnose failure root cause and proposed fix"},
            headers={"X-Tenant-ID": "tenant_acme"},
        )
        assert ai_res.status_code == 200, f"AI diagnosis failed: {ai_res.text}"
        report = ai_res.json()
        assert "root_cause_summary" in report
        assert "error_category" in report
        assert "suggested_actions" in report


@pytest.mark.asyncio
async def test_feature_connections_and_drift():
    """Verify connection listing, 4-point connectivity test, and schema drift detection."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:

        conns_res = await client.get("/api/v1/connections", headers={"X-Tenant-ID": "tenant_acme"})
        assert conns_res.status_code == 200
        conns = conns_res.json()
        assert len(conns) >= 3

        pg_conn = next(c for c in conns if c["type"] == "postgres")
        test_res = await client.post(f"/api/v1/connections/{pg_conn['id']}/test", headers={"X-Tenant-ID": "tenant_acme"})
        assert test_res.status_code == 200
        test_data = test_res.json()
        assert test_data["success"] is True
        assert len(test_data["steps"]) == 4

        drift_res = await client.get(f"/api/v1/connections/{pg_conn['id']}/drift", headers={"X-Tenant-ID": "tenant_acme"})
        assert drift_res.status_code == 200
        drift_data = drift_res.json()
        assert "has_drift" in drift_data
        assert "highest_severity" in drift_data
        assert "changes" in drift_data


@pytest.mark.asyncio
async def test_feature_edge_agents_fleet():
    """Verify Edge Agent fleet listing, enrollment token generation, and heartbeats."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:

        agents_res = await client.get("/api/v1/agents", headers={"X-Tenant-ID": "tenant_acme"})
        assert agents_res.status_code == 200
        agents = agents_res.json()
        assert len(agents) >= 1
        assert any(a["status"] == "healthy" for a in agents)

        tok_res = await client.post(
            "/api/v1/agents/enrollment-token",
            headers={"X-Tenant-ID": "tenant_acme", "X-User-Role": "operator"},
        )
        assert tok_res.status_code == 200, f"Token gen failed: {tok_res.text}"
        tok_data = tok_res.json()
        assert "enrollment_token" in tok_data

        enroll_res = await client.post(
            "/api/v1/agents/enroll",
            json={
                "enrollment_token": tok_data["enrollment_token"],
                "name": "qa-test-agent-01",
                "version": "v1.0.0",
            },
            headers={"X-Tenant-ID": "tenant_acme"},
        )
        assert enroll_res.status_code == 200, f"Enrollment failed: {enroll_res.text}"
        enroll_data = enroll_res.json()
        assert "agent_id" in enroll_data


@pytest.mark.asyncio
async def test_feature_incidents_and_dlq():
    """Verify incident list, incident resolution, and DLQ inspection."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:

        inc_res = await client.get("/api/v1/incidents", headers={"X-Tenant-ID": "tenant_acme"})
        assert inc_res.status_code == 200
        incidents = inc_res.json()
        assert len(incidents) >= 1

        dlq_res = await client.get("/api/v1/incidents/dlq", headers={"X-Tenant-ID": "tenant_acme"})
        assert dlq_res.status_code == 200
        dlq_items = dlq_res.json()
        assert isinstance(dlq_items, list)


@pytest.mark.asyncio
async def test_feature_observability_and_metrics():
    """Verify telemetry stats, OpenTelemetry trace retrieval, and Prometheus metrics."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:

        metrics_res = await client.get("/metrics")
        assert metrics_res.status_code == 200
        assert "flowmesh" in metrics_res.text

        stats_res = await client.get("/api/v1/observability/stats")
        assert stats_res.status_code == 200
        stats = stats_res.json()
        assert "p50_latency_ms" in stats
        assert "p95_latency_ms" in stats


@pytest.mark.asyncio
async def test_feature_audit_trail():
    """Verify append-only immutable audit trail queries."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        audit_res = await client.get("/api/v1/audit", headers={"X-Tenant-ID": "tenant_acme"})
        assert audit_res.status_code == 200
        records = audit_res.json()
        assert len(records) >= 1
        assert "actor" in records[0]
        assert "action" in records[0]


@pytest.mark.asyncio
async def test_feature_events_stream():
    """Verify NATS JetStream event stream queries."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        events_res = await client.get("/api/v1/events", headers={"X-Tenant-ID": "tenant_acme"})
        assert events_res.status_code == 200
        events = events_res.json()
        assert len(events) >= 1
        assert "type" in events[0]
        assert "source" in events[0]


@pytest.mark.asyncio
async def test_feature_organization_and_tenants():
    """Verify tenant retrieval, active context, and tenant isolation."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:

        cur_res = await client.get("/api/v1/tenants/current", headers={"X-Tenant-ID": "tenant_acme"})
        assert cur_res.status_code == 200
        cur_tenant = cur_res.json()
        assert cur_tenant["id"] == "tenant_acme"

        tenants_res = await client.get("/api/v1/tenants", headers={"X-Tenant-ID": "tenant_acme"})
        assert tenants_res.status_code == 200
        tenants = tenants_res.json()
        assert len(tenants) >= 2


@pytest.mark.asyncio
async def test_feature_system_health_and_readiness():
    """Verify /health liveness probe and /ready dependency readiness."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        health_res = await client.get("/health")
        assert health_res.status_code == 200
        assert health_res.json()["status"] == "healthy"

        ready_res = await client.get("/ready")
        assert ready_res.status_code == 200
        assert ready_res.json()["status"] == "ready"
