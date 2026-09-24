import pytest
from httpx import AsyncClient, ASGITransport
import sys

sys.path.insert(0, "apps/api")
sys.path.insert(0, "packages/auth")

from app.main import app
from app.config import settings


@pytest.mark.asyncio
async def test_oversized_body_rejected(monkeypatch):
    monkeypatch.setattr(settings, "max_request_body_bytes", 1024)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        large_payload = {"data": "x" * 2048}
        resp = await ac.post("/api/v1/connections", json=large_payload, headers={"X-Tenant-ID": "tenant_acme"})
        assert resp.status_code == 413
        assert resp.json()["error"] == "PayloadTooLarge"


@pytest.mark.asyncio
async def test_deeply_nested_json_rejected(monkeypatch):
    monkeypatch.setattr(settings, "max_json_nesting_depth", 5)
    nested = {"a": {"b": {"c": {"d": {"e": {"f": "too deep"}}}}}}
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        resp = await ac.post("/api/v1/connections", json=nested, headers={"X-Tenant-ID": "tenant_acme"})
        assert resp.status_code == 400
        assert resp.json()["error"] == "PayloadTooDeep"


@pytest.mark.asyncio
async def test_normal_payload_accepted():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        normal = {
            "name": "Validation Test Conn",
            "type": "rest",
            "config": {"base_url": "https://api.example.com"},
        }
        resp = await ac.post("/api/v1/connections", json=normal, headers={"X-Tenant-ID": "tenant_acme"})
        assert resp.status_code == 201


@pytest.mark.asyncio
async def test_search_query_max_length():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        long_query = "q" * 300
        resp = await ac.get(f"/api/v1/search?q={long_query}", headers={"X-Tenant-ID": "tenant_acme"})
        assert resp.status_code == 422
