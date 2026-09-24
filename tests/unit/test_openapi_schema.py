import pytest
from httpx import AsyncClient, ASGITransport
import sys

sys.path.insert(0, "apps/api")
sys.path.insert(0, "packages/auth")

from app.main import app


@pytest.mark.asyncio
async def test_openapi_schema_endpoint():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        resp = await ac.get("/openapi.json")
        assert resp.status_code == 200
        schema = resp.json()

        assert schema.get("openapi", "").startswith("3.")
        assert "info" in schema
        assert schema["info"]["title"] == "FlowMesh API Gateway"
        assert "paths" in schema

        paths = schema["paths"]

        expected_endpoints = [
            "/health",
            "/ready",
            "/api/v1/overview",
            "/api/v1/connections",
            "/api/v1/workflows",
            "/api/v1/runs",
            "/api/v1/incidents",
            "/api/v1/incidents/dlq",
            "/api/v1/events",
            "/api/v1/audit",
            "/api/v1/search",
            "/api/v1/agents",
            "/api/v1/auth/token",
            "/api/v1/auth/me",
        ]

        for ep in expected_endpoints:
            assert ep in paths, f"Expected endpoint '{ep}' not found in OpenAPI schema"

        assert "components" in schema
        assert "schemas" in schema["components"]
        schemas = schema["components"]["schemas"]

        expected_schemas = [
            "ConnectionResponse",
            "WorkflowSummary",
            "WorkflowDetail",
            "RunSummary",
            "IncidentDetail",
            "DeadLetterItem",
            "EventLogItem",
            "AuditRecord",
        ]

        for s in expected_schemas:
            assert s in schemas, f"Expected schema definition '{s}' not found in OpenAPI components"
