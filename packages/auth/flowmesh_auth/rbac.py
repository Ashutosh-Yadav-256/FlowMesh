"""
FlowMesh Role-Based Access Control (RBAC) Engine

Structured as a central, declarative permission matrix:
(role, resource, action) -> bool

Roles:
- owner: Full organization administration, billing, tenant deletion, role modification.
- operator: Connection management, incident resolution, DLQ replay, workflow triggering, certificate rotation.
- developer: Workflow modeling, connection authoring, test execution, run inspection.
- viewer: Read-only observation across dashboards, workflows, traces, and audit logs.
"""

from typing import Dict, Set, Tuple
from enum import Enum


class Role(str, Enum):
    OWNER = "owner"
    OPERATOR = "operator"
    DEVELOPER = "developer"
    VIEWER = "viewer"


class Action(str, Enum):
    CREATE = "create"
    READ = "read"
    UPDATE = "update"
    DELETE = "delete"
    EXECUTE = "execute"
    REPLAY = "replay"
    ROTATE = "rotate"


class Resource(str, Enum):
    TENANT = "tenant"
    USER = "user"
    API_KEY = "api_key"
    CONNECTION = "connection"
    WORKFLOW = "workflow"
    RUN = "run"
    INCIDENT = "incident"
    DLQ = "dlq"
    AGENT = "agent"
    AUDIT = "audit"


_POLICY_MATRIX: Set[Tuple[str, str, str]] = {

    *(
        (Role.OWNER.value, res.value, act.value)
        for res in Resource
        for act in Action
    ),

    (Role.OPERATOR.value, Resource.TENANT.value, Action.READ.value),
    (Role.OPERATOR.value, Resource.USER.value, Action.READ.value),
    (Role.OPERATOR.value, Resource.API_KEY.value, Action.READ.value),
    (Role.OPERATOR.value, Resource.CONNECTION.value, Action.READ.value),
    (Role.OPERATOR.value, Resource.CONNECTION.value, Action.UPDATE.value),
    (Role.OPERATOR.value, Resource.CONNECTION.value, Action.EXECUTE.value),
    (Role.OPERATOR.value, Resource.CONNECTION.value, Action.ROTATE.value),
    (Role.OPERATOR.value, Resource.WORKFLOW.value, Action.READ.value),
    (Role.OPERATOR.value, Resource.WORKFLOW.value, Action.EXECUTE.value),
    (Role.OPERATOR.value, Resource.WORKFLOW.value, Action.UPDATE.value),
    (Role.OPERATOR.value, Resource.RUN.value, Action.READ.value),
    (Role.OPERATOR.value, Resource.RUN.value, Action.EXECUTE.value),
    (Role.OPERATOR.value, Resource.RUN.value, Action.UPDATE.value),
    (Role.OPERATOR.value, Resource.RUN.value, Action.REPLAY.value),
    (Role.OPERATOR.value, Resource.INCIDENT.value, Action.READ.value),
    (Role.OPERATOR.value, Resource.INCIDENT.value, Action.UPDATE.value),
    (Role.OPERATOR.value, Resource.DLQ.value, Action.READ.value),
    (Role.OPERATOR.value, Resource.DLQ.value, Action.REPLAY.value),
    (Role.OPERATOR.value, Resource.AGENT.value, Action.READ.value),
    (Role.OPERATOR.value, Resource.AGENT.value, Action.CREATE.value),
    (Role.OPERATOR.value, Resource.AGENT.value, Action.EXECUTE.value),
    (Role.OPERATOR.value, Resource.AGENT.value, Action.ROTATE.value),
    (Role.OPERATOR.value, Resource.AUDIT.value, Action.READ.value),

    (Role.DEVELOPER.value, Resource.TENANT.value, Action.READ.value),
    (Role.DEVELOPER.value, Resource.USER.value, Action.READ.value),
    (Role.DEVELOPER.value, Resource.API_KEY.value, Action.CREATE.value),
    (Role.DEVELOPER.value, Resource.API_KEY.value, Action.READ.value),
    (Role.DEVELOPER.value, Resource.CONNECTION.value, Action.CREATE.value),
    (Role.DEVELOPER.value, Resource.CONNECTION.value, Action.READ.value),
    (Role.DEVELOPER.value, Resource.CONNECTION.value, Action.UPDATE.value),
    (Role.DEVELOPER.value, Resource.CONNECTION.value, Action.EXECUTE.value),
    (Role.DEVELOPER.value, Resource.WORKFLOW.value, Action.CREATE.value),
    (Role.DEVELOPER.value, Resource.WORKFLOW.value, Action.READ.value),
    (Role.DEVELOPER.value, Resource.WORKFLOW.value, Action.UPDATE.value),
    (Role.DEVELOPER.value, Resource.WORKFLOW.value, Action.EXECUTE.value),
    (Role.DEVELOPER.value, Resource.RUN.value, Action.READ.value),
    (Role.DEVELOPER.value, Resource.RUN.value, Action.EXECUTE.value),
    (Role.DEVELOPER.value, Resource.INCIDENT.value, Action.READ.value),
    (Role.DEVELOPER.value, Resource.DLQ.value, Action.READ.value),
    (Role.DEVELOPER.value, Resource.AGENT.value, Action.READ.value),
    (Role.DEVELOPER.value, Resource.AGENT.value, Action.CREATE.value),
    (Role.DEVELOPER.value, Resource.AGENT.value, Action.EXECUTE.value),
    (Role.DEVELOPER.value, Resource.AUDIT.value, Action.READ.value),

    (Role.VIEWER.value, Resource.TENANT.value, Action.READ.value),
    (Role.VIEWER.value, Resource.USER.value, Action.READ.value),
    (Role.VIEWER.value, Resource.CONNECTION.value, Action.READ.value),
    (Role.VIEWER.value, Resource.WORKFLOW.value, Action.READ.value),
    (Role.VIEWER.value, Resource.RUN.value, Action.READ.value),
    (Role.VIEWER.value, Resource.INCIDENT.value, Action.READ.value),
    (Role.VIEWER.value, Resource.DLQ.value, Action.READ.value),
    (Role.VIEWER.value, Resource.AGENT.value, Action.READ.value),
    (Role.VIEWER.value, Resource.AUDIT.value, Action.READ.value),
}


def is_allowed(role: str, resource: str, action: str) -> bool:
    """Evaluates the central policy matrix to determine if (role, resource, action) is allowed."""
    return (role.lower(), resource.lower(), action.lower()) in _POLICY_MATRIX


def enforce_rbac(role: str, resource: str, action: str) -> None:
    """Raises PermissionError if the action is not explicitly permitted in the policy matrix."""
    if not is_allowed(role, resource, action):
        raise PermissionError(
            f"RBAC Denied: Role '{role}' does not have permission to '{action}' on resource '{resource}'"
        )
