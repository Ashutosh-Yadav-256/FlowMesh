import sys
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport

sys.path.insert(0, "apps/api")
sys.path.insert(0, "packages/auth")
from app.main import app


@pytest_asyncio.fixture(autouse=True)
async def seed_demo_workspace():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        await ac.post("/api/v1/demo/seed", headers={"X-Tenant-ID": "tenant_acme"})
    yield



@pytest.mark.asyncio
async def test_health_endpoint():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["app"] == "FlowMesh"
        assert "uptime_seconds" in data


@pytest.mark.asyncio
async def test_ready_endpoint():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/ready")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ready"
        assert "components" in data


@pytest.mark.asyncio
async def test_overview_endpoint():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/api/v1/overview")
        assert response.status_code == 200
        data = response.json()
        assert data["metrics"]["active_workflows"] > 0
        assert data["metrics"]["success_rate_pct"] >= 0.0
        assert len(data["system_health"]) >= 5
        assert len(data["workflow_activity"]) > 0


@pytest.mark.asyncio
async def test_connections_and_test_step():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/api/v1/connections")
        assert response.status_code == 200
        conns = response.json()
        assert len(conns) >= 5

        test_resp = await ac.post(f"/api/v1/connections/{conns[0]['id']}/test")
        assert test_resp.status_code == 200
        test_data = test_resp.json()
        assert test_data["success"] is True
        assert len(test_data["steps"]) == 4
        assert all(step["status"] == "passed" for step in test_data["steps"])


@pytest.mark.asyncio
async def test_workflows_and_runs():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        wf_resp = await ac.get("/api/v1/workflows")
        assert wf_resp.status_code == 200
        workflows = wf_resp.json()
        assert len(workflows) >= 3

        runs_resp = await ac.get("/api/v1/runs")
        assert runs_resp.status_code == 200
        runs = runs_resp.json()
        assert len(runs) >= 2

        run_detail_resp = await ac.get(f"/api/v1/runs/{runs[0]['id']}")
        assert run_detail_resp.status_code == 200
        run_detail = run_detail_resp.json()
        assert len(run_detail["steps"]) >= 4


@pytest.mark.asyncio
async def test_agents_and_incidents():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        agents_resp = await ac.get("/api/v1/agents", headers={"X-Tenant-ID": "tenant_acme"})
        assert agents_resp.status_code == 200
        agents = agents_resp.json()
        assert len(agents) >= 1

        incidents_resp = await ac.get("/api/v1/incidents", headers={"X-Tenant-ID": "tenant_acme"})
        assert incidents_resp.status_code == 200
        incidents = incidents_resp.json()
        assert len(incidents) >= 1

        dlq_resp = await ac.get("/api/v1/incidents/dlq", headers={"X-Tenant-ID": "tenant_acme"})
        assert dlq_resp.status_code == 200
        dlq_items = dlq_resp.json()
        assert isinstance(dlq_items, list)


@pytest.mark.asyncio
async def test_connection_enable_disable_toggle():
    headers = {"X-Tenant-ID": "tenant_acme"}
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        res = await ac.get("/api/v1/connections", headers=headers)
        assert res.status_code == 200
        conns = res.json()
        target = conns[0]
        conn_id = target["id"]
        assert target.get("enabled") is True

        dis_res = await ac.post(f"/api/v1/connections/{conn_id}/disable", headers=headers)
        assert dis_res.status_code == 200
        dis_data = dis_res.json()
        assert dis_data["enabled"] is False
        assert dis_data["status"] == "disabled"

        test_blocked = await ac.post(f"/api/v1/connections/{conn_id}/test", headers=headers)
        assert test_blocked.status_code == 400
        assert "currently disabled" in test_blocked.json()["detail"]

        disc_blocked = await ac.post(f"/api/v1/connections/{conn_id}/discover", headers=headers)
        assert disc_blocked.status_code == 400
        assert "currently disabled" in disc_blocked.json()["detail"]

        toggle_res = await ac.post(f"/api/v1/connections/{conn_id}/toggle", headers=headers)
        assert toggle_res.status_code == 200
        assert toggle_res.json()["enabled"] is True
        assert toggle_res.json()["status"] == "healthy"

        test_ok = await ac.post(f"/api/v1/connections/{conn_id}/test", headers=headers)
        assert test_ok.status_code == 200
        assert test_ok.json()["success"] is True

        en_res = await ac.post(f"/api/v1/connections/{conn_id}/enable", headers=headers)
        assert en_res.status_code == 200
        assert en_res.json()["enabled"] is True

