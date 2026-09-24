"""
Unit Tests for FlowMesh Workflow Pre-flight Validation Engine

Tests:
1. Valid DAG passes with clean stats.
2. Direct and indirect cyclic dependency detection.
3. Unreachable / disconnected node detection.
4. Tenant connection boundary enforcement.
5. Template expression validation ({{ input.* }}, {{ steps.* }}).
6. Extended node property verification (negative delay, approval gate detection).
"""

import pytest
from flowmesh_workflow.schema import WorkflowDefinition, WorkflowNode, WorkflowEdge, TriggerSpec
from flowmesh_engine.validation import WorkflowValidator, ValidationResult


def test_valid_dag_validation_passes():
    wf_dict = {
        "schema_version": 1,
        "name": "Valid Pipeline",
        "description": "Standard linear pipeline",
        "trigger": {"type": "webhook", "config": {"path": "/orders"}},
        "nodes": [
            {"id": "node_1", "type": "trigger.webhook", "name": "Ingress", "config": {}},
            {"id": "node_2", "type": "transform", "name": "Transform Order", "config": {"mapping": {"id": "{{ input.order_id }}"}}},
            {"id": "node_3", "type": "action.notification", "name": "Notify Slack", "config": {"message": "Order {{ steps.node_2.output.id }} received"}},
            {"id": "node_4", "type": "audit.log", "name": "Audit", "config": {}},
        ],
        "edges": [
            {"source": "node_1", "target": "node_2"},
            {"source": "node_2", "target": "node_3"},
            {"source": "node_3", "target": "node_4"},
        ],
    }

    result = WorkflowValidator.validate(wf_dict)
    assert result.is_valid is True
    assert len(result.errors) == 0
    assert result.stats["node_count"] == 4
    assert result.stats["edge_count"] == 3
    assert result.stats["estimated_depth"] == 4
    assert result.stats["has_approval_gate"] is False


def test_cycle_detection_flags_error():

    wf_dict = {
        "schema_version": 1,
        "name": "Cyclic Pipeline",
        "trigger": {"type": "webhook", "config": {}},
        "nodes": [
            {"id": "a", "type": "trigger.webhook", "name": "A", "config": {}},
            {"id": "b", "type": "transform", "name": "B", "config": {}},
            {"id": "c", "type": "transform", "name": "C", "config": {}},
        ],
        "edges": [
            {"source": "a", "target": "b"},
            {"source": "b", "target": "c"},
            {"source": "c", "target": "a"},
        ],
    }

    result = WorkflowValidator.validate(wf_dict)
    assert result.is_valid is False
    assert any("Cyclic" in err or "cycle" in err.lower() for err in result.errors)


def test_unreachable_node_detected():

    wf_dict = {
        "schema_version": 1,
        "name": "Disconnected Pipeline",
        "trigger": {"type": "webhook", "config": {}},
        "nodes": [
            {"id": "a", "type": "trigger.webhook", "name": "Trigger", "config": {}},
            {"id": "b", "type": "audit.log", "name": "Log", "config": {}},
            {"id": "orphaned_node", "type": "action.http", "name": "Orphan", "config": {"endpoint": "/test"}},
        ],
        "edges": [
            {"source": "a", "target": "b"},
        ],
    }

    result = WorkflowValidator.validate(wf_dict)
    assert result.is_valid is False
    assert any("orphaned_node" in err and "Unreachable" in err for err in result.errors)


def test_tenant_connection_scope_enforcement():
    wf_dict = {
        "schema_version": 1,
        "name": "Secured Pipeline",
        "trigger": {"type": "webhook", "config": {}},
        "nodes": [
            {"id": "t1", "type": "trigger.webhook", "name": "Trigger", "config": {}},
            {"id": "db1", "type": "action.db_query", "name": "DB Query", "connection_id": "conn_alien_tenant_99", "config": {}},
        ],
        "edges": [
            {"source": "t1", "target": "db1"},
        ],
    }

    authorized_conns = {"conn_pg_01", "conn_rest_01"}

    result = WorkflowValidator.validate(wf_dict, available_connection_ids=authorized_conns)
    assert result.is_valid is False
    assert any("conn_alien_tenant_99" in err and "tenant scope" in err for err in result.errors)


def test_template_syntax_unclosed_braces():
    wf_dict = {
        "schema_version": 1,
        "name": "Broken Template",
        "trigger": {"type": "webhook", "config": {}},
        "nodes": [
            {"id": "t1", "type": "trigger.webhook", "name": "Trigger", "config": {}},
            {"id": "t2", "type": "transform", "name": "Bad Mapping", "config": {"mapping": {"broken": "{{ input.order_id"}}},
        ],
        "edges": [{"source": "t1", "target": "t2"}],
    }

    result = WorkflowValidator.validate(wf_dict)
    assert result.is_valid is False
    assert any("Unclosed template" in err for err in result.errors)


def test_extended_node_validation():
    wf_dict = {
        "schema_version": 1,
        "name": "Approval and Delay Pipeline",
        "trigger": {"type": "webhook", "config": {}},
        "nodes": [
            {"id": "t1", "type": "trigger.webhook", "name": "Trigger", "config": {}},
            {"id": "appr1", "type": "action.approval", "name": "Manager Approval Gate", "config": {"approver_role": "operator"}},
            {"id": "delay1", "type": "control.delay", "name": "Cooldown Delay", "config": {"seconds": 5}},
            {"id": "log1", "type": "audit.log", "name": "Audit", "config": {}},
        ],
        "edges": [
            {"source": "t1", "target": "appr1"},
            {"source": "appr1", "target": "delay1"},
            {"source": "delay1", "target": "log1"},
        ],
    }

    result = WorkflowValidator.validate(wf_dict)
    assert result.is_valid is True
    assert result.stats["has_approval_gate"] is True
    assert "action.approval" in result.stats["node_types"]
    assert "control.delay" in result.stats["node_types"]

    wf_dict["nodes"][2]["config"]["seconds"] = -10
    res2 = WorkflowValidator.validate(wf_dict)
    assert res2.is_valid is False
    assert any("negative sleep duration" in err for err in res2.errors)
