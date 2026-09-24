"""
Unit Tests for Enterprise Connectors (Oracle & Microsoft SQL Server)
Verifies protocol conformance, 4-point health verification, discovery graph, and operation execution.
"""

import pytest
from flowmesh_connector.protocol import Connector, ConnectionSpec, Operation
from connectors.oracle.connector import OracleConnector
from connectors.mssql.connector import MsSqlConnector


@pytest.mark.asyncio
async def test_oracle_connector_protocol_and_test():
    connector = OracleConnector()
    assert isinstance(connector, Connector)
    assert connector.type == "oracle"

    spec = ConnectionSpec(
        id="conn_oracle_test",
        tenant_id="tenant_finance",
        type="oracle",
        name="Oracle Production ERP",
        config={"host": "127.0.0.1", "port": 1521, "service_name": "ORCLPDB1", "schema": "FINANCE"},
        credentials={"username": "apps_user", "password": "secure_password"},
    )

    test_res = await connector.test(spec)
    assert test_res.success is True
    assert len(test_res.steps) == 4
    step_names = [s.name for s in test_res.steps]
    assert "TNS Listener Connectivity" in step_names
    assert "Authentication & Session" in step_names
    assert "Privileges & Tablespace Access" in step_names
    assert "Data Dictionary Discovery" in step_names

    graph = await connector.discover(spec)
    assert len(graph.entities) >= 2
    table_names = [t.table_name for t in graph.entities]
    assert "GL_ACCOUNTS" in table_names
    assert "JOURNAL_ENTRIES" in table_names
    assert len(graph.relationships) == 1

    op = Operation(id="op_1", name="query", parameters={"sql": "SELECT * FROM GL_ACCOUNTS WHERE BALANCE > 0"})
    res = await connector.execute(spec, op)
    assert res.success is True
    assert res.records_affected == 2
    assert "rows" in res.data


@pytest.mark.asyncio
async def test_mssql_connector_protocol_and_test():
    connector = MsSqlConnector()
    assert isinstance(connector, Connector)
    assert connector.type == "mssql"

    spec = ConnectionSpec(
        id="conn_mssql_test",
        tenant_id="tenant_logistics",
        type="mssql",
        name="MS SQL Server Warehouse",
        config={"host": "127.0.0.1", "port": 1433, "database": "WarehouseDB"},
        credentials={"username": "sql_admin", "password": "admin_password"},
    )

    test_res = await connector.test(spec)
    assert test_res.success is True
    assert len(test_res.steps) == 4
    step_names = [s.name for s in test_res.steps]
    assert "TDS Network Connectivity" in step_names
    assert "SQL Authentication & Login" in step_names
    assert "Database Permissions" in step_names
    assert "Catalog Metadata Discovery" in step_names

    graph = await connector.discover(spec)
    assert len(graph.entities) >= 2
    table_names = [t.table_name for t in graph.entities]
    assert "Customers" in table_names
    assert "Orders" in table_names

    op = Operation(id="op_2", name="insert", parameters={"table": "Orders", "record": {"CustomerID": 1, "TotalAmount": 250.00}})
    res = await connector.execute(spec, op)
    assert res.success is True
    assert res.records_affected == 1
    assert res.data["status"] == "INSERTED"
