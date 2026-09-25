# FlowMesh Enterprise Database Adapter: Microsoft SQL Server

## Overview
The **SQL Server Enterprise Adapter** (`SqlServerDatabaseAdapter.java`) facilitates direct integration with Microsoft SQL Server 2019/2022 instances, Active Directory synced tables, and corporate Windows server fleets.

## Architectural Specifications
- **Driver**: `com.microsoft.sqlserver:mssql-jdbc`
- **Dialect**: T-SQL (`SELECT TOP (n)`, `sys.tables`, `INFORMATION_SCHEMA`)
- **Connection String**: `jdbc:sqlserver://<host>:1433;databaseName=<db>;encrypt=false;trustServerCertificate=true`
- **Security**: Supports SQL Server Authentication and Integrated Windows / Kerberos Authentication.
- **Failover / Simulation**: Includes enterprise simulation engine when running tests or isolated staging environments.

## Spring Boot REST API Reference
| Endpoint | Method | Description |
| :--- | :--- | :--- |
| `/api/v1/enterprise/database/adapters/SQL_SERVER/test` | `POST` | Validates SQL Server connectivity and T-SQL version |
| `/api/v1/enterprise/database/adapters/SQL_SERVER/query` | `POST` | Runs T-SQL queries with timeout and row bounding |
| `/api/v1/enterprise/database/adapters/SQL_SERVER/tables` | `GET` | Introspects `dbo.EnterpriseAuditLogs`, `dbo.SyncQueueItem`, and directory tables |
| `/api/v1/enterprise/database/adapters/SQL_SERVER/pool` | `GET` | Returns active connection pool telemetry |

## Example Usage
```bash
curl -X POST http://localhost:8082/api/v1/enterprise/database/adapters/SQL_SERVER/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "SELECT TOP (10) EventId, ActionType, TargetEntity FROM EnterpriseAuditLogs WHERE TenantId = 'tenant_acme'",
    "parameters": [],
    "maxRows": 10
  }'
```
