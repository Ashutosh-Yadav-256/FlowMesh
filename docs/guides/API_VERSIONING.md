# FlowMesh API Versioning & Deprecation Policy

## 1. Architectural Principles

FlowMesh adheres to **URI Path Versioning** for major API evolutions (`/api/v1/...`) combined with backward-compatible additive field evolutions.

### Key Tenets
1. **URI Path Routing**: Every tenant-facing, edge-agent, and integration endpoint is anchored under `/api/v1/`.
2. **Backward-Compatible Field Evolution**:
   - New response attributes may be introduced at any time without breaking existing consumers.
   - Consumers MUST ignore unrecognized JSON properties.
   - Fields will NEVER be renamed or repurposed within the same API major version.
3. **Strict Validation on Ingress**:
   - Request bodies are strictly bounded by size (`MAX_REQUEST_BODY_BYTES`) and nesting depth (`MAX_JSON_NESTING_DEPTH`).
   - Query limits and offsets are bounded (`page_size` max 200).

---

## 2. Deprecation Lifecycle

When an endpoint or schema property is slated for retirement:

```
[ Active ] ──> [ Deprecated (≥ 6 Months) ] ──> [ Sunset / 410 Gone ]
```

### Deprecation Response Headers
In compliance with RFC 8594:
- `Deprecation: @<timestamp>` — The Unix timestamp when deprecation took effect.
- `Sunset: <HTTP-date>` — The exact date when the endpoint will cease operation.
- `Link: <uri>; rel="deprecation"` — Link to relevant migration documentation.

### Example Deprecation Header
```http
HTTP/1.1 200 OK
Deprecation: @1773993600
Sunset: Wed, 01 Oct 2026 00:00:00 GMT
Link: <https://flowmesh.io/docs/migrations/v2>; rel="deprecation"
```

---

## 3. Breaking vs. Non-Breaking Changes

| Change Type | Classification | Policy |
|:---|:---|:---|
| Adding an optional query parameter | Non-breaking | Permitted in `/v1/` |
| Adding a new response field | Non-breaking | Permitted in `/v1/` |
| Adding a new enum variant | Non-breaking | Permitted in `/v1/` |
| Removing a required request field | Non-breaking | Permitted in `/v1/` |
| Removing or renaming an endpoint | **Breaking** | Requires new version (`/v2/`) |
| Removing an existing response property | **Breaking** | Requires new version (`/v2/`) |
| Changing response data types | **Breaking** | Requires new version (`/v2/`) |
| Adding a mandatory request header | **Breaking** | Requires new version (`/v2/`) |

---

## 4. Multi-Tenant Request Correlation

All API requests support and correlate the following headers:
- `X-Tenant-ID`: Identifies tenant isolation partition (default: `tenant_acme`).
- `X-Request-ID`: Client or gateway distributed tracing correlation ID (UUIDv4).
- `X-RateLimit-Limit`: Maximum allowed requests in current window.
- `X-RateLimit-Remaining`: Remaining allowance before receiving HTTP 429.
- `X-RateLimit-Reset`: Unix timestamp when the rate limit window resets.
