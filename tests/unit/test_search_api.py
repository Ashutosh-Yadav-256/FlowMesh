import sys
import pytest
from httpx import AsyncClient, ASGITransport

sys.path.insert(0, "apps/api")
sys.path.insert(0, "packages/search-engine")
sys.path.insert(0, "packages/auth")
from app.main import app


@pytest.mark.asyncio
async def test_search_api_workflow_connection_and_runs():
    headers = {"X-Tenant-ID": "tenant_search_test"}
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:

        seed_resp = await ac.post("/api/v1/demo/seed", headers=headers)
        assert seed_resp.status_code == 200

        search_pg = await ac.get("/api/v1/search?q=postgres", headers=headers)
        assert search_pg.status_code == 200
        pg_data = search_pg.json()
        assert pg_data["total_hits"] >= 1
        assert any("postgres" in r["title"].lower() or "postgres" in r["description"].lower() for r in pg_data["results"])

        search_prefix = await ac.get("/api/v1/search?q=postg", headers=headers)
        assert search_prefix.status_code == 200
        assert search_prefix.json()["total_hits"] >= 1

        search_typo = await ac.get("/api/v1/search?q=posgtres", headers=headers)
        assert search_typo.status_code == 200
        assert search_typo.json()["total_hits"] >= 1

        search_run = await ac.get("/api/v1/search?q=RUN-92831", headers=headers)
        assert search_run.status_code == 200
        assert any("92831" in r["title"] for r in search_run.json()["results"])

        search_filter = await ac.get("/api/v1/search?q=order&types=workflow", headers=headers)
        assert search_filter.status_code == 200
        for r in search_filter.json()["results"]:
            assert r["entity_type"] == "workflow"

        reindex_resp = await ac.post("/api/v1/search/reindex", headers=headers)
        assert reindex_resp.status_code == 200
        assert reindex_resp.json()["documents_indexed"] >= 5

        reset_resp = await ac.post("/api/v1/demo/reset", headers=headers)
        assert reset_resp.status_code == 200

        search_clean = await ac.get("/api/v1/search?q=order", headers=headers)
        assert search_clean.status_code == 200
        assert search_clean.json()["total_hits"] == 0
