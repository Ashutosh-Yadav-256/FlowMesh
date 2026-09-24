"""
Unit tests for FlowMesh Edge Agent Management API

Validates:
1. Zero-touch enrollment token generation & RBAC enforcement.
2. Agent registration handshake with Ed25519 key exchange.
3. Single-use enrollment token consumption.
4. Heartbeat telemetry ingestion & automatic staleness detection (> 15s marked OFFLINE).
5. Cryptographically signed command dispatching with Ed25519 signature verification.
6. Outbound long-polling & execution result recording.
7. Strict multi-tenant isolation.
"""

import sys
from datetime import datetime, timezone, timedelta
import pytest
from httpx import AsyncClient, ASGITransport

sys.path.insert(0, "apps/api")
sys.path.insert(0, "packages/auth")
from app.main import app
from app.database import AsyncSessionLocal, engine, Base
from app.models.tenant import Tenant
from app.repositories.tenant_scoped import AgentRepository
from app.services.auth_service import create_access_token
from flowmesh_auth.signing import (
    generate_ed25519_keypair,
    verify_ed25519_signature,
    get_control_plane_signer,
)
import pytest_asyncio


@pytest_asyncio.fixture(autouse=True)
async def init_tables():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield


@pytest_asyncio.fixture
async def setup_tenants():
    async with AsyncSessionLocal() as db:

        for tid, name in [("tenant_alpha", "Tenant Alpha"), ("tenant_beta", "Tenant Beta")]:
            existing = await db.get(Tenant, tid)
            if not existing:
                db.add(Tenant(id=tid, name=name, slug=tid))
        await db.commit()


def make_auth_header(tenant_id: str, role: str = "operator") -> dict:
    token = create_access_token(
        user_id=f"user_{role}",
        tenant_id=tenant_id,
        role=role,
        email=f"{role}@flowmesh.dev",
    )
    return {"Authorization": f"Bearer {token}", "X-Tenant-ID": tenant_id}


@pytest.mark.asyncio
async def test_agent_enrollment_lifecycle(setup_tenants):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        headers_a = make_auth_header("tenant_alpha", "operator")

        token_resp = await ac.post("/api/v1/agents/enrollment-token", headers=headers_a)
        assert token_resp.status_code == 200
        token_data = token_resp.json()
        assert token_data["enrollment_token"].startswith("flm_enroll_")
        assert token_data["expires_in_seconds"] == 3600
        enroll_token = token_data["enrollment_token"]

        _, agent_pub = generate_ed25519_keypair()
        enroll_req = {
            "enrollment_token": enroll_token,
            "name": "edge-gateway-01",
            "version": "v0.5.0",
            "public_key": agent_pub,
        }
        resp = await ac.post("/api/v1/agents/enroll", json=enroll_req)
        assert resp.status_code == 200
        enrolled = resp.json()
        assert enrolled["tenant_id"] == "tenant_alpha"
        assert enrolled["status"] == "ONLINE"
        assert "agent_id" in enrolled
        agent_id = enrolled["agent_id"]

        signer = get_control_plane_signer()
        assert enrolled["control_plane_public_key"] == signer.public_key_b64

        re_enroll = await ac.post("/api/v1/agents/enroll", json=enroll_req)
        assert re_enroll.status_code == 404

        hb_payload = {
            "cpu_percent": 18.2,
            "memory_percent": 42.5,
            "queue_depth": 3,
            "connectors": [
                {"name": "PostgreSQL Primary", "status": "healthy", "type": "postgres"},
                {"name": "Internal Logistics API", "status": "healthy", "type": "rest"},
            ],
        }
        hb_resp = await ac.post(
            f"/api/v1/agents/{agent_id}/heartbeat",
            json=hb_payload,
            headers={"X-Tenant-ID": "tenant_alpha"},
        )
        assert hb_resp.status_code == 200
        assert hb_resp.json()["status"] == "acknowledged"

        detail_resp = await ac.get(f"/api/v1/agents/{agent_id}", headers=headers_a)
        assert detail_resp.status_code == 200
        detail = detail_resp.json()
        assert detail["id"] == agent_id
        assert detail["status"] == "online"
        assert detail["cpu_percent"] == 18.2
        assert detail["queue_depth"] == 3
        assert len(detail["connectors"]) == 2
        assert detail["last_heartbeat_seconds_ago"] < 5


@pytest.mark.asyncio
async def test_signed_command_dispatch_and_poll(setup_tenants):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        headers_a = make_auth_header("tenant_alpha", "operator")

        token_resp = await ac.post("/api/v1/agents/enrollment-token", headers=headers_a)
        enroll_token = token_resp.json()["enrollment_token"]
        enroll_resp = await ac.post(
            "/api/v1/agents/enroll",
            json={"enrollment_token": enroll_token, "name": "dispatch-test-agent", "version": "v0.5.0"},
        )
        agent_id = enroll_resp.json()["agent_id"]

        cmd_req = {
            "connector": "postgres",
            "connection_id": "orders-db",
            "operation": "query",
            "resource": "orders",
            "limit": 50,
            "payload": {"filter": "status=open"},
        }
        dispatch_resp = await ac.post(f"/api/v1/agents/{agent_id}/commands", json=cmd_req, headers=headers_a)
        assert dispatch_resp.status_code == 200
        dispatched = dispatch_resp.json()
        cmd_id = dispatched["command_id"]
        assert dispatched["status"] == "QUEUED"
        sig_b64 = dispatched["signature"]
        assert sig_b64 is not None

        signer = get_control_plane_signer()
        expected_cmd = {
            "id": cmd_id,
            "type": "connector.execute",
            "connector": "postgres",
            "connection_id": "orders-db",
            "operation": "query",
            "resource": "orders",
            "limit": 50,
            "payload": {"filter": "status=open"},
        }
        assert verify_ed25519_signature(signer.public_key_b64, expected_cmd, sig_b64) is True

        poll_resp = await ac.get(
            f"/api/v1/agents/{agent_id}/commands/poll",
            headers={"X-Tenant-ID": "tenant_alpha"},
        )
        assert poll_resp.status_code == 200
        polled = poll_resp.json()
        assert len(polled) == 1
        assert polled[0]["command"]["id"] == cmd_id
        assert polled[0]["signature"] == sig_b64

        poll_again = await ac.get(
            f"/api/v1/agents/{agent_id}/commands/poll",
            headers={"X-Tenant-ID": "tenant_alpha"},
        )
        assert poll_again.status_code == 200
        assert len(poll_again.json()) == 0

        result_req = {
            "status": "COMPLETED",
            "result": {"rows_read": 50, "execution_time_ms": 12.4},
            "duration_ms": 12.4,
        }
        res_resp = await ac.post(
            f"/api/v1/agents/{agent_id}/commands/{cmd_id}/result",
            json=result_req,
            headers={"X-Tenant-ID": "tenant_alpha"},
        )
        assert res_resp.status_code == 200
        assert res_resp.json()["execution_status"] == "COMPLETED"


@pytest.mark.asyncio
async def test_agent_cross_tenant_isolation(setup_tenants):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        headers_a = make_auth_header("tenant_alpha", "operator")
        headers_b = make_auth_header("tenant_beta", "operator")

        token_resp = await ac.post("/api/v1/agents/enrollment-token", headers=headers_a)
        enroll_token = token_resp.json()["enrollment_token"]
        enroll_resp = await ac.post(
            "/api/v1/agents/enroll",
            json={"enrollment_token": enroll_token, "name": "alpha-exclusive-agent", "version": "v0.5.0"},
        )
        agent_id_a = enroll_resp.json()["agent_id"]

        resp_a = await ac.get(f"/api/v1/agents/{agent_id_a}", headers=headers_a)
        assert resp_a.status_code == 200

        resp_b = await ac.get(f"/api/v1/agents/{agent_id_a}", headers=headers_b)
        assert resp_b.status_code == 404

        cmd_req = {
            "connector": "postgres",
            "connection_id": "orders-db",
            "operation": "query",
        }
        dispatch_b = await ac.post(f"/api/v1/agents/{agent_id_a}/commands", json=cmd_req, headers=headers_b)
        assert dispatch_b.status_code == 404


@pytest.mark.asyncio
async def test_stale_heartbeat_marked_offline():
    async with AsyncSessionLocal() as db:
        agent_repo = AgentRepository(db, "tenant_alpha")
        now = datetime.now(timezone.utc)

        stale_agent = await agent_repo.create_agent(
            agent_id="agent-stale-test-01",
            name="stale-test-agent",
            version="v0.5.0",
        )
        stale_agent.last_heartbeat_at = now - timedelta(seconds=30)
        stale_agent.status = "ONLINE"
        await db.commit()

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        headers_a = make_auth_header("tenant_alpha", "viewer")
        detail_resp = await ac.get("/api/v1/agents/agent-stale-test-01", headers=headers_a)
        assert detail_resp.status_code == 200
        detail = detail_resp.json()

        assert detail["status"] == "offline"
        assert detail["last_heartbeat_seconds_ago"] >= 30
