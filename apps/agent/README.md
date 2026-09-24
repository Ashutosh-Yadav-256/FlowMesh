# FlowMesh Edge Agent

The FlowMesh Edge Agent securely connects private customer infrastructure to the FlowMesh platform.

The agent is designed for environments where internal services cannot be directly exposed to the public internet.

## Responsibilities

The agent provides:

- Outbound mTLS connectivity
- Connector execution (PostgreSQL, REST, SFTP, SAP, Custom)
- Local discovery (schema, tables, columns, relations)
- Policy enforcement (deny by default allowlist)
- Local buffering (SQLite-backed offline queue)
- Health reporting & metrics
- Secure signed command execution

## Architecture

```text
Customer Network

+------------------------------+
|                              |
| SAP                          |
| PostgreSQL                   |
| Internal APIs                |
| Legacy Services              |
|      |                       |
|      v                       |
| FlowMesh Agent               |
|      |                       |
|      +-- Connector Runtime   |
|      +-- Policy Engine       |
|      +-- Local Queue         |
|      +-- Telemetry           |
|                              |
+--------------+---------------+
               |
               | Outbound mTLS
               |
               v
         FlowMesh Platform
```

## Security Model

The agent **never** executes arbitrary code received from FlowMesh.

Commands must:

1. Be authenticated via Ed25519 signature verification.
2. Be authorized for the agent's tenant.
3. Pass local policy validation (strict declarative allowlist).
4. Target an approved connector.
5. Be recorded in the immutable audit log.

## Installation

### Docker

```bash
docker run \
  --name flowmesh-agent \
  -v ./config:/etc/flowmesh \
  flowmesh/agent:latest
```

### Linux

```bash
curl -fsSL https://install.flowmesh.dev | sh
flowmesh-agent register
systemctl enable flowmesh-agent
systemctl start flowmesh-agent
```

## Offline Behavior

If the control plane becomes temporarily unavailable:

```text
Customer System
      |
      v
Agent
      |
      v
Local Queue (SQLite)
      |
      X (Control Plane unavailable)
      |
      v
Continue buffering locally
      |
      v
Connection restored
      |
      v
Drain and replay pending events
```

## Development

```bash
go test ./...
go run ./cmd/flowmesh-agent
```
