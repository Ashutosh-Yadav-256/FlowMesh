import pytest
from httpx import AsyncClient, ASGITransport
import sys

sys.path.insert(0, "apps/api")
sys.path.insert(0, "packages/auth")

from app.main import app


@pytest.mark.asyncio
async def test_default_pagination():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        resp = await ac.get("/api/v1/connections", headers={"X-Tenant-ID": "tenant_acme"})
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)
        assert "X-Total-Count" in resp.headers
        assert resp.headers["X-Page"] == "1"
        assert resp.headers["X-Page-Size"] == "50"
        assert "X-Total-Pages" in resp.headers


@pytest.mark.asyncio
async def test_custom_page_size():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        resp = await ac.get("/api/v1/workflows?page_size=1", headers={"X-Tenant-ID": "tenant_acme"})
        assert resp.status_code == 200
        items = resp.json()
        assert isinstance(items, list)
        assert len(items) <= 1
        assert resp.headers["X-Page-Size"] == "1"


@pytest.mark.asyncio
async def test_page_beyond_total():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        resp = await ac.get("/api/v1/connections?page=999&page_size=50", headers={"X-Tenant-ID": "tenant_acme"})
        assert resp.status_code == 200
        items = resp.json()
        assert isinstance(items, list)
        assert len(items) == 0
        assert resp.headers["X-Page"] == "999"


@pytest.mark.asyncio
async def test_pagination_headers_runs_and_audit():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        runs_resp = await ac.get("/api/v1/runs?page=1&page_size=10", headers={"X-Tenant-ID": "tenant_acme"})
        assert runs_resp.status_code == 200
        assert "X-Total-Count" in runs_resp.headers
        assert runs_resp.headers["X-Page"] == "1"
        assert runs_resp.headers["X-Page-Size"] == "10"

        audit_resp = await ac.get("/api/v1/audit?page=1&page_size=5", headers={"X-Tenant-ID": "tenant_acme"})
        assert audit_resp.status_code == 200
        assert "X-Total-Count" in audit_resp.headers
        assert audit_resp.headers["X-Page"] == "1"
        assert audit_resp.headers["X-Page-Size"] == "5"
