# FlowMesh Enterprise Requirements, System Design & Architecture Specifications

This document defines the formal software engineering requirements, architecture designs, and C4 models for the FlowMesh Enterprise Platform.

---

## 1. Requirements Engineering

### 1.1 Stakeholder Personas
- **Enterprise Architect**: Requires standardized integration patterns (JPA 3.1, Outbox, AMQP/JMS), zero vendor lock-in, and clear architectural boundaries.
- **Data Platform Engineer**: Requires guaranteed at-least-once domain event emission, schema contract enforcement, and automated schema drift detection.
- **Compliance & Security Officer**: Demands immutable audit trails, optimistic concurrency locking, soft deletes, and SOC-2/ISO-27001 traceability.
- **SRE & DevOps Engineer**: Demands JMX/Prometheus telemetry, dual-deployment options (embedded container vs. external Tomcat WAR), and graceful degradation.

### 1.2 Functional Requirements (FR)
| ID | Requirement | Priority | Implementation Component |
|:---|:---|:---|:---|
| **FR-01** | Multi-database adapter layer for PostgreSQL, Oracle, and SQL Server with connection validation and pool statistics. | High | `io.flowmesh.enterprise.adapters.db` |
| **FR-02** | Distributed caching and atomic distributed locking with TTL. | High | `io.flowmesh.enterprise.redis` |
| **FR-03** | Dual-broker enterprise messaging supporting AMQP (RabbitMQ) and JMS (Apache Artemis). | High | `io.flowmesh.enterprise.messaging` |
| **FR-04** | JMX MBean instrumentation for live heap, thread count, transaction throughput, and garbage collection metrics. | Medium | `io.flowmesh.enterprise.monitoring.jmx` |
| **FR-05** | Dual-deployment capability: standalone Spring Boot executable JAR or external Tomcat WAR archive. | High | `io.flowmesh.enterprise.deployment` |
| **FR-06** | Optimistic concurrency control via versioning and non-destructive soft deletes with automatic filtering. | Critical | `io.flowmesh.enterprise.orm` |
| **FR-07** | Transactional Outbox pattern guaranteeing zero event loss and eliminating dual-write anomalies. | Critical | `io.flowmesh.enterprise.dataplatform` |
| **FR-08** | Runtime data contract validation and schema drift classification (`COMPATIBLE`, `NON_BREAKING_ADDITIVE`, `CRITICAL_BREAKING`). | Critical | `io.flowmesh.enterprise.dataplatform.schema` |
| **FR-09** | Modern React enterprise web console with real-time health checks, metrics, and system controls. | High | `apps/web/src/app/enterprise/page.tsx` |
| **FR-10** | Zero-dependency legacy AJAX console (`XMLHttpRequest`) for constrained or legacy browser environments. | Medium | `web-console/legacy-AJAX-demo` |

### 1.3 Non-Functional Requirements (NFR)
- **NFR-01: Performance & Latency**: API endpoints must respond with $p99 < 50\text{ms}$ under standard workload; in-memory caching must respond in $< 2\text{ms}$.
- **NFR-02: Scalability**: Worker service must leverage Java Virtual Threads (Project Loom) to support $> 5,000\text{ TPS}$ per instance without OS thread exhaustion.
- **NFR-03: Zero Data Loss**: Outbox events must be fate-shared with business state in an ACID transaction boundary.
- **NFR-04: Multi-Tenant Isolation**: Database queries and concurrency controllers must stripe work per `tenant_id`.
- **NFR-05: Auditability & Security**: MDC logging filters must propagate `traceId`, `tenantId`, and `userId` across all log messages.
- **NFR-06: Portability**: Tests must run without external dependencies via embedded H2 and embedded Artemis.

---

## 2. System Design & C4 Architecture

### 2.1 C4 Level 1: System Context Diagram
```mermaid
C4Context
    title FlowMesh Enterprise Platform - System Context
    Person(operator, "Enterprise Operator", "Monitors pipelines, executes transactions, analyzes drift")
    System(flowmesh, "FlowMesh Platform", "Orchestrates enterprise workflows, manages transactions, dispatches events")
    System_Ext(postgres, "PostgreSQL", "System of Record / Relational Storage")
    System_Ext(oracle, "Oracle ERP", "Core Enterprise Legacy ERP")
    System_Ext(sqlserver, "SQL Server", "Enterprise Data Warehouse")
    System_Ext(rabbitmq, "RabbitMQ", "Enterprise Message Broker")
    System_Ext(artemis, "Apache Artemis", "JMS Broker")
    System_Ext(redis, "Redis / RediForge", "Distributed Cache & State Store")

    Rel(operator, flowmesh, "Interacts via React Console / REST API", "HTTPS")
    Rel(flowmesh, postgres, "Reads/Writes State & Outbox", "JDBC/JPA")
    Rel(flowmesh, oracle, "Queries Metadata & Syncs", "JDBC")
    Rel(flowmesh, sqlserver, "Extracts Tables", "JDBC")
    Rel(flowmesh, rabbitmq, "Publishes AMQP Events", "AMQP")
    Rel(flowmesh, artemis, "Sends JMS Messages", "JMS/OpenWire")
    Rel(flowmesh, redis, "Acquires Locks & Caches", "RESP")
```

### 2.2 C4 Level 2: Container Diagram
```mermaid
C4Container
    title FlowMesh Enterprise Platform - Containers
    Container(web, "Next.js Web Console", "React 19, TypeScript, Tailwind CSS", "Modern Enterprise Management UI")
    Container(legacyWeb, "Legacy AJAX Console", "HTML5, Vanilla JS, CSS3", "Zero-dependency fallback console")
    Container(worker, "Enterprise Worker", "Java 17, Spring Boot 3.3.2, Hibernate 6", "Processes transactions, manages outbox, exposes REST/JMX")
    ContainerDb(db, "Primary Relational DB", "PostgreSQL 16", "Stores transactions, audit logs, outbox queue")
    ContainerDb(cache, "State Store", "Redis / RediForge", "Holds distributed locks and fast cache")
    Container(queue, "Message Brokers", "RabbitMQ & Artemis", "Asynchronous event distribution")

    Rel(web, worker, "API Requests", "REST / JSON")
    Rel(legacyWeb, worker, "AJAX Calls", "HTTP / JSON")
    Rel(worker, db, "JPA / Hibernate ORM", "JDBC")
    Rel(worker, cache, "Locks / Cache", "Jedis / Lettuce")
    Rel(worker, queue, "Dispatches Outbox Events", "AMQP / JMS")
```

### 2.3 C4 Level 3: Component Diagram (Enterprise Worker)
```mermaid
graph TD
    subgraph REST Ingress
        AC[DatabaseAdapterController]
        RC[RedisCacheController]
        MC[RabbitMqController / JmsController]
        JC[JmxMonitoringController]
        DC[DeploymentInfoController]
        DPC[DataPlatformController]
    end

    subgraph Core Services
        DAR[DatabaseAdapterRegistry]
        RDS[RedisDistributedLockService]
        RCS[RedisCacheService]
        TOS[TransactionalOutboxService]
        DSE[DataPlatformSchemaEngine]
        JMS_S[JmxMonitoringService]
    end

    subgraph Persistence Layer
        ETR[EnterpriseTransactionRepository]
        OER[OutboxEventRepository]
        TAR[TransactionAuditEntryRepository]
        TS[TransactionSpecification]
    end

    AC --> DAR
    RC --> RDS
    RC --> RCS
    DPC --> TOS
    DPC --> DSE
    JC --> JMS_S

    TOS --> OER
    TOS --> ETR
    ETR --> TS
```

---

## 3. State Machines & ER Models

### 3.1 Enterprise Transaction Lifecycle
```mermaid
stateDiagram-v2
    [*] --> PENDING: Ingress Request
    PENDING --> PROCESSING: Worker Lease Acquired
    PROCESSING --> COMMITTED: Business Logic Validated & Fate-Shared Outbox Written
    PROCESSING --> REJECTED: Validation or Business Rule Failed
    PROCESSING --> RETRYING: Transient I/O or Lock Collision
    RETRYING --> PROCESSING: Exponential Backoff
    RETRYING --> REJECTED: Max Retries Exceeded
    COMMITTED --> [*]: Final State
    REJECTED --> [*]: Final State
```

### 3.2 Transactional Outbox Lifecycle
```mermaid
stateDiagram-v2
    [*] --> PENDING_DISPATCH: Appended in Business Transaction (processed=false)
    PENDING_DISPATCH --> DISPATCHING: Polled by Outbox Worker
    DISPATCHING --> DISPATCHED: Published to Broker & ACK Received (processed=true)
    DISPATCHING --> PENDING_DISPATCH: Broker Unreachable (retry with backoff)
    DISPATCHED --> ARCHIVED: Scheduled Retention Cleanup (>30 days)
    ARCHIVED --> [*]
```

### 3.3 Entity-Relationship (ER) Diagram
```mermaid
erDiagram
    ENTERPRISE_TRANSACTIONS ||--o{ TRANSACTION_AUDIT_ENTRIES : contains
    ENTERPRISE_TRANSACTIONS {
        bigint id PK
        varchar_64 tenant_id
        varchar_128 external_reference
        numeric_18_2 amount
        varchar_3 currency
        varchar_64 source_system
        varchar_64 target_system
        varchar_32 status
        text metadata
        bigint version
        boolean deleted
        timestamp created_at
        timestamp updated_at
    }

    TRANSACTION_AUDIT_ENTRIES {
        bigint id PK
        bigint transaction_id FK
        varchar_64 action
        varchar_64 actor
        varchar_512 details
        timestamp performed_at
    }

    DATA_PLATFORM_OUTBOX_EVENTS {
        bigint id PK
        varchar_64 tenant_id
        varchar_64 aggregate_type
        varchar_128 aggregate_id
        varchar_64 event_type
        text payload
        boolean processed
        timestamp created_at
        timestamp processed_at
    }
```
