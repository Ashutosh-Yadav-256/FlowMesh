# FlowMesh Enterprise Messaging: Java Message Service (JMS)

## Overview
FlowMesh implements **Jakarta JMS 3.1** via **Apache ActiveMQ Artemis** to provide legacy enterprise messaging compliance (Point-to-Point Queues and Publish/Subscribe Topics).

## Architecture & Destinations
- **Specification**: Jakarta JMS 3.1 (`jakarta.jms.*`)
- **Engine**: Apache ActiveMQ Artemis (Embedded in-process broker or external broker)
- **Point-to-Point Queue**: `flowmesh.jms.queue`
- **Pub/Sub Topic**: `flowmesh.jms.topic`
- **Features**: Persistent delivery, priority routing, correlation ID tracking, and JSON object serialization via `MappingJackson2MessageConverter`.

## Spring Boot REST API Reference
| Endpoint | Method | Description |
| :--- | :--- | :--- |
| `/api/v1/enterprise/messaging/jms/queue/send` | `POST` | Sends a message to the point-to-point JMS queue |
| `/api/v1/enterprise/messaging/jms/topic/publish` | `POST` | Publishes a message to the broadcast JMS topic |
| `/api/v1/enterprise/messaging/jms/status` | `GET` | Returns JMS broker status, destinations, and message counters |
| `/api/v1/enterprise/messaging/jms/messages/recent` | `GET` | Fetches recently sent and received JMS messages |

## Example Usage
```bash
curl -X POST http://localhost:8082/api/v1/enterprise/messaging/jms/queue/send \
  -H "Content-Type: application/json" \
  -d '{
    "tenantId": "tenant_acme",
    "payload": { "batchId": "BATCH-GL-091", "action": "POST_GENERAL_LEDGER" }
  }'
```
