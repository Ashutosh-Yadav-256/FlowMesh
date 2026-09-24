"""
FlowMesh Pre-flight Workflow DAG Validation Engine

Performs structural, topological, and tenant-scoped validation on workflow definitions
before deployment:
1. Cycle detection (Kahn's algorithm / topological sort).
2. Reachability analysis (detects disconnected, unreachable, or orphaned nodes).
3. Dead-end & terminal node analysis.
4. Tenant connection boundary enforcement (verifies all connection_ids belong to the tenant).
5. Template expression syntax verification ({{ input.* }}, {{ steps.* }}).
6. Schema and parameter verification across extended node types.
"""

import re
from typing import Dict, Any, List, Set, Optional, Union
from pydantic import BaseModel, Field

from flowmesh_workflow.schema import WorkflowDefinition, WorkflowNode, WorkflowEdge


class ValidationResult(BaseModel):
    is_valid: bool = Field(..., description="True if no blocking validation errors exist")
    errors: List[str] = Field(default_factory=list, description="Critical blocking issues preventing deployment")
    warnings: List[str] = Field(default_factory=list, description="Non-blocking recommendations or cautionary items")
    stats: Dict[str, Any] = Field(default_factory=dict, description="Topological summary and execution metrics")


TEMPLATE_REGEX = re.compile(r"\{\{\s*([^{}]+)\s*\}\}")
VALID_ROOT_PATHS = {"input", "steps", "tenant_id", "trace_id", "workflow_id"}


class WorkflowValidator:
    """Pre-flight validator for FlowMesh workflow definitions."""

    @classmethod
    def validate(
        cls,
        definition: Union[WorkflowDefinition, Dict[str, Any]],
        available_connection_ids: Optional[Set[str]] = None,
    ) -> ValidationResult:
        """
        Validates a workflow definition comprehensively.
        Returns a ValidationResult with errors, warnings, and DAG statistics.
        """
        errors: List[str] = []
        warnings: List[str] = []

        if isinstance(definition, dict):
            try:
                wf_def = WorkflowDefinition(**definition)
            except Exception as e:
                return ValidationResult(
                    is_valid=False,
                    errors=[f"Schema validation failed: {str(e)}"],
                    warnings=[],
                    stats={"node_count": 0, "edge_count": 0},
                )
        else:
            wf_def = definition

        nodes = wf_def.nodes
        edges = wf_def.edges
        trigger = wf_def.trigger

        node_ids: Set[str] = set()
        for node in nodes:
            if node.id in node_ids:
                errors.append(f"Duplicate node ID detected: '{node.id}'")
            node_ids.add(node.id)

        for edge in edges:
            if edge.source not in node_ids:
                errors.append(f"Edge source '{edge.source}' references a non-existent node")
            if edge.target not in node_ids:
                errors.append(f"Edge target '{edge.target}' references a non-existent node")

        adjacency: Dict[str, List[str]] = {n.id: [] for n in nodes}
        in_degree: Dict[str, int] = {n.id: 0 for n in nodes}
        for edge in edges:
            if edge.source in adjacency and edge.target in in_degree:
                adjacency[edge.source].append(edge.target)
                in_degree[edge.target] += 1

        queue = [nid for nid, deg in in_degree.items() if deg == 0]
        visited_order: List[str] = []
        while queue:
            curr = queue.pop(0)
            visited_order.append(curr)
            for neighbor in adjacency[curr]:
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)

        if len(visited_order) < len(nodes):
            cycle_nodes = set(node_ids) - set(visited_order)
            errors.append(
                f"Cyclic dependency detected involving nodes: {', '.join(sorted(cycle_nodes))}. "
                "FlowMesh workflows must be directed acyclic graphs (DAGs)."
            )

        trigger_node_ids = {n.id for n in nodes if n.type.startswith("trigger.")}
        if not trigger_node_ids:
            start_candidates = [n.id for n in nodes if len([e for e in edges if e.target == n.id]) == 0]
            if not start_candidates:
                errors.append("Workflow has no entry node (in-degree 0).")
            else:
                trigger_node_ids = set(start_candidates[:1])

        reachable: Set[str] = set()
        reach_queue = list(trigger_node_ids)
        while reach_queue:
            curr = reach_queue.pop(0)
            if curr in reachable:
                continue
            reachable.add(curr)
            for nxt in adjacency.get(curr, []):
                reach_queue.append(nxt)

        unreachable = node_ids - reachable
        if unreachable:
            for unreach_id in sorted(unreachable):
                errors.append(f"Unreachable node detected: '{unreach_id}' cannot be reached from any trigger node.")

        if len(trigger_node_ids) > 1:
            warnings.append(
                f"Workflow defines {len(trigger_node_ids)} starting/trigger nodes ({', '.join(sorted(trigger_node_ids))}). "
                "Ensure multiple ingress paths are intended."
            )

        dead_ends = [n.id for n in nodes if not adjacency.get(n.id) and n.id in reachable]
        if len(dead_ends) > 1:
            warnings.append(
                f"Multiple terminal branch ends detected: {', '.join(sorted(dead_ends))}."
            )

        for node in nodes:
            if node.connection_id:
                if available_connection_ids is not None:
                    if node.connection_id not in available_connection_ids:
                        errors.append(
                            f"Node '{node.id}' ({node.name}) references connection '{node.connection_id}' "
                            "which does not exist or is not authorized within the tenant scope."
                        )

        for node in nodes:
            cls._check_templates_in_dict(node.config, node.id, errors, warnings)
        for edge in edges:
            if edge.condition:
                cls._check_template_expr(edge.condition, f"edge {edge.source}->{edge.target}", errors, warnings)

        has_approval_gate = False
        node_types = set()
        for node in nodes:
            node_types.add(node.type)
            if node.type == "action.approval":
                has_approval_gate = True
            elif node.type == "control.parallel":
                if not adjacency.get(node.id) and "branches" not in node.config:
                    warnings.append(f"Parallel node '{node.id}' has no outgoing edges and no branch definitions.")
            elif node.type == "control.delay":
                seconds = node.config.get("seconds", 0)
                if seconds < 0:
                    errors.append(f"Delay node '{node.id}' cannot have negative sleep duration: {seconds}s")
            elif node.type == "action.http":
                if not node.config.get("path") and not node.config.get("endpoint"):
                    warnings.append(f"HTTP node '{node.id}' has no endpoint or path specified in config.")

        longest_path_len = cls._compute_max_depth(nodes, edges)

        stats = {
            "node_count": len(nodes),
            "edge_count": len(edges),
            "trigger_type": trigger.type,
            "node_types": sorted(list(node_types)),
            "has_approval_gate": has_approval_gate,
            "estimated_depth": longest_path_len,
            "reachable_node_count": len(reachable),
        }

        return ValidationResult(
            is_valid=(len(errors) == 0),
            errors=errors,
            warnings=warnings,
            stats=stats,
        )

    @classmethod
    def _check_templates_in_dict(cls, data: Any, node_id: str, errors: List[str], warnings: List[str]) -> None:
        if isinstance(data, str):
            cls._check_template_expr(data, f"node '{node_id}'", errors, warnings)
        elif isinstance(data, dict):
            for k, v in data.items():
                cls._check_templates_in_dict(v, node_id, errors, warnings)
        elif isinstance(data, list):
            for item in data:
                cls._check_templates_in_dict(item, node_id, errors, warnings)

    @classmethod
    def _check_template_expr(cls, text: str, location: str, errors: List[str], warnings: List[str]) -> None:
        if "{{" in text and "}}" not in text:
            errors.append(f"Unclosed template expression '{{{{' in {location}: {text[:50]}")
            return
        if "}}" in text and "{{" not in text:
            errors.append(f"Unmatched template closing '}}}}' in {location}: {text[:50]}")
            return

        for match in TEMPLATE_REGEX.finditer(text):
            expr = match.group(1).strip()
            if not expr:
                warnings.append(f"Empty template expression '{{{{}}}}' found in {location}")
                continue
            root = expr.split(".")[0].split("[")[0].strip()
            if root not in VALID_ROOT_PATHS and not root.startswith("$"):
                warnings.append(
                    f"Template expression '{{{{ {expr} }}}}' in {location} uses unexpected root '{root}'. "
                    f"Expected one of: {', '.join(sorted(VALID_ROOT_PATHS))}."
                )

    @classmethod
    def _compute_max_depth(cls, nodes: List[WorkflowNode], edges: List[WorkflowEdge]) -> int:
        if not nodes:
            return 0
        adjacency: Dict[str, List[str]] = {n.id: [] for n in nodes}
        in_degree: Dict[str, int] = {n.id: 0 for n in nodes}
        for e in edges:
            if e.source in adjacency:
                adjacency[e.source].append(e.target)
                in_degree[e.target] = in_degree.get(e.target, 0) + 1

        dist: Dict[str, int] = {n.id: 1 for n in nodes}
        queue = [nid for nid, deg in in_degree.items() if deg == 0]
        while queue:
            curr = queue.pop(0)
            for nxt in adjacency.get(curr, []):
                if dist[curr] + 1 > dist[nxt]:
                    dist[nxt] = dist[curr] + 1
                in_degree[nxt] -= 1
                if in_degree[nxt] == 0:
                    queue.append(nxt)

        return max(dist.values()) if dist else 1
