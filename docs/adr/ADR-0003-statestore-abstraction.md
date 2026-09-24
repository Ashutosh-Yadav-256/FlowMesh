# ADR-0003: Generic StateStore Abstraction for Redis & RediForge

**Date**: 2026-09-19
**Status**: Accepted
**Deciders**: FlowMesh Core Architecture Team

## Context

FlowMesh requires high-performance transient state management for:
- Distributed locks on workflow execution leases.
- Circuit breaker trip states per connection.
- Sliding-window rate limiters.
- Fast idempotency key lookups.

The team has developed **RediForge**, a custom high-performance state engine. However, customer deployments vary: some customers already run managed Redis on AWS ElastiCache, others run GCP Memorystore, while local developers want zero-dependency in-memory execution.

## Decision

FlowMesh introduces an abstract, pluggable `StateStore` interface. RediForge is a first-class supported backend alongside standard Redis and an In-Memory reference implementation:
```text
             StateStore
                 │
       ┌─────────┼─────────┐
       ▼         ▼         ▼
     Redis    RediForge   Memory
```
FlowMesh core workflow logic depends solely on the `StateStore` abstraction. RediForge remains a first-class option without being load-bearing or creating vendor lock-in.

## Alternatives Considered

### Alternative 1: Hardcoding Direct Redis Commands Across All Services
- **Pros**: Slightly less boilerplate.
- **Cons**: Tightly couples the entire platform to Redis; precludes zero-dependency in-memory testing or drop-in RediForge acceleration.

## Consequences

### Positive
- Platform runs with zero external state dependencies during unit tests (`MemoryStateStore`).
- Seamless drop-in adoption for customers running either Redis or RediForge.
- Clear separation between storage mechanics and business workflows.
