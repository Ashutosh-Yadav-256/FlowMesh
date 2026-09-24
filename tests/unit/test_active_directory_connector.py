"""
Unit Tests for FlowMesh Active Directory & LDAP Connector
Validates identity lifecycle, group membership, and security compliance operations.
"""

import pytest
from connectors.active_directory.connector import ActiveDirectoryConnector
from flowmesh_connector.protocol import ConnectionSpec, Operation


@pytest.fixture
def ad_conn_spec() -> ConnectionSpec:
    return ConnectionSpec(
        id="conn_ad_test",
        tenant_id="tenant_acme",
        type="active_directory",
        name="Acme Corp Active Directory Domain",
        config={
            "domain_controller": "dc01.corp.acme.local",
            "base_dn": "DC=corp,DC=acme,DC=local",
        },
        credentials={
            "bind_dn": "CN=svc_flowmesh,OU=ServiceAccounts,DC=corp,DC=acme,DC=local",
            "password": "DomainAdminSecretPass!",
        },
    )


@pytest.mark.asyncio
async def test_active_directory_conformance(ad_conn_spec: ConnectionSpec):
    connector = ActiveDirectoryConnector()
    assert connector.type == "active_directory"

    ops = connector.operations()
    op_names = [o.name for o in ops]
    assert "get_user" in op_names
    assert "create_user" in op_names
    assert "disable_user" in op_names
    assert "unlock_user" in op_names
    assert "add_user_to_group" in op_names
    assert "audit_stale_accounts" in op_names


@pytest.mark.asyncio
async def test_active_directory_4point_verification(ad_conn_spec: ConnectionSpec):
    connector = ActiveDirectoryConnector()
    result = await connector.test(ad_conn_spec)

    assert result.success is True
    assert len(result.steps) == 4
    step_names = [s.name for s in result.steps]
    assert "Network Connectivity" in step_names
    assert "Authentication" in step_names
    assert "Permissions & Scope" in step_names
    assert "Schema Discovery" in step_names


@pytest.mark.asyncio
async def test_active_directory_operations(ad_conn_spec: ConnectionSpec):
    connector = ActiveDirectoryConnector()

    # 1. Get User
    op_get = Operation(id="op_ad_1", name="get_user", parameters={"sAMAccountName": "jdoe"})
    res_get = await connector.execute(ad_conn_spec, op_get)
    assert res_get.success is True
    assert res_get.data["sAMAccountName"] == "jdoe"
    assert res_get.data["enabled"] is True

    # 2. Disable User
    op_dis = Operation(id="op_ad_2", name="disable_user", parameters={"sAMAccountName": "legacy_contractor"})
    res_dis = await connector.execute(ad_conn_spec, op_dis)
    assert res_dis.success is True
    assert res_dis.data["action"] == "ACCOUNT_DISABLED"

    # 3. Unlock User
    op_unl = Operation(id="op_ad_3", name="unlock_user", parameters={"sAMAccountName": "jdoe"})
    res_unl = await connector.execute(ad_conn_spec, op_unl)
    assert res_unl.success is True
    assert res_unl.data["action"] == "ACCOUNT_UNLOCKED"

    # 4. Add User to Security Group
    op_grp = Operation(id="op_ad_4", name="add_user_to_group", parameters={"sAMAccountName": "jdoe", "group_name": "Sec-Ops"})
    res_grp = await connector.execute(ad_conn_spec, op_grp)
    assert res_grp.success is True
    assert res_grp.data["status"] == "MEMBER_ADDED"

    # 5. Stale Account Compliance Audit
    op_audit = Operation(id="op_ad_5", name="audit_stale_accounts", parameters={"inactive_days": 90})
    res_audit = await connector.execute(ad_conn_spec, op_audit)
    assert res_audit.success is True
    assert len(res_audit.data) >= 1
