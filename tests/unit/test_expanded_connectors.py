"""
Unit Tests for Expanded Enterprise Connectors:
- MySQL / MariaDB
- MongoDB NoSQL
- Enterprise Data Lake / S3 Parquet
- Apache Airflow
"""

import pytest
from flowmesh_connector.protocol import Connector, ConnectionSpec, Operation
from connectors.mysql.connector import MySqlConnector
from connectors.mongodb.connector import MongoDbConnector
from connectors.datalake.connector import DataLakeConnector
from connectors.airflow.connector import AirflowConnector


@pytest.mark.asyncio
async def test_mysql_connector():
    connector = MySqlConnector()
    assert isinstance(connector, Connector)
    assert connector.type == "mysql"

    spec = ConnectionSpec(
        id="conn_mysql_1",
        tenant_id="tenant_web",
        type="mysql",
        name="MySQL Users DB",
        config={"host": "127.0.0.1", "port": 3306, "database": "production_app"},
        credentials={"username": "app_user"},
    )
    test_res = await connector.test(spec)
    assert test_res.success is True
    assert len(test_res.steps) == 4

    graph = await connector.discover(spec)
    assert len(graph.entities) >= 2

    op = Operation(id="op_q", name="query", parameters={"sql": "SELECT * FROM users"})
    res = await connector.execute(spec, op)
    assert res.success is True
    assert res.records_affected == 2


@pytest.mark.asyncio
async def test_mongodb_connector():
    connector = MongoDbConnector()
    assert isinstance(connector, Connector)
    assert connector.type == "mongodb"

    spec = ConnectionSpec(
        id="conn_mongo_1",
        tenant_id="tenant_catalog",
        type="mongodb",
        name="Catalog Store",
        config={"host": "127.0.0.1", "port": 27017, "database": "catalog_store"},
        credentials={"username": "admin"},
    )
    test_res = await connector.test(spec)
    assert test_res.success is True
    assert len(test_res.steps) == 4

    graph = await connector.discover(spec)
    assert len(graph.entities) >= 2

    op = Operation(id="op_find", name="find", parameters={"collection": "products", "filter": {}})
    res = await connector.execute(spec, op)
    assert res.success is True
    assert res.records_affected == 2


@pytest.mark.asyncio
async def test_datalake_connector():
    connector = DataLakeConnector()
    assert isinstance(connector, Connector)
    assert connector.type == "datalake"

    spec = ConnectionSpec(
        id="conn_lake_1",
        tenant_id="tenant_lake",
        type="datalake",
        name="AWS S3 Analytics Lake",
        config={"endpoint_host": "s3.amazonaws.com", "port": 443, "bucket": "analytics-lake"},
        credentials={"access_key": "AKIA_TEST_KEY"},
    )
    test_res = await connector.test(spec)
    assert test_res.success is True
    assert len(test_res.steps) == 4

    op = Operation(
        id="op_write",
        name="write_parquet",
        parameters={"path": "tenant_lake/year=2026/month=09/data.parquet", "count": 500}
    )
    res = await connector.execute(spec, op)
    assert res.success is True
    assert res.records_affected == 500
    assert res.data["format"] == "parquet"


@pytest.mark.asyncio
async def test_airflow_connector():
    connector = AirflowConnector()
    assert isinstance(connector, Connector)
    assert connector.type == "airflow"

    spec = ConnectionSpec(
        id="conn_af_1",
        tenant_id="tenant_etl",
        type="airflow",
        name="Astronomer Airflow Cluster",
        config={"host": "127.0.0.1", "port": 8080},
        credentials={"username": "airflow_admin"},
    )
    test_res = await connector.test(spec)
    assert test_res.success is True
    assert len(test_res.steps) == 4

    graph = await connector.discover(spec)
    assert len(graph.entities) >= 1

    op = Operation(
        id="op_trig",
        name="trigger_dag",
        parameters={"dag_id": "daily_sales_reconciliation", "conf": {"batch": "20260922"}}
    )
    res = await connector.execute(spec, op)
    assert res.success is True
    assert res.data["state"] == "queued"
