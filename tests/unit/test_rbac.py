"""
Milestone 1 — RBAC Matrix & Policy Enforcement Verification

Tests all 4 roles: owner, operator, developer, viewer.
Verifies allowed actions pass and unauthorized actions raise PermissionError.
"""

import sys
import pytest

sys.path.insert(0, "packages/auth")
from flowmesh_auth.rbac import (
    Role,
    Resource,
    Action,
    is_allowed,
    enforce_rbac,
)


def test_owner_role_has_full_access():
    """Owner role must be permitted for every resource and action."""
    for res in Resource:
        for act in Action:
            assert is_allowed(Role.OWNER.value, res.value, act.value) is True

            enforce_rbac(Role.OWNER.value, res.value, act.value)


def test_operator_role_boundaries():
    """Operator can run workflows, replay DLQ, and rotate certs, but cannot delete tenants or create users."""

    assert is_allowed(Role.OPERATOR.value, Resource.WORKFLOW.value, Action.EXECUTE.value) is True
    assert is_allowed(Role.OPERATOR.value, Resource.DLQ.value, Action.REPLAY.value) is True
    assert is_allowed(Role.OPERATOR.value, Resource.AGENT.value, Action.ROTATE.value) is True
    assert is_allowed(Role.OPERATOR.value, Resource.INCIDENT.value, Action.UPDATE.value) is True

    assert is_allowed(Role.OPERATOR.value, Resource.TENANT.value, Action.DELETE.value) is False
    assert is_allowed(Role.OPERATOR.value, Resource.USER.value, Action.CREATE.value) is False
    assert is_allowed(Role.OPERATOR.value, Resource.USER.value, Action.DELETE.value) is False

    with pytest.raises(PermissionError):
        enforce_rbac(Role.OPERATOR.value, Resource.TENANT.value, Action.DELETE.value)


def test_developer_role_boundaries():
    """Developer can create/update workflows and connections, but cannot rotate agent certs or delete tenants."""

    assert is_allowed(Role.DEVELOPER.value, Resource.WORKFLOW.value, Action.CREATE.value) is True
    assert is_allowed(Role.DEVELOPER.value, Resource.WORKFLOW.value, Action.UPDATE.value) is True
    assert is_allowed(Role.DEVELOPER.value, Resource.CONNECTION.value, Action.CREATE.value) is True
    assert is_allowed(Role.DEVELOPER.value, Resource.API_KEY.value, Action.CREATE.value) is True

    assert is_allowed(Role.DEVELOPER.value, Resource.AGENT.value, Action.ROTATE.value) is False
    assert is_allowed(Role.DEVELOPER.value, Resource.TENANT.value, Action.DELETE.value) is False
    assert is_allowed(Role.DEVELOPER.value, Resource.DLQ.value, Action.REPLAY.value) is False

    with pytest.raises(PermissionError):
        enforce_rbac(Role.DEVELOPER.value, Resource.AGENT.value, Action.ROTATE.value)


def test_viewer_role_strict_read_only():
    """Viewer role must only have READ access; all mutations and executions must fail."""

    assert is_allowed(Role.VIEWER.value, Resource.WORKFLOW.value, Action.READ.value) is True
    assert is_allowed(Role.VIEWER.value, Resource.RUN.value, Action.READ.value) is True
    assert is_allowed(Role.VIEWER.value, Resource.AUDIT.value, Action.READ.value) is True

    mutations_and_actions = [
        (Resource.WORKFLOW.value, Action.CREATE.value),
        (Resource.WORKFLOW.value, Action.UPDATE.value),
        (Resource.WORKFLOW.value, Action.EXECUTE.value),
        (Resource.CONNECTION.value, Action.CREATE.value),
        (Resource.DLQ.value, Action.REPLAY.value),
        (Resource.TENANT.value, Action.DELETE.value),
    ]

    for res, act in mutations_and_actions:
        assert is_allowed(Role.VIEWER.value, res, act) is False
        with pytest.raises(PermissionError):
            enforce_rbac(Role.VIEWER.value, res, act)
