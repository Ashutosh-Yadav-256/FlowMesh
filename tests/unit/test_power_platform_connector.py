"""
Unit tests for FlowMesh Microsoft Power Platform Connector
Tests 4-point verification, Power Automate flow triggers, and Dataverse OData queries.
"""

import pytest
from flowmesh_connector.protocol import ConnectionSpec, Operation
from connectors.power_platform.connector import PowerPlatformConnector


@pytest.fixture
def power_platform_conn_spec() -> ConnectionSpec:
    return ConnectionSpec(
        id="conn_power_plat_test",
        tenant_id="tenant_acme",
        type="power_platform",
        name="Acme Corporate Microsoft Power Platform & Dataverse",
        config={
            "environment_id": "Default-98213840-acme",
            "environment_url": "https://acmeprod.crm.dynamics.com",
            "region": "unitedstates",
        },
        credentials={
            "tenant_id": "entra-tenant-acme",
            "client_id": "power-platform-flowmesh-client",
            "client_secret": "PowerPlatformClientSecret123!",
        },
        agent_id=None,
    )


@pytest.mark.asyncio
async def test_power_platform_conformance(power_platform_conn_spec: ConnectionSpec):
    connector = PowerPlatformConnector()
    assert connector.type == "power_platform"

    # 4-point verification
    test_res = await connector.test(power_platform_conn_spec)
    assert test_res.success is True
    assert len(test_res.steps) == 4
    step_names = [s.name for s in test_res.steps]
    assert any("Endpoint Connectivity" in name for name in step_names)
    assert any("Entra ID Authentication" in name for name in step_names)
    assert any("Environment Scopes" in name for name in step_names)
    assert any("Flow & Entity Catalog" in name for name in step_names)

    # Schema discovery
    graph = await connector.discover(power_platform_conn_spec)
    table_names = [t.table_name for t in graph.entities]
    assert "flows" in table_names
    assert "dataverse_entities" in table_names


@pytest.mark.asyncio
async def test_power_platform_operations(power_platform_conn_spec: ConnectionSpec):
    connector = PowerPlatformConnector()

    # 1. Trigger Flow
    op_flow = Operation(
        id="op_pp_1",
        name="trigger_flow",
        parameters={
            "flow_id": "flow-invoice-approval-99",
            "payload": {"invoice_id": "INV-2026-0042", "amount": 12500.0, "currency": "USD"},
        },
    )
    res_flow = await connector.execute(power_platform_conn_spec, op_flow)
    assert res_flow.success is True
    assert "flow_run_id" in res_flow.data
    assert res_flow.data["status"] == "Running"

    # 2. Get Flow Run
    run_id = res_flow.data["flow_run_id"]
    op_run = Operation(
        id="op_pp_2",
        name="get_flow_run",
        parameters={"flow_run_id": run_id},
    )
    res_run = await connector.execute(power_platform_conn_spec, op_run)
    assert res_run.success is True
    assert res_run.data["status"] == "Succeeded"
    assert "outputs" in res_run.data
    assert res_run.data["outputs"]["approval_decision"] == "Approved"

    # 3. Query Dataverse
    op_query = Operation(
        id="op_pp_3",
        name="query_dataverse",
        parameters={
            "entity_name": "accounts",
            "filter": "revenue gt 1000000",
            "top": 5,
        },
    )
    res_query = await connector.execute(power_platform_conn_spec, op_query)
    assert res_query.success is True
    assert "records" in res_query.data
    assert len(res_query.data["records"]) >= 1

    # 4. Create Dataverse Record
    op_create = Operation(
        id="op_pp_4",
        name="create_dataverse_record",
        parameters={
            "entity_name": "contacts",
            "record_data": {"firstname": "John", "lastname": "Doe", "emailaddress1": "jdoe@acme.corp"},
        },
    )
    res_create = await connector.execute(power_platform_conn_spec, op_create)
    assert res_create.success is True
    assert res_create.data["status"] == "CREATED"
    assert "record_id" in res_create.data

    # 5. List Flows
    op_list = Operation(id="op_pp_5", name="list_flows", parameters={})
    res_list = await connector.execute(power_platform_conn_spec, op_list)
    assert res_list.success is True
    assert len(res_list.data) >= 2
