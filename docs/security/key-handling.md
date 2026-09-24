# FlowMesh Cryptographic Key Handling & Encryption Architecture

## 1. Envelope Encryption Architecture (Credentials at Rest)

FlowMesh employs a **two-tier envelope encryption model** for all sensitive credentials (database passwords, API tokens, private certificates, and client secrets):

```text
               MASTER KEY ENCRYPTION KEY (KEK)
                 (Stored in AWS KMS / GCP KMS / Vault)
                               │
                               ▼
               TENANT DATA ENCRYPTION KEY (DEK)
                 (AES-256-GCM, Unique Per Tenant)
                               │
                               ▼
                    ENCRYPTED CREDENTIAL
                 (Ciphertext stored in PostgreSQL)
```

### Key Hierarchy
1. **Key Encryption Key (KEK)**:
   - 256-bit AES master key supplied via environment variable or KMS (`ENCRYPTION_MASTER_KEY`).
   - Used exclusively to wrap and unwrap Tenant Data Encryption Keys (DEKs).
   - Never used directly to encrypt connection payloads.

2. **Data Encryption Key (DEK)**:
   - 256-bit cryptographically random key generated per tenant via `os.urandom(32)`.
   - Stored in wrapped format (`wrapped_dek`) in the database encrypted under the KEK using AES-256-GCM.
   - Decrypted only in-memory when resolving credentials for active connector execution.

3. **Connection Secret Ciphertext**:
   - Connection credentials (e.g. Postgres passwords, Bearer tokens) are encrypted with the tenant's DEK using AES-256-GCM with a unique 96-bit initialization vector (nonce) per encryption operation.
   - Associated Data (AAD) is bound to `tenant_id` and `connection_id`, guaranteeing that ciphertext cannot be transposed across tenants or connections.

### Write-Only API Guarantee
- Connection secrets can be submitted when creating or rotating a connection via `POST /api/v1/connections`.
- The API **never** returns connection secrets in GET responses. Secrets are referenced strictly by opaque token IDs.

---

## 2. Command Authentication & Integrity (Ed25519)

### Asymmetric Command Signing
To enforce [ADR-0002: Rejection of Arbitrary Remote Code Execution](file:///c:/Desktop/CODING%20_IS_LIFE/1%20ANTI%20GRAVITY/ENTERPISE%20WORKFLOW/docs/adr/ADR-0002-no-remote-code-execution.md):
- The central Control Plane possesses an Ed25519 private signing key.
- When dispatching a structural command to an Edge Agent, the Control Plane canonicalizes the payload (sorting keys lexicographically without extraneous whitespace) and computes an Ed25519 signature.
- The command envelope carries:
  ```json
  {
    "command": {
      "id": "cmd-88219",
      "type": "connector.execute",
      "connector": "postgres",
      "connection_id": "conn_pg_01",
      "operation": "query",
      "resource": "orders",
      "limit": 100,
      "payload": { "status": "PENDING" },
      "trace_id": "4bf92f3577b34da6a3ce929d0e0e4736",
      "span_id": "00f067aa0ba902b7"
    },
    "signature": "base64-ed25519-signature..."
  }
  ```
- The Edge Agent uses the Control Plane's pinned public key to verify the signature before parsing.
- Release builds of the Edge Agent have no bypass flags; commands with invalid signatures are rejected instantly.

---

## 3. Mutual TLS (mTLS) Agent Transport

- Communication between the Edge Agent and Control Plane takes place over WebSocket or HTTPS with mutual TLS.
- During enrollment, the Edge Agent generates an ephemeral CSR, verified by the Control Plane CA, which issues a short-lived client certificate (e.g. 90 days).
- Heartbeat loops automatically request certificate renewal when 30 days of certificate validity remain.
- If an agent is decommissioned, its certificate fingerprint is immediately placed on the tenant's revocation list, terminating transport-level handshakes.
