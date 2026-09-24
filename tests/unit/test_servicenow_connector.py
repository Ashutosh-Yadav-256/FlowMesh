"""
Unit Tests for FlowMesh ServiceNow Enterprise Connector
Validates Connector Protocol conformance, 4-point verification, and Table API operations.
"""

import pytest
from connectors.servicenow.connector import ServiceNowConnector
from flowmesh_connector.protocol import ConnectionSpec, Operation


@pytest.fixture
def servicenow_conn_spec() -> ConnectionSpec:
    return ConnectionSpec(
        id="conn_snow_test",
        tenant_id="tenant_acme",
        type="servicenow",
        name="Acme Corporate ServiceNow Instance",
        config={
            "instance": "acmedev",
            "instance_url": "https://acmedev.service-now.com",
            "timeout_seconds": 15.0,
        },
        credentials={
            "username": "svc_flowmesh",
            "password": "SecurePassword123!",
        },
    )


@pytest.mark.asyncio
async def test_servicenow_conformance(servicenow_conn_spec: ConnectionSpec):
    connector = ServiceNowConnector()
    assert connector.type == "servicenow"

    ops = connector.operations()
    op_names = [o.name for o in ops]
    assert "create_incident" in op_names
    assert "get_incident" in op_names
    assert "create_change_request" in op_names
    assert "query_cmdb_ci" in op_names


@pytest.mark.asyncio
async def test_servicenow_4point_verification(servicenow_conn_spec: ConnectionSpec):
    connector = ServiceNowConnector()
    result = await connector.test(servicenow_conn_spec)

    assert result.success is True
    assert len(result.steps) == 4
    step_names = [s.name for s in result.steps]
    assert "Network Connectivity" in step_names
    assert "Authentication" in step_names
    assert "Permissions & Scope" in step_names
    assert "Schema Discovery" in step_names
    assert all(s.status == "passed" for s in result.steps)


@pytest.mark.asyncio
async def test_servicenow_schema_discovery(servicenow_conn_spec: ConnectionSpec):
    connector = ServiceNowConnector()
    graph = await connector.discover(servicenow_conn_spec)

    table_names = [t.table_name for t in graph.entities]
    assert "incident" in table_names
    assert "change_request" in table_names
    assert "cmdb_ci" in table_names


@pytest.mark.asyncio
async def test_servicenow_operations(servicenow_conn_spec: ConnectionSpec):
    connector = ServiceNowConnector()

    # 1. Create Incident
    op_inc = Operation(
        id="op_inc_1",
        name="create_incident",
        parameters={"short_description": "Network latency spike on Edge Agent", "urgency": 1, "impact": 1},
    )
    res_inc = await connector.execute(servicenow_conn_spec, op_inc)
    assert res_inc.success is True
    assert "number" in res_inc.data
    assert res_inc.data["short_description"] == "Network latency spike on Edge Agent"

    # 2. Get Incident
    op_get = Operation(id="op_inc_2", name="get_incident", parameters={"number": res_inc.data["number"]})
    res_get = await connector.execute(servicenow_conn_spec, op_get)
    assert res_get.success is True
    assert res_get.data["number"] == res_inc.data["number"]

    # 3. Create Change Request
    op_chg = Operation(
        id="op_chg_1",
        name="create_change_request",
        parameters={"short_description": "Upgrade edge daemons to v1.2", "type": "Normal", "risk": 2},
    )
    res_chg = await connector.execute(servicenow_conn_spec, op_chg)
    assert res_chg.success is True
    assert res_chg.data["approval"] == "approved"

    # 4. Query CMDB CI
    op_ci = Operation(id="op_ci_1", name="query_cmdb_ci", parameters={"class_name": "cmdb_ci_server"})
    res_ci = await connector.execute(servicenow_conn_spec, op_ci)
    assert res_ci.success is True
    assert len(res_ci.data) >= 1
