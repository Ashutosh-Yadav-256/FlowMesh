"""
FlowMesh Workflow Schema Package
Authoritative contract for workflow DAG definitions, nodes, edges, and triggers.
"""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field, model_validator


class TriggerSpec(BaseModel):
    type: str = Field(..., description="webhook, event, nats, schedule, manual")
    config: Dict[str, Any] = Field(default_factory=dict)


class RetryPolicy(BaseModel):
    max_attempts: int = Field(default=3, ge=1, le=10)
    backoff: str = Field(default="exponential", description="exponential, fixed, linear")
    initial_interval_seconds: float = Field(default=0.5, ge=0.0)
    max_interval_seconds: float = Field(default=30.0, ge=0.1)
    jitter: bool = Field(default=True)


class WorkflowNode(BaseModel):
    id: str = Field(..., min_length=1)
    type: str = Field(..., description="trigger.webhook, trigger.event, action.http, action.db_query, action.db_write, control.condition, transform, audit.log")
    name: str = Field(..., min_length=1)
    connection_id: Optional[str] = None
    config: Dict[str, Any] = Field(default_factory=dict)
    retry: Optional[RetryPolicy | Dict[str, Any]] = None


class WorkflowEdge(BaseModel):
    source: str
    target: str
    condition: Optional[str] = None


class WorkflowDefinition(BaseModel):
    id: Optional[str] = None
    schema_version: int = 1
    name: str = Field(..., min_length=2, max_length=100)
    description: str = Field(default="")
    trigger: TriggerSpec
    nodes: List[WorkflowNode] = Field(..., min_length=1)
    edges: List[WorkflowEdge] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_dag(self) -> "WorkflowDefinition":
        node_ids = {n.id for n in self.nodes}
        if len(node_ids) != len(self.nodes):
            raise ValueError("Duplicate node IDs found in workflow definition")

        for edge in self.edges:
            if edge.source not in node_ids:
                raise ValueError(f"Edge references non-existent source node: {edge.source}")
            if edge.target not in node_ids:
                raise ValueError(f"Edge references non-existent target node: {edge.target}")

        adjacency: Dict[str, List[str]] = {n.id: [] for n in self.nodes}
        in_degree: Dict[str, int] = {n.id: 0 for n in self.nodes}
        for edge in self.edges:
            adjacency[edge.source].append(edge.target)
            in_degree[edge.target] += 1

        queue = [nid for nid, deg in in_degree.items() if deg == 0]
        visited_count = 0
        while queue:
            curr = queue.pop(0)
            visited_count += 1
            for neighbor in adjacency[curr]:
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)

        if visited_count < len(self.nodes):
            raise ValueError("Cycle detected in workflow DAG. FlowMesh workflows must be directed acyclic graphs.")

        return self
