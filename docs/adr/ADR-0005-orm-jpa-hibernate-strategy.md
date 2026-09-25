# ADR-0005: Enterprise ORM, Jakarta Persistence 3.1 & Hibernate 6 Architecture

**Date**: 2026-09-25  
**Status**: Accepted  
**Deciders**: FlowMesh Core Architecture & Data Platform Engineering Team  

## Context

FlowMesh enterprise processing demands transactional guarantees, multi-tenant isolation, auditability, and consistent data transformations across heterogeneous backends (PostgreSQL, Oracle, SQL Server). Historically, data-access layers in distributed enterprise systems face several recurring pitfalls:

1. **The $N+1$ Query Anti-Pattern**: Naive ORM mapping of 1-to-many relationships (e.g., Transactions to Audit Trail Entries) results in a flurry of individual SELECT queries per row during reconciliation batches, degrading database throughput.
2. **Lost Updates & Race Conditions**: High-frequency concurrent workflow engines updating the same entity without synchronization cause silent data overrides.
3. **Data Loss via Hard Deletions**: Regulatory compliance (SOC-2, HIPAA, ISO-27001) strictly mandates audit trails; physical record deletion destroys evidentiary chains.
4. **Impedance Mismatch in Complex Domains**: Primitive string/number representations of financial quantities cause currency misalignment, precision loss, and unstructured metadata sprawl.

## Decision

We adopt **Jakarta Persistence (JPA 3.1) with Hibernate 6** for enterprise persistence in `enterprise-worker`, adhering to the following architectural patterns:

### 1. Optimistic Locking via Versioning
All state-bearing domain aggregates incorporate `@Version private Long version;`. 
- Hibernate automatically appends `AND version = ?` to all SQL `UPDATE` statements.
- Concurrent updates on stale data fail fast with `OptimisticLockException` (translated to Spring's `ObjectOptimisticLockingFailureException`), safeguarding transactional integrity without high-cost database row-level locking.

### 2. Elimination of $N+1$ Queries via `@NamedEntityGraph`
Entities declaring 1-to-many child collections declare explicit Named Entity Graphs:
```java
@NamedEntityGraph(
    name = "EnterpriseTransaction.withAuditEntries",
    attributeNodes = @NamedAttributeNode("auditEntries")
)
```
Repositories invoke these graphs dynamically via `@EntityGraph(value = "EnterpriseTransaction.withAuditEntries", type = EntityGraph.EntityGraphType.LOAD)`, compiling into a single SQL `LEFT OUTER JOIN` fetching both parent and children in $O(1)$ database trips.

### 3. Soft Deletes via Modern Hibernate 6 Annotations
Physical deletions are intercepted at the ORM layer:
- `@SQLDelete(sql = "UPDATE enterprise_transactions SET deleted = true WHERE id = ? AND version = ?")`
- `@SQLRestriction("deleted = false")` (replacing legacy Hibernate 5 `@Where`)
Queries transparently filter out soft-deleted records, while administrative recovery tools retain full historical visibility.

### 4. Domain-Driven Value Objects & Attribute Converters
- Money is represented as a first-class `@Embeddable MonetaryAmount(BigDecimal amount, String currency)` with scale 2 precision.
- Arbitrary JSON metadata is handled via a dedicated `AttributeConverter<Map<String, Object>, String>`, providing seamless mapping to relational `TEXT` or `JSONB` without leaking database specifics into the domain model.

### 5. Type-Safe Dynamic Querying via JPA Criteria API
Dynamic dashboard and reconciliation queries utilize `JpaSpecificationExecutor<EnterpriseTransaction>` with composable `Specification` predicates, preventing SQL injection vulnerabilities while supporting complex multi-tenant filters.

## Alternatives Considered

### Alternative 1: Plain Spring JDBC / JdbcTemplate
- **Pros**: Direct control over raw SQL execution; minimal runtime abstraction overhead.
- **Cons**: Requires substantial manual boilerplate for result set mapping, dirty checking, audit logging, and relationship traversal. Prone to synchronization omissions in optimistic locking.

### Alternative 2: MyBatis or jOOQ
- **Pros**: Excellent SQL-centric developer experience; compile-time SQL validation.
- **Cons**: Introduces additional proprietary query paradigms and lacks native aggregate root state management, lifecycle callbacks (`@PrePersist`, `@PreUpdate`), and declarative entity graph joins.

## Consequences

### Positive
- **Guaranteed Consistency**: Zero lost updates across distributed worker threads.
- **High Throughput**: Eager join fetching via entity graphs completely eliminates $N+1$ latency spikes during bulk reconciliation.
- **Compliance Ready**: Soft-delete semantics ensure immutable historical compliance logs.
- **Testability**: Clean slice testing via Spring Boot `@DataJpaTest` with zero external database dependencies during local verification.

### Negative
- **Learning Curve**: Developers must strictly understand Hibernate session lifecycle (managed vs. detached entities, first-level cache persistence context) to prevent unintended flushes.
