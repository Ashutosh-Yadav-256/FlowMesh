"""
Unit Tests for FlowMesh PyYAML Workflow Parser & Compiler
Validates strict YAML loading, DAG validation, and round-trip YAML serialization.
"""

import pytest
import yaml
from flowmesh_workflow.yaml_parser import (
    YamlWorkflowParser,
    load_workflow_yaml,
    dump_workflow_yaml,
)
from flowmesh_workflow.schema import WorkflowDefinition


SAMPLE_YAML = """
name: "Acme Order Processing Pipeline"
description: "Ingests webhook payload, validates inventory, and notifies ServiceNow"
trigger:
  type: "webhook"
  config:
    path: "/api/v1/orders"
nodes:
  - id: "step_ingest"
    type: "trigger.webhook"
    name: "Ingest Order"
  - id: "step_validate"
    type: "action.db_query"
    name: "Validate Inventory"
    connection_id: "conn_postgres_01"
  - id: "step_snow_notify"
    type: "action.http"
    name: "Create ServiceNow Incident on Out of Stock"
    connection_id: "conn_snow_01"
edges:
  - source: "step_ingest"
    target: "step_validate"
  - source: "step_validate"
    target: "step_snow_notify"
    condition: "payload.stock_level < 5"
"""


def test_yaml_workflow_loading():
    wf = load_workflow_yaml(SAMPLE_YAML)
    assert isinstance(wf, WorkflowDefinition)
    assert wf.name == "Acme Order Processing Pipeline"
    assert len(wf.nodes) == 3
    assert len(wf.edges) == 2
    assert wf.nodes[0].id == "step_ingest"
    assert wf.nodes[2].connection_id == "conn_snow_01"


def test_yaml_workflow_roundtrip():
    wf = load_workflow_yaml(SAMPLE_YAML)
    yaml_output = dump_workflow_yaml(wf)

    # Verify output is valid YAML and can be parsed again
    wf_reparsed = load_workflow_yaml(yaml_output)
    assert wf_reparsed.name == wf.name
    assert len(wf_reparsed.nodes) == len(wf.nodes)


def test_yaml_syntax_error_handling():
    invalid_yaml = "name: Broken: [unclosed"
    is_valid, err_msg, parsed = YamlWorkflowParser.validate_yaml_string(invalid_yaml)
    assert is_valid is False
    assert err_msg is not None
    assert parsed is None


def test_yaml_dag_validation():
    # Invalid DAG with disconnected edge
    invalid_dag_yaml = """
name: "Broken Edge Pipeline"
trigger:
  type: "webhook"
nodes:
  - id: "node_a"
    type: "action.http"
    name: "Node A"
edges:
  - source: "node_a"
    target: "node_non_existent"
"""
    is_valid, err_msg, parsed = YamlWorkflowParser.validate_yaml_string(invalid_dag_yaml)
    assert is_valid is False
    assert "non-existent" in str(err_msg)
