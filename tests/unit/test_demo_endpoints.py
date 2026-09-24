import sys
import pytest
from httpx import AsyncClient, ASGITransport

sys.path.insert(0, "apps/api")
sys.path.insert(0, "packages/auth")
from app.main import app


@pytest.mark.asyncio
async def test_demo_status_endpoint():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/api/v1/demo/status", headers={"X-Tenant-ID": "tenant_test_status"})
        assert response.status_code == 200
        data = response.json()
        assert "tenant_id" in data
        assert "is_demo_mode" in data
        assert "connection_count" in data


@pytest.mark.asyncio
async def test_demo_seed_and_reset_lifecycle():
    headers = {"X-Tenant-ID": "tenant_clean_test_org"}
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:

        seed_resp = await ac.post("/api/v1/demo/seed", headers=headers)
        assert seed_resp.status_code == 200
        seed_data = seed_resp.json()
        assert seed_data["success"] is True
        assert seed_data["connections_created"] >= 3
        assert seed_data["workflows_created"] >= 1

        status_resp = await ac.get("/api/v1/demo/status", headers=headers)
        assert status_resp.status_code == 200
        assert status_resp.json()["is_demo_mode"] is True
        assert status_resp.json()["connection_count"] >= 3

        reset_resp = await ac.post("/api/v1/demo/reset", headers=headers)
        assert reset_resp.status_code == 200
        reset_data = reset_resp.json()
        assert reset_data["success"] is True

        final_status = await ac.get("/api/v1/demo/status", headers=headers)
        assert final_status.status_code == 200
        assert final_status.json()["connection_count"] == 0
        assert final_status.json()["workflow_count"] == 0
        assert final_status.json()["is_demo_mode"] is False
