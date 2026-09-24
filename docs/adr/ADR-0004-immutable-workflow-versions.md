# ADR-0004: Immutable Workflow Versioning and Pinning

**Date**: 2026-09-19
**Status**: Accepted
**Deciders**: FlowMesh Core Architecture Team

## Context

In long-running business workflows (such as order fulfillment or invoice processing), a workflow execution may take hours, days, or wait on human approvals. If an operator edits and deploys an updated workflow definition while thousands of executions are currently paused or in flight, mutating the definition in-place leads to non-deterministic execution, state corruption, and broken rollback capability.

## Decision

All deployed workflow definitions in FlowMesh are **strictly immutable**.
- Deploying a workflow creates a new version: `version = N + 1`.
- Every workflow run pins the exact `(workflow_id, version)` at the instant of event ingress.
- In-flight runs complete against their pinned version.
- Rollbacks simply point the `current_version` pointer back to version `N - 1` without modifying historical run data.

## Consequences

### Positive
- Zero risk of mid-execution corruption when updating workflow topologies.
- Deterministic event replay: replaying an event from 3 months ago uses the exact workflow topology active when the event occurred.
- Full compliance and auditability.
