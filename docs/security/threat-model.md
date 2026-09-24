# FlowMesh Security Architecture & Threat Model (STRIDE)

## 1. Security Philosophy

FlowMesh is built on three uncompromisable security foundations:
1. **The customer owns their infrastructure and data**: Data stays within the customer VPC unless explicitly transformed or exported by an approved, versioned workflow.
2. **Zero inbound ports on Edge Agents**: The Edge Agent initiates outbound mTLS connections exclusively. Customer corporate firewalls remain completely closed to external ingress.
3. **Rejection of arbitrary remote code execution**: The central control plane cannot push scripts, shell commands, or arbitrary bytecode to Edge Agents. All commands are strictly typed, declarative structural operations verified against local deny-by-default allowlists.

---

## 2. Trust Boundaries

```text
               PUBLIC INTERNET / UNTRUSTED CLIENTS
                               │
                [HTTPS / CloudEvents / Webhooks]
                               │
┌──────────────────────────────▼────────────────────────────────┐
│ FLOWMESH CONTROL & DATA PLANE (TRUST BOUNDARY A)              │
│                                                               │
│  ├── API Gateway (OIDC Authentik / JWT / RBAC)                │
│  ├── NATS JetStream (Tenant Stream Partitioning)              │
│  ├── PostgreSQL 16 (Tenant-Scoped Row Isolation)              │
│  ├── Envelope Encryption Key Engine (Master KEK in KMS)       │
│  └── Control Plane Asymmetric Signer (Ed25519 Private Key)   │
└──────────────────────────────┬────────────────────────────────┘
                               │
               OUTBOUND ONLY mTLS WEBSOCKET / POLLING
             (No Inbound Ports, Client Cert Required)
                               │
┌──────────────────────────────▼────────────────────────────────┐
│ CUSTOMER PRIVATE NETWORK / VPC (TRUST BOUNDARY B)             │
│                                                               │
│  FLOWMESH EDGE AGENT (Go Static Daemon)                       │
│  ├── Cryptographic Signature Verifier (Control Plane PubKey)  │
│  ├── Local Declarative Policy Engine (DENY by Default)        │
│  ├── Local SQLite Buffer (0700 File Permissions)              │
│  └── Connector Runtime (PostgreSQL, REST, SAP, SFTP)          │
│                                                               │
│       ┌─────────────────────┬───────────────────┐             │
│       ▼                     ▼                   ▼             │
│   Private DB          Internal REST         Private SAP       │
└───────────────────────────────────────────────────────────────┘
```

---

## 3. STRIDE Threat Analysis & Mitigations

| Category | Threat Scenario | FlowMesh Architectural Mitigation |
| :--- | :--- | :--- |
| **Spoofing (Identity)** | Rogue entity pretends to be the central Control Plane to send commands to an Edge Agent. | **Mandatory Ed25519 Command Signing**: Every command payload is canonically serialized and signed by the Control Plane private key. Edge Agents verify the signature against pinned public keys before inspecting the command. Unsigned or tampered commands fail closed (`REJECTED_SIGNATURE`). |
| **Spoofing (Agent)** | Malicious actor impersonates a legitimate Edge Agent to receive sensitive workflow tasks. | **Single-Use Enrollment Tokens & mTLS**: Agent enrollment generates unique Ed25519 key pairs with mutual TLS certificate binding. Enrollment tokens are one-time and expire in 15 minutes. |
| **Tampering (Data)** | Attacker alters a command payload in transit or tampers with connection credentials. | **Envelope Encryption & Signature Verification**: All credentials are encrypted with tenant-specific DEKs via AES-256-GCM (authenticated encryption with associated data). Command tampering breaks cryptographic signature verification. |
| **Repudiation** | An operator denies deploying a malicious workflow or executing a mutating connection command. | **Append-Only Immutable Audit Ledger**: Every mutating operation, deployment, rollback, and agent command execution generates an unalterable audit event record (`audit_events`) with author attribution and SHA-256 checksums. |
| **Information Disclosure** | Cross-tenant data leak where Tenant B accesses Tenant A's database credentials or workflow runs. | **Tenant-Scoped Repository Isolation**: All database queries are scoped strictly by `tenant_id` at the repository layer. Cross-tenant lookups return HTTP 404 to avoid leaking resource existence. Connection secrets are write-only over the API and never returned in plaintext. |
| **Denial of Service** | Upstream target service outage or network partition overwhelms workflow engine or edge agents. | **Distributed Circuit Breakers & Dead Letter Queues**: StateStore circuit breakers trip to `OPEN` on consecutive failures, fast-failing downstream requests without exhausting connection pools. Edge agents buffer to local SQLite with FIFO size and age caps. |
| **Elevation of Privilege** | Attacker commands Edge Agent to drop production tables or read unauthorized employee records. | **Deny-by-Default Policy Engine (ADR-0002)**: The Edge Agent evaluates every command against a local declarative allowlist. Even if a compromised Control Plane instructs the agent to read an unallowlisted table, the agent rejects the command locally (`REJECTED_POLICY`). |

---

## 4. Operational Hardening Guidelines

1. **Agent Process Privileges**: Run the Edge Agent binary as an unprivileged dedicated system user (`flowmesh`).
2. **Buffer File Security**: Ensure `/var/lib/flowmesh-agent` is mounted with `0700` permissions.
3. **Master KEK Rotation**: Store the 256-bit Master Key in a hardware security module (AWS KMS, GCP KMS, or HashiCorp Vault).
