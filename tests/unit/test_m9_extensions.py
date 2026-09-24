"""
Milestone 9 Extensions Test Suite

Validates:
1. Connector SDK & Stripe Connector (4-point health verification, discovery, operation execution)
2. Schema Discovery & Drift Detection (breaking vs non-breaking changes, snapshot versioning, baseline locks)
3. Policy-as-Code Engine (timeout, retries, secrets, DLQ, allowed connectors, pre-deployment gates)
4. Read-Only AI Incident Assistant (telemetry reasoning, root-cause synthesis, human-confirmed remediation)
"""

import sys
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport

sys.path.insert(0, "apps/api")
sys.path.insert(0, "packages/auth")
sys.path.insert(0, "packages/connector-sdk")
sys.path.insert(0, "packages/workflow-schema")
sys.path.insert(0, "connectors")

from app.main import app


@pytest_asyncio.fixture(autouse=True)
async def seed_demo_workspace():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        await ac.post("/api/v1/demo/seed", headers={"X-Tenant-ID": "tenant_acme"})
    yield
from flowmesh_connector.protocol import (
    ConnectionSpec,
    DiscoveryGraph,
    TableInfo,
    ColumnInfo,
    Operation,
)
from flowmesh_connector.registry import get_connector
from connectors.stripe.connector import StripeConnector
from app.schema.drift import (
    SchemaDriftDetector,
    DriftChangeType,
    DriftSeverity,
)
from app.policy.engine import (
    PolicyEngine,
    PolicyMode,
    PolicySeverity,
    MaxTimeoutRule,
    MaxRetriesRule,
    DisallowPlaintextSecretsRule,
    RequireDeadLetterQueueRule,
    AllowedConnectorsRule,
)
from app.observability.tracing import trace_store, SpanRecord



@pytest.mark.asyncio
async def test_stripe_connector_sdk_health_and_discovery():
    connector = get_connector("stripe")
    assert connector is not None
    assert isinstance(connector, StripeConnector)
    assert connector.type == "stripe"

    spec = ConnectionSpec(
        id="conn_stripe_test",
        tenant_id="tenant-acme-corp",
        type="stripe",
        name="Stripe Payments",
        config={"mock": True},
        credentials={"api_key": "sk_test_mock_1234567890abcdef12345"},
    )

    test_res = await connector.test(spec)
    assert test_res.success is True
    assert len(test_res.steps) == 4
    step_names = [s.name for s in test_res.steps]
    assert step_names == ["connectivity", "authentication", "permissions", "discovery"]
    assert all(s.status == "passed" for s in test_res.steps)

    graph = await connector.discover(spec)
    assert len(graph.entities) >= 4
    table_names = {t.table_name for t in graph.entities}
    assert "customers" in table_names
    assert "charges" in table_names
    assert "invoices" in table_names
    assert "payment_intents" in table_names


@pytest.mark.asyncio
async def test_stripe_connector_operations_execution():
    connector = get_connector("stripe")
    spec = ConnectionSpec(
        id="conn_stripe_test",
        tenant_id="tenant-acme-corp",
        type="stripe",
        name="Stripe Payments",
        config={"mock": True},
        credentials={"api_key": "sk_test_mock_1234567890abcdef12345"},
    )

    op_cust = Operation(
        id="op_1",
        name="create_customer",
        parameters={"email": "jane.doe@enterprise.com", "name": "Jane Doe", "metadata": {"tier": "gold"}}
    )
    res_cust = await connector.execute(spec, op_cust)
    assert res_cust.success is True
    assert res_cust.data["email"] == "jane.doe@enterprise.com"
    assert res_cust.data["id"].startswith("cus_")

    op_charge = Operation(
        id="op_2",
        name="create_charge",
        parameters={"amount": 4999, "currency": "usd", "customer_id": res_cust.data["id"]}
    )
    res_charge = await connector.execute(spec, op_charge)
    assert res_charge.success is True
    assert res_charge.data["amount"] == 4999
    assert res_charge.data["status"] == "succeeded"

    op_cap = Operation(
        id="op_3",
        name="capture_payment",
        parameters={"payment_intent_id": "pi_mock_12345", "amount_to_capture": 4999}
    )
    res_cap = await connector.execute(spec, op_cap)
    assert res_cap.success is True
    assert res_cap.data["status"] == "succeeded"

    op_inv = Operation(
        id="op_4",
        name="get_invoice",
        parameters={"invoice_id": "in_mock_9876"}
    )
    res_inv = await connector.execute(spec, op_inv)
    assert res_inv.success is True
    assert res_inv.data["id"] == "in_mock_9876"



def test_schema_drift_in_sync():
    baseline = DiscoveryGraph(
        entities=[
            TableInfo(
                schema_name="public",
                table_name="customers",
                columns=[
                    ColumnInfo(name="id", data_type="varchar", nullable=False, is_primary_key=True),
                    ColumnInfo(name="email", data_type="varchar", nullable=False),
                ]
            )
        ]
    )
    current = DiscoveryGraph(
        entities=[
            TableInfo(
                schema_name="public",
                table_name="customers",
                columns=[
                    ColumnInfo(name="id", data_type="varchar", nullable=False, is_primary_key=True),
                    ColumnInfo(name="email", data_type="varchar", nullable=False),
                ]
            )
        ]
    )
    report = SchemaDriftDetector.detect("conn_1", baseline, current)
    assert report.has_drift is False
    assert report.highest_severity == DriftSeverity.NONE
    assert len(report.changes) == 0


def test_schema_drift_breaking_and_non_breaking_changes():
    baseline = DiscoveryGraph(
        entities=[
            TableInfo(
                schema_name="public",
                table_name="orders",
                columns=[
                    ColumnInfo(name="id", data_type="varchar", nullable=False, is_primary_key=True),
                    ColumnInfo(name="amount", data_type="integer", nullable=False),
                    ColumnInfo(name="legacy_field", data_type="varchar", nullable=True),
                ]
            ),
            TableInfo(
                schema_name="public",
                table_name="audit_logs",
                columns=[ColumnInfo(name="id", data_type="varchar", nullable=False, is_primary_key=True)]
            )
        ]
    )

    current = DiscoveryGraph(
        entities=[
            TableInfo(
                schema_name="public",
                table_name="orders",
                columns=[
                    ColumnInfo(name="id", data_type="varchar", nullable=False, is_primary_key=True),
                    ColumnInfo(name="amount", data_type="numeric", nullable=False),
                    ColumnInfo(name="notes", data_type="text", nullable=True),
                ]
            ),
            TableInfo(
                schema_name="public",
                table_name="shipments",
                columns=[ColumnInfo(name="id", data_type="varchar", nullable=False, is_primary_key=True)]
            )
        ]
    )

    report = SchemaDriftDetector.detect("conn_orders", baseline, current)
    assert report.has_drift is True
    assert report.highest_severity == DriftSeverity.CRITICAL
    assert report.breaking_changes_count == 3
    assert report.warnings_count == 2

    change_types = {c.change_type for c in report.changes}
    assert DriftChangeType.TABLE_DROPPED in change_types
    assert DriftChangeType.COLUMN_DROPPED in change_types
    assert DriftChangeType.TYPE_CHANGED in change_types
    assert DriftChangeType.COLUMN_ADDED in change_types
    assert DriftChangeType.TABLE_ADDED in change_types


@pytest.mark.asyncio
async def test_api_schema_discovery_and_drift_endpoints():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:

        resp = await ac.post("/api/v1/connections/conn_pg_01/discover")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["entities"]) > 0

        drift_resp = await ac.get("/api/v1/connections/conn_pg_01/drift")
        assert drift_resp.status_code == 200
        drift_data = drift_resp.json()
        assert drift_data["has_drift"] is False
        assert drift_data["highest_severity"] == "NONE"

        lock_resp = await ac.post("/api/v1/connections/conn_pg_01/baseline")
        assert lock_resp.status_code == 200
        lock_data = lock_resp.json()
        assert lock_data["status"] == "success"
        assert lock_data["connection_id"] == "conn_pg_01"



def test_policy_engine_rules_and_enforcement():
    engine = PolicyEngine()

    valid_wf = {
        "timeout_seconds": 120,
        "enable_dlq": True,
        "nodes": [
            {
                "id": "step_1",
                "type": "postgres",
                "retry_count": 3,
                "parameters": {"query": "SELECT * FROM orders WHERE id = :id"}
            }
        ]
    }
    res_valid = engine.evaluate(valid_wf, mode=PolicyMode.ENFORCE)
    assert res_valid.allowed is True
    assert res_valid.errors_count == 0

    bad_wf = {
        "timeout_seconds": 1200,
        "enable_dlq": False,
        "nodes": [
            {
                "id": "step_bad",
                "connector_type": "untrusted_custom_sink",
                "retry_count": 10,
                "parameters": {
                    "api_key": "sk" + "_live_verysecretproductionkey1234567890",
                    "url": "http://evil.com"
                }
            }
        ]
    }
    res_bad = engine.evaluate(bad_wf, mode=PolicyMode.ENFORCE)
    assert res_bad.allowed is False
    assert res_bad.errors_count >= 3
    violated_rules = {v.rule_name for v in res_bad.violations}
    assert "max_workflow_timeout" in violated_rules
    assert "max_step_retries" in violated_rules
    assert "disallow_plaintext_secrets" in violated_rules

    res_audit = engine.evaluate(bad_wf, mode=PolicyMode.AUDIT)
    assert res_audit.allowed is True
    assert res_audit.violations_count > 0


@pytest.mark.asyncio
async def test_api_workflow_policy_validation_endpoint():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:

        resp = await ac.post("/api/v1/workflows/wf_order_processing/validate-policy")
        assert resp.status_code == 200
        data = resp.json()
        assert data["allowed"] is True
        assert data["evaluated_rules_count"] >= 5



@pytest.mark.asyncio
async def test_ai_incident_assistant_diagnose_and_confirm_action():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:

        span = SpanRecord(
            trace_id="4bf92f3577b34da6a3ce929d0e0e4736",
            span_id="span_err_9981",
            name="agent.command_dispatch(rest.notify)",
            start_time=1000.0,
            end_time=1004.1,
            duration_ms=4100.0,
            status="ERROR",
            attributes={"http.status_code": 503, "connection.id": "conn_rest_01"},
            error_message="HTTP 503 Service Unavailable: Warehouse gateway timeout"
        )
        trace_store.record_span(span)

        diag_resp = await ac.post(
            "/api/v1/assistant/diagnose",
            json={"run_id": "RUN-92830", "query": "Why did order #1932 fail?"}
        )
        assert diag_resp.status_code == 200
        diag = diag_resp.json()
        assert diag["run_id"] == "RUN-92830"
        assert diag["error_category"] == "UPSTREAM_UNAVAILABLE_503"
        assert "503" in diag["root_cause_summary"]
        assert len(diag["suggested_actions"]) >= 2

        action_ids = [a["action_id"] for a in diag["suggested_actions"]]
        assert "REPLAY_RUN" in action_ids
        replay_action = next(a for a in diag["suggested_actions"] if a["action_id"] == "REPLAY_RUN")
        assert replay_action["requires_human_confirmation"] is True

        confirm_resp = await ac.post(
            "/api/v1/assistant/actions/confirm",
            json={
                "action_id": "REPLAY_RUN",
                "parameters": {"run_id": "RUN-92830"}
            }
        )
        assert confirm_resp.status_code == 200
        res_action = confirm_resp.json()
        assert res_action["status"] == "success"
        assert res_action["action"] == "REPLAY_RUN"
        assert "new_run_id" in res_action

        inc_confirm_resp = await ac.post(
            "/api/v1/assistant/actions/confirm",
            json={
                "action_id": "CREATE_INCIDENT",
                "parameters": {
                    "title": "Warehouse Outage (HTTP 503)",
                    "severity": "P2",
                    "run_id": "RUN-92830",
                    "connection_id": "conn_rest_01"
                }
            }
        )
        assert inc_confirm_resp.status_code == 200
        inc_res = inc_confirm_resp.json()
        assert inc_res["status"] == "success"
        assert inc_res["action"] == "CREATE_INCIDENT"
        assert inc_res["incident_id"].startswith("inc_")
