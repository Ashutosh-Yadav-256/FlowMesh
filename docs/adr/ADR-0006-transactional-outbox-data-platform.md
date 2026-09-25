# ADR-0006: Transactional Outbox Pattern & Data Platform Schema Governance

**Date**: 2026-09-25  
**Status**: Accepted  
**Deciders**: FlowMesh Core Architecture & Data Platform Engineering Team  

## Context

In distributed enterprise architectures, services must execute business logic, mutate state in relational datastores, and notify downstream data pipelines (Kafka, RabbitMQ, JMS, Lakehouse ingestion) of domain state changes.

Direct dual-writing (e.g., executing `repository.save(transaction)` and immediately invoking `rabbitTemplate.send(event)`) suffers from the classic **Dual-Write Problem**:
- If the broker publish succeeds but the database transaction rolls back, downstream consumers process phantom events that never existed in the system of record.
- If the database commits but the broker publish fails due to a network partition, downstream consumers suffer from silent event loss, corrupting analytical models and downstream reconciliation.

Furthermore, enterprise data lakehouses and stream consumers are vulnerable to **Schema Drift**:
- Producers altering column data types or removing fields without notice break downstream SQL/Spark ETL pipelines.
- Pipelines require explicit **Data Contracts** with automated drift classification prior to ingestion.

## Decision

FlowMesh adopts the **Transactional Outbox Pattern** combined with a **Contract-First Schema Engine** for all data platform integrations:

```text
┌────────────────────────────────────────────────────────┐
│               ACID Database Transaction                │
│                                                        │
│  ┌───────────────────────┐   ┌──────────────────────┐  │
│  │ Enterprise Transaction │   │     Outbox Event     │  │
│  │   (Business State)    │   │  (Domain Event Log)  │  │
│  └───────────────────────┘   └──────────────────────┘  │
└──────────────────────────────────────────┬─────────────┘
                                           │ Commit
                                           ▼
                            ┌────────────────────────────┐
                            │    Outbox Poller/Streamer  │
                            │ (At-Least-Once Dispatcher) │
                            └──────────────┬─────────────┘
                                           │
                    ┌──────────────────────┼─────────────────────┐
                    ▼                      ▼                     ▼
             RabbitMQ / AMQP          Apache Artemis JMS       Apache Kafka
```

### 1. Atomic Outbox Persistence
Every state mutation creates an `OutboxEvent` record persisted into the `data_platform_outbox_events` table within the exact same database transaction boundary as the primary entity.

### 2. At-Least-Once Dispatching
A dedicated dispatcher (`TransactionalOutboxService`) queries unprocessed outbox records, dispatches payloads to configured message brokers (RabbitMQ, JMS, Kafka), and marks them `processed = true` with a timestamp upon successful broker acknowledgement.

### 3. Schema Contract & Drift Classification Engine
The `DataPlatformSchemaEngine` evaluates incoming payloads against strict data contracts and evaluates proposed schema evolutions into three standard tiers:
- `COMPATIBLE`: Field names and types match baseline 100%.
- `NON_BREAKING_ADDITIVE`: New nullable/additive fields introduced; backward-compatible for existing downstream consumers.
- `CRITICAL_BREAKING`: Dropped columns or altered data types; pipeline execution is halted and flagged for schema review.

## Alternatives Considered

### Alternative 1: Two-Phase Commit (2PC / XA Transactions)
- **Pros**: Native multi-resource ACID coordination.
- **Cons**: High latency, single point of coordinator failure, and lack of support across modern cloud-native message brokers and serverless databases.

### Alternative 2: Change Data Capture (CDC) via Debezium only
- **Pros**: Reads directly from database write-ahead log (WAL) without custom polling code.
- **Cons**: Requires complex Kafka Connect infrastructure and infrastructure-level DB privileges (e.g., `REPLICATION` in PostgreSQL), which may not be feasible in restricted enterprise environments. The outbox table serves as an ideal intermediate CDC source when Debezium is deployed.

## Consequences

### Positive
- **Zero Event Loss**: Guaranteed at-least-once delivery; database commits and event emissions are strictly fate-shared.
- **Resilience**: Outbox dispatch survives message broker downtime; events queue up safely in the database and flush automatically once the broker recovers.
- **Deterministic Schema Evolution**: Ingestion pipelines proactively reject breaking schema modifications before downstream analytics jobs fail.

### Negative
- **At-Least-Once Semantics**: Downstream consumers must be idempotent (e.g., using aggregate ID deduplication or idempotency keys).
- **Table Growth**: Requires automated periodic archival or pruning of processed outbox entries.
