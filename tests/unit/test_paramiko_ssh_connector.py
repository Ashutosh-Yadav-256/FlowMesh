"""
Unit Tests for FlowMesh Paramiko SSH & SFTP Connector
Validates SSH remote command execution, SFTP file handling, and protocol conformance.
"""

import pytest
import paramiko
from connectors.ssh.connector import SshParamikoConnector
from flowmesh_connector.protocol import ConnectionSpec, Operation


@pytest.fixture
def ssh_conn_spec() -> ConnectionSpec:
    return ConnectionSpec(
        id="conn_ssh_test",
        tenant_id="tenant_acme",
        type="ssh",
        name="Acme Linux & Windows SSH Fleet",
        config={"host": "linux-worker-01.corp.acme.local", "port": 22},
        credentials={"username": "devops", "password": "SecureSSHPass123!"},
    )


@pytest.mark.asyncio
async def test_ssh_paramiko_conformance(ssh_conn_spec: ConnectionSpec):
    connector = SshParamikoConnector()
    assert connector.type == "ssh"

    ops = connector.operations()
    op_names = [o.name for o in ops]
    assert "exec_command" in op_names
    assert "sftp_upload" in op_names
    assert "sftp_list" in op_names


@pytest.mark.asyncio
async def test_ssh_paramiko_4point_verification(ssh_conn_spec: ConnectionSpec):
    connector = SshParamikoConnector()
    result = await connector.test(ssh_conn_spec)
    assert result.success is True
    assert len(result.steps) == 4
    step_names = [s.name for s in result.steps]
    assert "Network Connectivity" in step_names
    assert "Authentication" in step_names
    assert "Permissions & Scope" in step_names
    assert "Schema Discovery" in step_names


@pytest.mark.asyncio
async def test_ssh_paramiko_operations(ssh_conn_spec: ConnectionSpec):
    connector = SshParamikoConnector()

    # 1. Remote command execution
    op_cmd = Operation(id="op_ssh_1", name="exec_command", parameters={"command": "df -h"})
    res_cmd = await connector.execute(ssh_conn_spec, op_cmd)
    assert res_cmd.success is True
    assert res_cmd.data["exit_code"] == 0
    assert "df -h" in res_cmd.data["command"]

    # 2. SFTP Upload
    op_up = Operation(id="op_ssh_2", name="sftp_upload", parameters={"remote_path": "/var/log/audit.log", "content": "AUDIT_OK"})
    res_up = await connector.execute(ssh_conn_spec, op_up)
    assert res_up.success is True
    assert res_up.data["status"] == "UPLOAD_SUCCESS"

    # 3. SFTP List
    op_ls = Operation(id="op_ssh_3", name="sftp_list", parameters={"remote_dir": "/var/log"})
    res_ls = await connector.execute(ssh_conn_spec, op_ls)
    assert res_ls.success is True
    assert len(res_ls.data) >= 1
