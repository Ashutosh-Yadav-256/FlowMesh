# FlowMesh Enterprise Messaging: RabbitMQ

## Overview
FlowMesh leverages **RabbitMQ** (AMQP 0-9-1) for decoupled event routing, reliable transaction event streaming, and automated dead-letter queue (DLQ) processing.

## Architecture & Topology
- **Direct Exchange**: `flowmesh.direct` (durable)
- **Dead-Letter Exchange (DLX)**: `flowmesh.dlx` (durable)
- **Transaction Queue**: `flowmesh.transactions.queue`
  - Dead-letter routing key: `transaction.dlq`
  - Message TTL: 86,400,000 ms (24 hours)
- **Dead-Letter Queue (DLQ)**: `flowmesh.dlq`
- **Routing Key**: `transaction.process`
- **Payload Format**: Jackson-serialized `EnterpriseMessage` with `X-Trace-ID`, `X-Tenant-ID`, and correlation ID.

## Docker Compose
In `docker-compose.yml`, RabbitMQ is provisioned with the management plugin enabled:
- AMQP Port: `5672`
- Management Web UI: `http://localhost:15672` (Credentials: `flowmesh` / `flowmesh_secure_password`)

## Spring Boot REST API Reference
| Endpoint | Method | Description |
| :--- | :--- | :--- |
| `/api/v1/enterprise/messaging/rabbitmq/publish` | `POST` | Publishes message to RabbitMQ exchange |
| `/api/v1/enterprise/messaging/rabbitmq/status` | `GET` | Returns broker health, queues, and dispatch counts |
| `/api/v1/enterprise/messaging/rabbitmq/messages/recent` | `GET` | Fetches recent dispatched and consumed messages |

## Example Usage
```bash
curl -X POST http://localhost:8082/api/v1/enterprise/messaging/rabbitmq/publish \
  -H "Content-Type: application/json" \
  -d '{
    "tenantId": "tenant_acme",
    "routingKey": "transaction.process",
    "payload": { "transactionId": "TXN-9081", "amount": 4500.0, "status": "APPROVED" }
  }'
```
