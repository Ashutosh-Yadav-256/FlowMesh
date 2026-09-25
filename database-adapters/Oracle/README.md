# FlowMesh Enterprise Database Adapter: Oracle Database

## Overview
The **Oracle Database Enterprise Adapter** (`OracleDatabaseAdapter.java`) enables zero-lock-in connectivity with enterprise ERP databases (SAP on Oracle, Oracle E-Business Suite, General Ledger, Accounts Payable).

## Architectural Specifications
- **Driver**: `com.oracle.database.jdbc:ojdbc11` (v23.4.0.24.05)
- **Dialect**: Oracle 23ai / PL-SQL (`SELECT ... FROM DUAL`, `OFFSET x ROWS FETCH NEXT y ROWS ONLY`)
- **Connection String**: `jdbc:oracle:thin:@<host>:1521/<service_name>`
- **Pool**: Oracle Universal Connection Pool (UCP) / HikariCP
- **Failover / Simulation**: Includes automated fallback simulation for zero-downtime local validation and testing.

## Spring Boot REST API Reference
| Endpoint | Method | Description |
| :--- | :--- | :--- |
| `/api/v1/enterprise/database/adapters/ORACLE/test` | `POST` | Pings Oracle instance or verifies virtual connection |
| `/api/v1/enterprise/database/adapters/ORACLE/query` | `POST` | Executes Oracle SQL / PL-SQL with pagination |
| `/api/v1/enterprise/database/adapters/ORACLE/tables` | `GET` | Introspects tables (`ERP_TRANSACTIONS`, `GL_LEDGER_ENTRIES`, `AP_INVOICES_ALL`) |
| `/api/v1/enterprise/database/adapters/ORACLE/pool` | `GET` | Returns connection pool statistics |

## Example Usage
```bash
curl -X POST http://localhost:8082/api/v1/enterprise/database/adapters/ORACLE/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "SELECT TXN_ID, ACCOUNT_CODE, AMOUNT_USD FROM ERP_TRANSACTIONS WHERE STATUS = 'POSTED'",
    "parameters": [],
    "maxRows": 25
  }'
```
