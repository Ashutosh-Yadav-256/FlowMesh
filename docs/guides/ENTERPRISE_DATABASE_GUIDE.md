# FlowMesh Enterprise Database Design & SQL Optimization Guide

This specification details database modeling, indexing strategies, and query optimization patterns for high-throughput enterprise deployments across **PostgreSQL 16**, **Oracle Database 19c/21c/23ai**, and **Microsoft SQL Server 2022**.

---

## 1. Relational Schema Architecture & Tenancy Isolation

FlowMesh enforces tenant isolation at the database layer using the **Tenant-Scoped Repository Pattern**:
- Every query must predicate on `tenant_id`
- Composite primary and foreign keys include `tenant_id` as the leading column
- Prevents cross-tenant table scans and guarantees optimal index hit ratios

```
┌────────────────────────────────────────────────────────┐
│                   Tenants (Master Table)               │
│ id (PK) | name | plan | status | created_at            │
└───────────────────────────┬────────────────────────────┘
                            │ 1:N
┌───────────────────────────▼────────────────────────────┐
│              Workflow Definitions                      │
│ id (PK) | tenant_id (FK, Leading) | dag_spec | status  │
└───────────────────────────┬────────────────────────────┘
                            │ 1:N
┌───────────────────────────▼────────────────────────────┐
│              Workflow Runs (Partitioned)               │
│ id (PK) | tenant_id (Leading) | status | created_at   │
└────────────────────────────────────────────────────────┘
```

---

## 2. PostgreSQL 16 Optimization Strategies

### A. Declarative Range Partitioning for High-Volume Tables
High-volume event and execution tables (`workflow_runs`, `audit_logs`, `event_records`) utilize PostgreSQL native declarative partitioning by month:

```sql
-- Partitioned master table
CREATE TABLE workflow_runs (
    id VARCHAR(64) NOT NULL,
    tenant_id VARCHAR(64) NOT NULL,
    workflow_id VARCHAR(64) NOT NULL,
    status VARCHAR(32) NOT NULL,
    triggered_by VARCHAR(64),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    completed_at TIMESTAMPTZ,
    PRIMARY KEY (id, created_at)
) PARTITION BY RANGE (created_at);

-- Monthly partition slices
CREATE TABLE workflow_runs_2026_09 PARTITION OF workflow_runs
    FOR VALUES FROM ('2026-09-01 00:00:00+00') TO ('2026-10-01 00:00:00+00');

CREATE TABLE workflow_runs_2026_10 PARTITION OF workflow_runs
    FOR VALUES FROM ('2026-10-01 00:00:00+00') TO ('2026-11-01 00:00:00+00');
```

**Benefits**:
- **Partition Pruning**: Queries filtering by date scan only the relevant monthly partition rather than millions of rows.
- **Fast Retention Dropping**: Purging aged logs executes as instant `DROP TABLE partition_name` instead of heavy `DELETE` scans that cause table bloat.

---

### B. Composite & Partial Index Optimization

To guarantee sub-5ms query response times on dashboard filters:

```sql
-- 1. High-frequency tenant run lookup
CREATE INDEX idx_runs_tenant_status_created 
ON workflow_runs (tenant_id, status, created_at DESC);

-- 2. Partial index for active/in-flight runs only (avoids indexing millions of completed runs)
CREATE INDEX idx_active_runs 
ON workflow_runs (tenant_id, created_at) 
WHERE status IN ('RUNNING', 'QUEUED');

-- 3. GIN index for JSON payload path search
CREATE INDEX idx_audit_payload_gin 
ON audit_logs USING GIN (metadata jsonb_path_ops);
```

---

### C. Query Optimization & EXPLAIN ANALYZE Checklist
1. **Avoid `SELECT *`**: Always project required columns to leverage Index-Only Scans.
2. **Strict Parameterization**: Use prepared statements with bind variables to prevent SQL injection and enable query plan caching.
3. **Connection Pooling**: Tune HikariCP or PgBouncer with `pool_size = 20-50` and `max_idle_time = 30000ms`.
4. **Vacuum & Analyze Hygiene**: Set `autovacuum_vacuum_scale_factor = 0.05` on write-heavy tables.

---

## 3. Oracle Database 19c/21c Enterprise Patterns

- **Index-Organized Tables (IOT)**: Used for high-frequency key-value checkpoint lookups.
- **PL/SQL Bulk Binding**: Use `FORALL` and `BULK COLLECT INTO` for batch ingest of thousands of integration rows in a single network round-trip.
- **Result Cache**: Enable `/*+ RESULT_CACHE */` hint on read-mostly reference schemas.

---

## 4. Microsoft SQL Server 2022 Enterprise Patterns

- **Filtered Indexes**: Equivalent to PostgreSQL partial indexes, reducing index space on disk by up to 90%.
- **Clustered Columnstore Indexes (CCI)**: For historical audit analytics queries aggregating millions of records.
- **Optimized Locking (SQL 2022)**: Enable `READ_COMMITTED_SNAPSHOT` (RCSI) to prevent read-write blocking concurrency bottlenecks.
