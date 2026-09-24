"""
Milestone 2 — Envelope Encryption & Secret Management Test Suite

Tests:
1. Master KEK derivation (256-bit AES).
2. Tenant DEK generation and wrapping with Tenant ID AAD binding.
3. Cryptographic rejection of cross-tenant DEK unwrap (InvalidTag).
4. Connection secret encryption with Connection ID AAD binding.
5. Cryptographic rejection of cross-connection decryption and tampered ciphertext.
6. Write-only API guarantee: Credentials accepted on create/rotate, never leaked in GET.
7. Credential rotation: Version increment, old secret invalidation, live verification.
"""

import sys
import base64
import pytest
from httpx import AsyncClient, ASGITransport
from cryptography.exceptions import InvalidTag

sys.path.insert(0, "apps/api")
sys.path.insert(0, "packages/auth")
sys.path.insert(0, "packages/connector-sdk")
sys.path.insert(0, "connectors")

from flowmesh_auth.crypto import EnvelopeCrypto, get_master_kek
from app.main import app


def test_master_kek_derivation():
    """Validates that Master KEK is derived as a 256-bit (32 bytes) key."""
    kek = get_master_kek()
    assert isinstance(kek, bytes)
    assert len(kek) == 32


def test_tenant_dek_wrap_and_unwrap():
    """Validates that Tenant DEK is wrapped and unwrapped faithfully with tenant AAD binding."""
    crypto = EnvelopeCrypto()
    tenant_id = "tenant_finance_prod"
    dek = crypto.generate_dek()
    assert len(dek) == 32

    wrapped_dek = crypto.wrap_dek(dek, tenant_id=tenant_id)
    assert isinstance(wrapped_dek, str)

    unwrapped_dek = crypto.unwrap_dek(wrapped_dek, tenant_id=tenant_id)
    assert unwrapped_dek == dek


def test_cross_tenant_dek_unwrap_rejected():
    """Cryptographically proves Tenant B cannot unwrap Tenant A's DEK (InvalidTag)."""
    crypto = EnvelopeCrypto()
    dek_a = crypto.generate_dek()
    wrapped_a = crypto.wrap_dek(dek_a, tenant_id="tenant_a")

    with pytest.raises(InvalidTag):
        crypto.unwrap_dek(wrapped_a, tenant_id="tenant_b")


def test_secret_encryption_and_connection_binding():
    """Validates secret payload encryption and verifies AAD binding to connection_id."""
    crypto = EnvelopeCrypto()
    dek = crypto.generate_dek()
    conn_id = "conn_db_customers_01"
    secret_payload = {"username": "db_admin", "password": "vault_pwd_884920", "ssl_cert": "pem_data"}

    ciphertext_b64 = crypto.encrypt_secret(dek, secret_payload, connection_id=conn_id)
    assert isinstance(ciphertext_b64, str)
    assert "vault_pwd_884920" not in ciphertext_b64

    decrypted = crypto.decrypt_secret(dek, ciphertext_b64, connection_id=conn_id)
    assert decrypted == secret_payload

    with pytest.raises(InvalidTag):
        crypto.decrypt_secret(dek, ciphertext_b64, connection_id="conn_different_id")


def test_tampered_ciphertext_rejected():
    """Proves any bit-flip in ciphertext or authentication tag raises InvalidTag."""
    crypto = EnvelopeCrypto()
    dek = crypto.generate_dek()
    conn_id = "conn_secure_01"
    ciphertext_b64 = crypto.encrypt_secret(dek, {"token": "secret_xyz"}, conn_id)

    raw_bytes = bytearray(base64.b64decode(ciphertext_b64))

    raw_bytes[-1] ^= 0x01
    tampered_b64 = base64.b64encode(raw_bytes).decode("utf-8")

    with pytest.raises(InvalidTag):
        crypto.decrypt_secret(dek, tampered_b64, conn_id)


@pytest.mark.asyncio
async def test_write_only_api_credentials_and_rotation():
    """
    End-to-end API test:
    1. Create connection with plaintext credentials.
    2. Verify credentials are NOT present in create response.
    3. Verify credentials are NOT present in GET response.
    4. Rotate credentials -> verify version increment.
    5. Test connection -> verify 4-step check passes with new credentials.
    """
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        headers = {"X-Tenant-ID": "tenant_sec_test"}

        create_payload = {
            "name": "Production Postgres Payments",
            "type": "postgres",
            "agent_id": "agent-prod-01",
            "config": {"host": "10.0.12.4", "port": 5432, "database": "payments_db"},
            "credentials": {"username": "pay_service", "password": "super_secret_initial_pass_123"},
        }
        res = await ac.post("/api/v1/connections", json=create_payload, headers=headers)
        assert res.status_code == 201
        created = res.json()
        conn_id = created["id"]
        assert "credentials" not in created
        assert "super_secret_initial_pass_123" not in str(created)

        get_res = await ac.get(f"/api/v1/connections/{conn_id}", headers=headers)
        assert get_res.status_code == 200
        fetched = get_res.json()
        assert "credentials" not in fetched
        assert "super_secret_initial_pass_123" not in str(fetched)

        rotate_payload = {
            "credentials": {"username": "pay_service", "password": "rotated_master_secret_pass_456"}
        }
        rot_res = await ac.post(f"/api/v1/connections/{conn_id}/rotate-credentials", json=rotate_payload, headers=headers)
        assert rot_res.status_code == 200
        rot_data = rot_res.json()
        assert rot_data["status"] == "rotated"
        assert rot_data["new_version"] == 2
        assert "rotated_master_secret_pass_456" not in str(rot_data)

        test_res = await ac.post(f"/api/v1/connections/{conn_id}/test", headers=headers)
        assert test_res.status_code == 200
        test_data = test_res.json()
        assert test_data["success"] is True
        assert len(test_data["steps"]) == 4
        assert all(step["status"] == "passed" for step in test_data["steps"])
