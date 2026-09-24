# ADR-0002: Rejection of Arbitrary Remote Code Execution in Favor of Signed Structured Commands

**Date**: 2026-09-19
**Status**: Accepted
**Deciders**: FlowMesh Core Architecture Team

## Context

Many integration tools and agent platforms allow the central server to transmit arbitrary Python, JavaScript, or shell scripts to customer-side agents for execution. In an enterprise setting, this turns the integration agent into a potential remote code execution (RCE) backdoor. If the central control plane is compromised, an attacker could execute arbitrary code inside the customer's private data center.

## Decision

The FlowMesh Edge Agent **never executes arbitrary code** received from FlowMesh.
All instructions transmitted over the control channel must be:
1. Structured, typed commands (e.g., `connector.execute` targeting a known connector ID).
2. Cryptographically signed by the control plane using Ed25519.
3. Evaluated against a **local declarative deny-by-default policy engine** on the agent.

Even if the control plane dispatches a command, the agent refuses execution if the targeted database, table, or operation is not in its local allowlist.

## Alternatives Considered

### Alternative 1: Transmitting Sandboxed Python/Wasm Scripts
- **Pros**: Extreme flexibility for ad-hoc customer transformations.
- **Cons**: High escape risk; violates enterprise compliance standards (SOC 2, ISO 27001, HIPAA).
- **Why not**: Arbitrary script execution cannot be audited reliably at the perimeter.

## Consequences

### Positive
- Prevents central control plane compromises from escalating to customer network breaches.
- Every operation is auditable with strict parameter validation.
- Enterprise security review pass rate increases dramatically.

### Negative
- Custom connector behaviors must be compiled into or registered as formal connector plugins rather than ad-hoc inline scripts.
