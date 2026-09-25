# FlowMesh Enterprise Database Adapter: PostgreSQL

## Overview
The **PostgreSQL Enterprise Adapter** (`PostgreSqlDatabaseAdapter.java`) provides high-throughput relational persistence, multi-tenant row isolation, and dynamic schema introspection within the FlowMesh Enterprise Worker (`services/enterprise-worker`).

## Architectural Specifications
- **Driver**: `org.postgresql:postgresql` (JDBC 4.2 compliant)
- **Connection Pool**: HikariCP (`FlowMeshEnterpriseHikariCP`), maximum pool size: 20, minimum idle: 5, connection timeout: 10,000ms.
- **Dialect**: Hibernate 6 / Spring Data JPA `PostgreSQLDialect`
- **Port**: Default `5432`
- **Schema Introspection**: Live queries against `information_schema.tables` and `information_schema.columns`.

## Spring Boot REST API Reference
| Endpoint | Method | Description |
| :--- | :--- | :--- |
| `/api/v1/enterprise/database/adapters/POSTGRESQL/test` | `POST` | Executes `SELECT 1, version()` and measures latency |
| `/api/v1/enterprise/database/adapters/POSTGRESQL/query` | `POST` | Executes parameterized query with row bounds and timeout |
| `/api/v1/enterprise/database/adapters/POSTGRESQL/tables` | `GET` | Introspects schema tables and column metadata |
| `/api/v1/enterprise/database/adapters/POSTGRESQL/pool` | `GET` | Returns live HikariCP pool metrics (active, idle, threads waiting) |

## Example Usage
```bash
curl -X POST http://localhost:8082/api/v1/enterprise/database/adapters/POSTGRESQL/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "SELECT * FROM enterprise_transactions WHERE tenant_id = ? LIMIT 10",
    "parameters": ["tenant_acme"],
    "timeoutSeconds": 10,
    "maxRows": 10
  }'
```
