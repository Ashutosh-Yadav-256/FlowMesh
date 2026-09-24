"""
Unit Tests for FlowMesh Windows Server Administration & PowerShell Runner
Validates PowerShell cmdlets, Service control, Event Log parsing, and WindowsAdminConnector.
"""

import pytest
from flowmesh_connector.powershell_runner import PowerShellRunner
from connectors.windows_admin.connector import WindowsAdminConnector
from flowmesh_connector.protocol import ConnectionSpec, Operation


@pytest.fixture
def win_conn_spec() -> ConnectionSpec:
    return ConnectionSpec(
        id="conn_win_test",
        tenant_id="tenant_acme",
        type="windows_admin",
        name="Acme Production Windows Server Cluster",
        config={"host": "win-app-01.corp.acme.local"},
        credentials={"username": "Administrator", "password": "AdminSecretPassword!"},
    )


def test_powershell_runner_script_execution():
    runner = PowerShellRunner()
    res = runner.execute_script("Write-Output 'FlowMesh Agent Test'")
    assert res.success is True
    assert res.exit_code == 0
    assert "FlowMesh" in str(res.data or res.stdout)


def test_powershell_service_management():
    runner = PowerShellRunner()
    svc = runner.get_windows_service("wuauserv")
    assert "Status" in svc or "Name" in svc

    res_restart = runner.manage_windows_service("spooler", "restart")
    assert res_restart["service"] == "spooler"
    assert res_restart["action"] == "restart"


def test_powershell_event_logs_and_metrics():
    runner = PowerShellRunner()
    logs = runner.query_event_logs(log_name="Application", max_events=2)
    assert isinstance(logs, list)
    assert len(logs) >= 1

    health = runner.get_system_health()
    assert "TotalVisibleMemorySize" in health or "Version" in health

    tasks = runner.get_scheduled_tasks()
    assert isinstance(tasks, list)


@pytest.mark.asyncio
async def test_windows_admin_connector_conformance(win_conn_spec: ConnectionSpec):
    connector = WindowsAdminConnector()
    assert connector.type == "windows_admin"

    # 4-point verification
    test_res = await connector.test(win_conn_spec)
    assert test_res.success is True
    assert len(test_res.steps) == 4

    # Discovery
    graph = await connector.discover(win_conn_spec)
    table_names = [t.table_name for t in graph.entities]
    assert "services" in table_names
    assert "event_logs" in table_names
    assert "scheduled_tasks" in table_names

    # Execute service check
    op_svc = Operation(id="op_win_1", name="get_service", parameters={"service_name": "wuauserv"})
    res_svc = await connector.execute(win_conn_spec, op_svc)
    assert res_svc.success is True

    # Execute event logs
    op_logs = Operation(id="op_win_2", name="get_event_logs", parameters={"max_events": 2})
    res_logs = await connector.execute(win_conn_spec, op_logs)
    assert res_logs.success is True

    # Execute custom powershell script
    op_ps = Operation(id="op_win_3", name="execute_powershell_script", parameters={"script": "$x = 40 + 2; Write-Output $x"})
    res_ps = await connector.execute(win_conn_spec, op_ps)
    assert res_ps.success is True
