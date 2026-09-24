"""
FlowMesh PyYAML Workflow Compiler & Parser
Provides strict PyYAML schema loading, DAG validation, and round-trip YAML serialization
for declarative enterprise workflow definitions.
"""

from typing import Dict, Any, Tuple, Optional
import yaml
from flowmesh_workflow.schema import WorkflowDefinition, TriggerSpec, WorkflowNode, WorkflowEdge, RetryPolicy


class YamlWorkflowParser:
    """Enterprise YAML loader and serializer for FlowMesh DAG workflows."""

    @classmethod
    def load_from_yaml(cls, yaml_content: str) -> WorkflowDefinition:
        """Parses a YAML string into a fully validated WorkflowDefinition model."""
        try:
            raw_data = yaml.safe_load(yaml_content)
        except yaml.YAMLError as exc:
            raise ValueError(f"YAML Syntax Error: {str(exc)}") from exc

        if not isinstance(raw_data, dict):
            raise ValueError("Invalid YAML workflow: root document must be a dictionary")

        return WorkflowDefinition(**raw_data)

    @classmethod
    def dump_to_yaml(cls, workflow: WorkflowDefinition) -> str:
        """Serializes a WorkflowDefinition model to clean, human-readable YAML."""
        data = workflow.model_dump(exclude_none=True)
        return yaml.safe_dump(
            data,
            sort_keys=False,
            default_flow_style=False,
            indent=2,
            allow_unicode=True,
        )

    @classmethod
    def validate_yaml_string(cls, yaml_content: str) -> Tuple[bool, Optional[str], Optional[WorkflowDefinition]]:
        """
        Validates a YAML string against the FlowMesh schema.
        Returns: (is_valid, error_message, parsed_workflow)
        """
        try:
            wf = cls.load_from_yaml(yaml_content)
            return True, None, wf
        except Exception as exc:
            return False, str(exc), None


def load_workflow_yaml(yaml_str: str) -> WorkflowDefinition:
    """Convenience helper to parse workflow YAML."""
    return YamlWorkflowParser.load_from_yaml(yaml_str)


def dump_workflow_yaml(wf: WorkflowDefinition) -> str:
    """Convenience helper to dump workflow to YAML."""
    return YamlWorkflowParser.dump_to_yaml(wf)
