"""
Milestone 2 — Connector Protocol & Implementations Test Suite

Tests:
1. PostgresConnector conformance to Connector Protocol.
2. 4-point health verification: Network, Auth, Permissions, Schema Discovery.
3. Postgres schema discovery and relational graph traversal.
4. Postgres operation execution (query, insert, update, delete).
5. RestConnector conformance to Connector Protocol.
6. RestConnector 4-point verification and execution.
7. ConnectorRegistry factory lookup and custom connector registration.
"""

import sys
import pytest

sys.path.insert(0, "packages/connector-sdk")
sys.path.insert(0, "connectors")

from flowmesh_connector.protocol import (
    Connector,
    ConnectionSpec,
    Operation,
    DiscoveryGraph,
    TestResult,
)
from flowmesh_connector.registry import get_connector, register_connector, ConnectorRegistry
from connectors.postgres.connector import PostgresConnector
from connectors.rest.connector import RestConnector


@pytest.mark.asyncio
async def test_postgres_connector_conformance_and_health_check():
    """Validates PostgresConnector satisfies Connector Protocol and runs 4-point test."""
    connector = PostgresConnector()
    assert isinstance(connector, Connector)
    assert connector.type == "postgres"

    spec = ConnectionSpec(
        id="conn_pg_test_01",
        tenant_id="tenant_acme",
        type="postgres",
        name="Production Database",
        config={"host": "10.0.4.12", "port": 5432, "database": "production_orders"},
        credentials={"username": "order_svc", "password": "secure_pass_123"},
        agent_id="agent-prod-01",
    )

    result = await connector.test(spec)
    assert isinstance(result, TestResult)
    assert result.success is True
    assert len(result.steps) == 4

    step_names = [s.name for s in result.steps]
    assert "Network Connectivity" in step_names
    assert "Authentication" in step_names
    assert "Permissions & Scope" in step_names
    assert "Schema Discovery" in step_names

    for step in result.steps:
        assert step.status == "passed"
        assert step.duration_ms > 0
        assert len(step.message) > 5


@pytest.mark.asyncio
async def test_postgres_connector_schema_discovery():
    """Validates PostgreSQL schema discovery produces TableInfo and relationships."""
    connector = PostgresConnector()
    spec = ConnectionSpec(
        id="conn_pg_disc_01",
        tenant_id="tenant_acme",
        type="postgres",
        name="Orders DB",
        config={"database": "production_orders"},
    )

    graph = await connector.discover(spec)
    assert isinstance(graph, DiscoveryGraph)
    assert len(graph.entities) >= 3

    table_names = [t.table_name for t in graph.entities]
    assert "orders" in table_names
    assert "order_items" in table_names
    assert "customers" in table_names

    orders_table = next(t for t in graph.entities if t.table_name == "orders")
    pk_cols = [c.name for c in orders_table.columns if c.is_primary_key]
    assert "id" in pk_cols

    assert len(graph.relationships) >= 2
    assert any(r["source_table"] == "order_items" and r["target_table"] == "orders" for r in graph.relationships)


@pytest.mark.asyncio
async def test_postgres_connector_execute_operations():
    """Validates PostgresConnector executes authorized SQL queries and mutations."""
    connector = PostgresConnector()
    spec = ConnectionSpec(
        id="conn_pg_exec_01",
        tenant_id="tenant_acme",
        type="postgres",
        name="Orders DB",
        config={},
    )

    query_op = Operation(
        id="op_q_01",
        name="query",
        parameters={"sql": "SELECT * FROM orders WHERE status = :status", "params": {"status": "CONFIRMED"}},
    )
    q_result = await connector.execute(spec, query_op)
    assert q_result.success is True
    assert q_result.duration_ms > 0
    assert len(q_result.data["rows"]) == 2
    assert q_result.records_affected == 2

    insert_op = Operation(
        id="op_ins_01",
        name="insert",
        parameters={"table": "orders", "records": [{"id": "ord_1003", "total_cents": 4500}]},
    )
    ins_result = await connector.execute(spec, insert_op)
    assert ins_result.success is True
    assert ins_result.data["inserted_count"] == 1

    bad_op = Operation(id="op_bad", name="query", parameters={})
    bad_result = await connector.execute(spec, bad_op)
    assert bad_result.success is False
    assert "Missing required 'sql' parameter" in bad_result.error


@pytest.mark.asyncio
async def test_rest_connector_conformance_and_execution():
    """Validates RestConnector satisfies Connector Protocol, 4-point check, and execution."""
    connector = RestConnector()
    assert isinstance(connector, Connector)
    assert connector.type == "rest"

    spec = ConnectionSpec(
        id="conn_rest_test_01",
        tenant_id="tenant_acme",
        type="rest",
        name="Warehouse API",
        config={"base_url": "https://internal-warehouse.corp.local/v2", "timeout_seconds": 5},
        credentials={"token": "bearer_sample_token_live"},
        agent_id="agent-prod-01",
    )

    test_result = await connector.test(spec)
    assert test_result.success is True
    assert len(test_result.steps) == 4

    graph = await connector.discover(spec)
    assert len(graph.entities) >= 2
    assert any(t.table_name == "/items" for t in graph.entities)

    get_op = Operation(
        id="op_http_01",
        name="get",
        parameters={"endpoint": "/items/item_992"},
    )
    exec_result = await connector.execute(spec, get_op)
    assert exec_result.success is True
    assert exec_result.data["status_code"] == 200


def test_connector_registry_lookup_and_registration():
    """Validates registry retrieval and dynamic registration of custom connectors."""
    reg = ConnectorRegistry()
    assert reg.get("postgres") is not None
    assert reg.get("rest") is not None
    assert reg.get("unsupported_type") is None

    class CustomKafkaConnector:
        type = "kafka"
        async def test(self, conn): pass
        async def discover(self, conn): pass
        async def execute(self, conn, op): pass
        def operations(self): return []

    reg.register("kafka", CustomKafkaConnector())
    assert reg.get("kafka") is not None
    assert "kafka" in reg.list_types()
