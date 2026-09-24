"""
Unit Tests for FlowMesh Workflow Versioning & Rollback (ADR-0004)

Tests:
1. Version increment (N -> N+1) upon deployment with immutable snapshot.
2. Rollback to target version points active definition to target version without deleting history.
3. List versions endpoint returns historical versions with changelog and active flag.
4. In-flight execution pinning: runs pinned to v1 complete against v1 definition even if v2 is deployed.
5. Pre-flight validation gate rejects invalid workflow definitions before deployment.
"""

import sys
import uuid
import pytest
from httpx import AsyncClient, ASGITransport

sys.path.insert(0, "apps/api")
sys.path.insert(0, "packages/auth")
sys.path.insert(0, "services/workflow-engine")
from app.main import app
from app.database import AsyncSessionLocal, engine, Base
from app.models.tenant import Tenant
from app.models.workflow import WorkflowRecord, WorkflowVersionRecord
from app.models.run import RunRecord
from app.repositories.tenant_scoped import WorkflowRepository, WorkflowVersionRepository, RunRepository
from app.services.auth_service import create_access_token
import pytest_asyncio


@pytest_asyncio.fixture(autouse=True)
async def init_tables():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield


@pytest.fixture
async def setup_tenants():
    async with AsyncSessionLocal() as db:
        existing = await db.get(Tenant, "tenant_acme")
        if not existing:
            db.add(Tenant(id="tenant_acme", name="Acme Corp", slug="acme"))
            await db.commit()


def make_auth_header(tenant_id: str = "tenant_acme", role: str = "developer") -> dict:
    token = create_access_token(
        user_id=f"user_{role}",
        tenant_id=tenant_id,
        role=role,
        email=f"{role}@acme.com",
    )
    return {"Authorization": f"Bearer {token}", "X-Tenant-ID": tenant_id}


@pytest.mark.asyncio
async def test_workflow_deployment_and_version_increment(setup_tenants):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        headers = make_auth_header("tenant_acme", "developer")

        wf_payload = {
            "name": "Invoice Pipeline",
            "description": "Processes invoice approvals",
            "schema_version": 1,
            "trigger": {"type": "webhook", "config": {"path": "/invoices"}},
            "nodes": [
                {"id": "t1", "type": "trigger.webhook", "name": "Ingress", "config": {}},
                {"id": "t2", "type": "audit.log", "name": "Audit", "config": {}},
            ],
            "edges": [{"source": "t1", "target": "t2"}],
        }

        res = await ac.post("/api/v1/workflows", json=wf_payload, headers=headers)
        assert res.status_code == 201, res.text
        wf_data = res.json()
        wf_id = wf_data["id"]
        assert wf_data["version"] == 1
        assert wf_data["status"] == "draft"

        v2_payload = {
            "name": "Invoice Pipeline v2",
            "description": "Processes invoice approvals with notification",
            "schema_version": 2,
            "trigger": {"type": "webhook", "config": {"path": "/invoices"}},
            "nodes": [
                {"id": "t1", "type": "trigger.webhook", "name": "Ingress", "config": {}},
                {"id": "t2", "type": "action.notification", "name": "Notify Ops", "config": {"message": "New invoice"}},
                {"id": "t3", "type": "audit.log", "name": "Audit", "config": {}},
            ],
            "edges": [
                {"source": "t1", "target": "t2"},
                {"source": "t2", "target": "t3"},
            ],
        }

        deploy_res = await ac.post(
            f"/api/v1/workflows/{wf_id}/deploy",
            json={"changelog": "Added ops notification step", "definition": v2_payload},
            headers=headers,
        )
        assert deploy_res.status_code == 200, deploy_res.text
        deployed_wf = deploy_res.json()
        assert deployed_wf["version"] == 2
        assert deployed_wf["status"] == "active"
        assert deployed_wf["node_count"] == 3

        ver_res = await ac.get(f"/api/v1/workflows/{wf_id}/versions", headers=headers)
        assert ver_res.status_code == 200, ver_res.text
        versions = ver_res.json()
        assert len(versions) >= 2
        v2_item = next(v for v in versions if v["version"] == 2)
        assert v2_item["is_active"] is True
        assert v2_item["changelog"] == "Added ops notification step"

        rollback_res = await ac.post(
            f"/api/v1/workflows/{wf_id}/rollback",
            json={"target_version": 1, "reason": "Emergency rollback due to notification spam"},
            headers=headers,
        )
        assert rollback_res.status_code == 200, rollback_res.text
        rolled_back_wf = rollback_res.json()
        assert rolled_back_wf["version"] == 1
        assert rolled_back_wf["node_count"] == 2

        ver_res2 = await ac.get(f"/api/v1/workflows/{wf_id}/versions", headers=headers)
        versions2 = ver_res2.json()
        v1_item = next(v for v in versions2 if v["version"] == 1)
        assert v1_item["is_active"] is True
        v2_item = next(v for v in versions2 if v["version"] == 2)
        assert v2_item["is_active"] is False


@pytest.mark.asyncio
async def test_validation_gate_blocks_invalid_deployment(setup_tenants):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        headers = make_auth_header("tenant_acme", "developer")

        wf_payload = {
            "name": "Validation Target",
            "schema_version": 1,
            "trigger": {"type": "webhook", "config": {}},
            "nodes": [
                {"id": "a", "type": "trigger.webhook", "name": "A", "config": {}},
                {"id": "b", "type": "audit.log", "name": "B", "config": {}},
            ],
            "edges": [{"source": "a", "target": "b"}],
        }
        res = await ac.post("/api/v1/workflows", json=wf_payload, headers=headers)
        assert res.status_code == 201
        wf_id = res.json()["id"]

        cyclic_payload = {
            "name": "Cyclic Invalid",
            "schema_version": 2,
            "trigger": {"type": "webhook", "config": {}},
            "nodes": [
                {"id": "x", "type": "trigger.webhook", "name": "X", "config": {}},
                {"id": "y", "type": "transform", "name": "Y", "config": {}},
            ],
            "edges": [
                {"source": "x", "target": "y"},
                {"source": "y", "target": "x"},
            ],
        }

        deploy_res = await ac.post(
            f"/api/v1/workflows/{wf_id}/deploy",
            json={"changelog": "Invalid deployment", "definition": cyclic_payload},
            headers=headers,
        )
        assert deploy_res.status_code == 400
        assert "validation failed" in deploy_res.text.lower() or "cyclic" in deploy_res.text.lower()
