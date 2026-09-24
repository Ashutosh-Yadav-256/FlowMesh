import sys
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport

sys.path.insert(0, "apps/api")
sys.path.insert(0, "packages/auth")

from app.database import engine, Base
from app.main import app


@pytest_asyncio.fixture(autouse=True)
async def init_test_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield


@pytest.mark.asyncio
async def test_auth_token_issuance_and_me():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:

        login_resp = await ac.post("/api/v1/auth/token", json={
            "email": "operator.elena@acme.corp",
            "password": "secure_password_123",
            "tenant_id": "tenant_acme",
            "role": "operator"
        })
        assert login_resp.status_code == 200
        token_data = login_resp.json()
        assert "access_token" in token_data
        assert token_data["role"] == "operator"
        assert token_data["tenant_id"] == "tenant_acme"

        token = token_data["access_token"]
        me_resp = await ac.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
        assert me_resp.status_code == 200
        me_data = me_resp.json()
        assert me_data["email"] == "operator.elena@acme.corp"
        assert me_data["role"] == "operator"
        assert me_data["tenant_id"] == "tenant_acme"


@pytest.mark.asyncio
async def test_tenant_switching():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:

        switch_resp = await ac.post(
            "/api/v1/tenants/switch",
            json={"target_tenant_id": "tenant_beta"},
            headers={"X-Tenant-ID": "tenant_acme"}
        )
        assert switch_resp.status_code == 200
        switch_data = switch_resp.json()
        assert switch_data["active_tenant_id"] == "tenant_beta"
        assert "access_token" in switch_data


@pytest.mark.asyncio
async def test_api_key_creation_and_revocation():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:

        create_resp = await ac.post("/api/v1/api-keys", json={
            "name": "Production Agent Deploy Key",
            "role": "developer"
        })
        assert create_resp.status_code == 201
        key_data = create_resp.json()
        assert key_data["secret_key"] is not None
        assert key_data["key_prefix"].startswith("flm_")
        key_id = key_data["id"]

        list_resp = await ac.get("/api/v1/api-keys")
        assert list_resp.status_code == 200
        keys = list_resp.json()
        matching = next(k for k in keys if k["id"] == key_id)
        assert matching["secret_key"] is None, "SECURITY FAILURE: Plaintext secret returned in list!"

        revoke_resp = await ac.delete(f"/api/v1/api-keys/{key_id}")
        assert revoke_resp.status_code == 204
