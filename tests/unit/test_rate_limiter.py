import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
import sys

sys.path.insert(0, "apps/api")
sys.path.insert(0, "packages/auth")

from app.main import app
from app.config import settings
from app.middleware.rate_limiter import _window_counters


@pytest_asyncio.fixture(autouse=True)
async def reset_rate_limit_windows():
    _window_counters.clear()
    yield
    _window_counters.clear()


@pytest.mark.asyncio
async def test_rate_limiter_allows_under_limit():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        for _ in range(10):
            resp = await ac.get("/api/v1/overview", headers={"X-Tenant-ID": "tenant_test_rl"})
            assert resp.status_code == 200
            assert "X-RateLimit-Limit" in resp.headers
            assert "X-RateLimit-Remaining" in resp.headers


@pytest.mark.asyncio
async def test_rate_limiter_blocks_over_limit(monkeypatch):
    monkeypatch.setattr(settings, "rate_limit_per_minute", 5)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        headers = {"X-Tenant-ID": "tenant_spam"}
        for i in range(5):
            resp = await ac.get("/api/v1/overview", headers=headers)
            assert resp.status_code == 200

        blocked = await ac.get("/api/v1/overview", headers=headers)
        assert blocked.status_code == 429
        data = blocked.json()
        assert data["error"] == "TooManyRequests"
        assert "Retry-After" in blocked.headers
        assert blocked.headers["X-RateLimit-Remaining"] == "0"


@pytest.mark.asyncio
async def test_rate_limiter_returns_correct_headers():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        resp = await ac.get("/api/v1/overview", headers={"X-Tenant-ID": "tenant_headers"})
        assert resp.status_code == 200
        assert resp.headers.get("X-RateLimit-Limit") == str(settings.rate_limit_per_minute)
        assert int(resp.headers.get("X-RateLimit-Remaining", "-1")) >= 0
        assert int(resp.headers.get("X-RateLimit-Reset", "0")) > 0


@pytest.mark.asyncio
async def test_rate_limiter_exempts_health_endpoints():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        for _ in range(15):
            resp = await ac.get("/health")
            assert resp.status_code == 200

        resp = await ac.get("/ready")
        assert resp.status_code == 200


@pytest.mark.asyncio
async def test_rate_limiter_per_tenant_isolation(monkeypatch):
    monkeypatch.setattr(settings, "rate_limit_per_minute", 3)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:

        for _ in range(3):
            resp = await ac.get("/api/v1/overview", headers={"X-Tenant-ID": "tenant_a"})
            assert resp.status_code == 200
        blocked_a = await ac.get("/api/v1/overview", headers={"X-Tenant-ID": "tenant_a"})
        assert blocked_a.status_code == 429

        resp_b = await ac.get("/api/v1/overview", headers={"X-Tenant-ID": "tenant_b"})
        assert resp_b.status_code == 200
