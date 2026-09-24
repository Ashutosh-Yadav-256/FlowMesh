"""
Unit tests for FlowMesh Azure Automation Connector
Tests 4-point verification, runbook orchestration, job polling, and variables.
"""

import pytest
from flowmesh_connector.protocol import ConnectionSpec, Operation
from connectors.azure_automation.connector import AzureAutomationConnector


@pytest.fixture
def azure_auto_conn_spec() -> ConnectionSpec:
    return ConnectionSpec(
        id="conn_az_auto_test",
        tenant_id="tenant_acme",
        type="azure_automation",
        name="Acme Corporate Azure Automation Account",
        config={
            "subscription_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
            "resource_group": "rg-flowmesh-production",
            "automation_account": "aa-flowmesh-prod",
            "location": "eastus2",
        },
        credentials={
            "tenant_id": "entra-tenant-9988",
            "client_id": "spn-flowmesh-automation-client",
            "client_secret": "SuperSecretAzureServicePrincipalKey123!",
        },
        agent_id=None,
    )


@pytest.mark.asyncio
async def test_azure_automation_conformance(azure_auto_conn_spec: ConnectionSpec):
    connector = AzureAutomationConnector()
    assert connector.type == "azure_automation"

    # 4-point verification
    test_res = await connector.test(azure_auto_conn_spec)
    assert test_res.success is True
    assert len(test_res.steps) == 4
    step_names = [s.name for s in test_res.steps]
    assert any("Endpoint Connectivity" in name for name in step_names)
    assert any("Entra ID Authentication" in name for name in step_names)
    assert any("RBAC Scope" in name for name in step_names)
    assert any("Runbook Asset Discovery" in name for name in step_names)

    # Schema discovery
    graph = await connector.discover(azure_auto_conn_spec)
    table_names = [t.table_name for t in graph.entities]
    assert "runbooks" in table_names
    assert "jobs" in table_names
    assert "variables" in table_names


@pytest.mark.asyncio
async def test_azure_automation_operations(azure_auto_conn_spec: ConnectionSpec):
    connector = AzureAutomationConnector()

    # 1. Start Runbook
    op_start = Operation(
        id="op_az_1",
        name="start_runbook",
        parameters={
            "runbook_name": "Patch-WindowsFleet",
            "parameters": {"Environment": "Production", "RebootIfRequired": True},
            "run_on": "HybridWorkerGroup-DMZ",
        },
    )
    res_start = await connector.execute(azure_auto_conn_spec, op_start)
    assert res_start.success is True
    assert "job_id" in res_start.data
    assert res_start.data["runbook_name"] == "Patch-WindowsFleet"
    assert res_start.data["status"] == "Running"

    # 2. Get Job Status
    job_id = res_start.data["job_id"]
    op_stat = Operation(
        id="op_az_2",
        name="get_job_status",
        parameters={"job_id": job_id},
    )
    res_stat = await connector.execute(azure_auto_conn_spec, op_stat)
    assert res_stat.success is True
    assert res_stat.data["status"] == "Completed"
    assert res_stat.data["provisioning_state"] == "Succeeded"

    # 3. Get Job Output
    op_out = Operation(
        id="op_az_3",
        name="get_job_output",
        parameters={"job_id": job_id},
    )
    res_out = await connector.execute(azure_auto_conn_spec, op_out)
    assert res_out.success is True
    assert "output_stream" in res_out.data
    assert "succeeded" in res_out.data["output_stream"].lower()

    # 4. List Runbooks
    op_list = Operation(id="op_az_4", name="list_runbooks", parameters={})
    res_list = await connector.execute(azure_auto_conn_spec, op_list)
    assert res_list.success is True
    assert len(res_list.data) >= 2

    # 5. Get Variable
    op_var = Operation(id="op_az_5", name="get_variable", parameters={"variable_name": "ClusterEndpoint"})
    res_var = await connector.execute(azure_auto_conn_spec, op_var)
    assert res_var.success is True
    assert res_var.data["name"] == "ClusterEndpoint"
    assert "https://" in res_var.data["value"]
