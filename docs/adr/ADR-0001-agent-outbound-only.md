# ADR-0001: Outbound-Only Architecture for Edge Agent

**Date**: 2026-09-19
**Status**: Accepted
**Deciders**: FlowMesh Core Architecture Team

## Context

Enterprise environments host mission-critical databases, SAP ERP instances, and internal microservices within private networks (e.g., `10.0.0.0/8`). Requiring enterprise security teams to punch inbound firewall holes or configure complex public ingress gateways to allow FlowMesh to trigger internal systems creates unacceptable security exposure and severe enterprise sales friction.

## Decision

The FlowMesh Edge Agent connects to the FlowMesh Control Plane **exclusively via outbound mTLS over WebSocket/HTTPS**. No inbound ports are opened on the customer network. The agent dials out from behind corporate firewalls/NAT, establishes a persistent bidirectional multiplexed channel, sends periodic heartbeats, and receives signed command dispatches.

## Alternatives Considered

### Alternative 1: Inbound Webhooks & Port Forwarding
- **Pros**: Simple cloud-to-customer direct calls.
- **Cons**: Requires customers to modify perimeter firewalls, configure reverse proxies, and expose internal APIs to the public internet.
- **Why not**: Enterprise SecOps teams routinely reject inbound firewall exceptions.

### Alternative 2: Dedicated Cloud-Managed VPN Tunnels (IPsec / WireGuard)
- **Pros**: Network-level transparency.
- **Cons**: High operational complexity, requires network admin privileges, risk of lateral network movement.
- **Why not**: Too heavy; an application-level outbound agent with least-privilege scoping is simpler and safer.

## Consequences

### Positive
- Zero inbound ports required on customer firewalls.
- Compatible with corporate HTTP proxies and standard egress egress filtering.
- Customers maintain 100% control over physical networking.

### Negative
- Requires maintaining persistent outbound WebSocket connections with reconnection logic and backoff.
- Agent must buffer locally (via SQLite) during control plane disconnections.
