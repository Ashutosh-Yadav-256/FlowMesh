# FlowMesh Engineering Documentation Hub

Welcome to the FlowMesh technical documentation directory. This index categorizes all architecture specifications, operational runbooks, decision logs, and internationalization resources.

---

## System Architecture & Specifications
- **[System Architecture Document (SAD)](../ARCHITECTURE.md)** — Core C4 system topology, event-driven orchestration, FastAPI control plane, zero-trust edge agent, and hybrid connectivity patterns.
- **[Monorepo Architecture & Directory Structure](../README.md#monorepo-directory-layout)** — Complete folder-by-folder layout of apps, services, packages, connectors, infrastructure, and tests.

---

## Engineering Guides & Operational Runbooks
Located in [`docs/guides/`](./guides/):

| Guide | Description |
| :--- | :--- |
| **[JAVA_ENTERPRISE_SYSTEMS.md](./guides/JAVA_ENTERPRISE_SYSTEMS.md)** | Deep dive on JVM memory regions (Eden, Survivor, Old Gen, Metaspace), G1GC/ZGC tuning profiles, and thread concurrency. |
| **[SONARQUBE_QUALITY_GATES.md](./guides/SONARQUBE_QUALITY_GATES.md)** | Clean as You Code gates, multi-language `sonar-project.properties`, JaCoCo coverage, and CI/CD timeout handling. |
| **[AGILE_DEVELOPMENT_LIFECYCLE.md](./guides/AGILE_DEVELOPMENT_LIFECYCLE.md)** | Scrum 2-week sprint framework, Definition of Ready (DoR), Definition of Done (DoD), and Planning Poker sizing rubrics. |
| **[ENTERPRISE_DATABASE_GUIDE.md](./guides/ENTERPRISE_DATABASE_GUIDE.md)** | Production database connectors (PostgreSQL, Oracle, MSSQL, MySQL, MongoDB, DataLake) with pooling and isolation. |
| **[ENTERPRISE_TESTING_TAXONOMY.md](./guides/ENTERPRISE_TESTING_TAXONOMY.md)** | Test pyramid breakdown: isolated unit tests, multi-tenant integration tests, Selenium E2E flows, and chaos fault injection. |
| **[GLOBAL_DEPLOYMENT.md](./guides/GLOBAL_DEPLOYMENT.md)** | Multi-region deployment, Kubernetes, Helm, Cloudflare Tunnels, and enterprise hybrid cloud setups. |
| **[ZERO_COST_DEPLOYMENT.md](./guides/ZERO_COST_DEPLOYMENT.md)** | Guide to running a full FlowMesh installation at **$0.00/mo** cloud cost using SQLite, in-memory state, and free tiers. |
| **[API_VERSIONING.md](./guides/API_VERSIONING.md)** | Lifecycle policy for `/api/v1` routes, semver deprecation windows, sunset headers, and backwards compatibility. |
| **[AIRFLOW_INTEGRATION.md](./guides/AIRFLOW_INTEGRATION.md)** | Cross-system DAG orchestration and bidirectional event synchronization with Apache Airflow clusters. |

---

## Architecture Decision Records (ADRs)
Formal decision records located in [`docs/adr/`](./adr/):

- **[ADR-0001: Outbound-Only Architecture for Edge Agent](./adr/ADR-0001-agent-outbound-only.md)** — Zero inbound open ports on customer firewalls.
- **[ADR-0002: Rejection of Arbitrary Remote Code Execution](./adr/ADR-0002-no-remote-code-execution.md)** — Elimination of RCE in favor of cryptographically signed structural actions.
- **[ADR-0003: Generic StateStore Abstraction for Redis & RediForge](./adr/ADR-0003-statestore-abstraction.md)** — Universal state storage interface with atomic distributed locking and circuit breakers.
- **[ADR-0004: Immutable Workflow Versioning and Pinning](./adr/ADR-0004-immutable-workflow-versions.md)** — Immutable $N+1$ deployment model with pinned execution and safe rollbacks.

---

## Security Architecture
Located in [`docs/security/`](./security/):

- **[STRIDE Threat Model](./security/threat-model.md)** — Threat mitigation matrix covering Spoofing, Tampering, Repudiation, Information Disclosure, Denial of Service, and Elevation of Privilege.
- **[Cryptographic Key Handling](./security/key-handling.md)** — AES-256-GCM envelope encryption, tenant-isolated DEKs, Ed25519 signing keys, and zero-plaintext storage.

---

## Global Translations (i18n)
Full repository documentation localized for global distributed teams in [`docs/i18n/`](./i18n/):

- **日本語 (Japanese)**: [README.ja.md](./i18n/README.ja.md) • [ARCHITECTURE.ja.md](./i18n/ARCHITECTURE.ja.md)
- **简体中文 (Simplified Chinese)**: [README.zh.md](./i18n/README.zh.md) • [ARCHITECTURE.zh.md](./i18n/ARCHITECTURE.zh.md)
- **हिन्दी (Hindi)**: [README.hi.md](./i18n/README.hi.md) • [ARCHITECTURE.hi.md](./i18n/ARCHITECTURE.hi.md)
- **Français (French)**: [README.fr.md](./i18n/README.fr.md) • [ARCHITECTURE.fr.md](./i18n/ARCHITECTURE.fr.md)
- **한국어 (Korean)**: [README.ko.md](./i18n/README.ko.md) • [ARCHITECTURE.ko.md](./i18n/ARCHITECTURE.ko.md)
- **Español (Spanish)**: [README.es.md](./i18n/README.es.md) • [ARCHITECTURE.es.md](./i18n/ARCHITECTURE.es.md)
