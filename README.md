# FlowMesh

<p align="center">
  <img src="https://img.shields.io/badge/Status-Production--Ready-00C853?style=for-the-badge&logo=statuspage&logoColor=white" alt="Production Ready" />
  <img src="https://img.shields.io/badge/Architecture-3--Tier%20Hybrid%20Cloud-007ACC?style=for-the-badge&logo=diagramsdotnet&logoColor=white" alt="3-Tier Architecture" />
  <img src="https://img.shields.io/badge/SonarQube-Quality%20Gate%20Passed-4CAF50?style=for-the-badge&logo=sonarqube&logoColor=white" alt="SonarQube Quality Gate" />
  <img src="https://img.shields.io/badge/Coverage-88%25%20JaCoCo%20%7C%20Pytest-brightgreen?style=for-the-badge&logo=codecov&logoColor=white" alt="Coverage" />
  <img src="https://img.shields.io/badge/Java-17%20%7C%2021%20LTS-ED8B00?style=for-the-badge&logo=openjdk&logoColor=white" alt="Java LTS" />
  <img src="https://img.shields.io/badge/Methodology-Agile%20%2F%20Scrum-673AB7?style=for-the-badge&logo=jira&logoColor=white" alt="Agile Scrum" />
  <img src="https://img.shields.io/badge/License-Apache%202.0-blue?style=for-the-badge&logo=apache&logoColor=white" alt="Apache 2.0" />
</p>

<p align="center">
  <b> Language / 语言 / 言語 / भाषा / Langue / 언어 / Idioma:</b><br>
  <b>English</b> •
  <a href="./docs/i18n/README.ja.md">日本語</a> •
  <a href="./docs/i18n/README.zh.md">简体中文</a> •
  <a href="./docs/i18n/README.hi.md">हिन्दी</a> •
  <a href="./docs/i18n/README.fr.md">Français</a> •
  <a href="./docs/i18n/README.ko.md">한국어</a> •
  <a href="./docs/i18n/README.es.md">Español</a>
</p>

---

> **FlowMesh is a self-hosted, cloud-neutral, zero-lock-in enterprise integration and distributed workflow orchestration platform.**
> It unifies on-premise databases, legacy ERPs, internal microservices, and SaaS APIs into observable, fault-tolerant, replayable DAG workflows without puncturing corporate firewalls.

---

## Table of Contents

- [Executive Summary](#-executive-summary)
- [Why FlowMesh?](#-why-flowmesh)
- [Key Capabilities & Architectural Tenets](#-key-capabilities--architectural-tenets)
- [System Architecture](#-system-architecture)
- [Monorepo Directory Layout](#-monorepo-directory-layout)
- [Enterprise Java Backend & Concurrency](#-enterprise-java-backend--concurrency)
  - [Spring Boot 3 Enterprise Worker](#spring-boot-3-enterprise-worker)
  - [SLF4J & Logback Production Logging](#slf4j--logback-production-logging)
  - [Advanced Java Concurrency](#advanced-java-concurrency)
  - [JVM Memory Management & GC Tuning](#jvm-memory-management--gc-tuning)
- [Code Quality & SonarQube Quality Gates](#-code-quality--sonarqube-quality-gates)
- [Agile Engineering & Scrum Delivery Framework](#-agile-engineering--scrum-delivery-framework)
- [Quickstart Guide](#-quickstart-guide)
  - [Prerequisites](#prerequisites)
  - [Option A: Production Docker Compose Stack (Recommended)](#option-a-production-docker-compose-stack-recommended)
  - [Option B: Local Bare-Metal Development](#option-b-local-bare-metal-development)
  - [Option C: Kubernetes & Helm Deployment](#option-c-kubernetes--helm-deployment)
  - [Option D: Hardened Edge Agent Deployment (Linux systemd)](#option-d-hardened-edge-agent-deployment-linux-systemd)
- [Core Functional Modules](#-core-functional-modules)
  - [1. Visual & Code-Native Workflow Engine](#1-visual--code-native-workflow-engine)
  - [2. Secure Edge Agent (Outbound-Only mTLS)](#2-secure-edge-agent-outbound-only-mtls)
  - [3. Enterprise Security & Envelope Encryption](#3-enterprise-security--envelope-encryption)
  - [4. High-Performance StateStore & Distributed Locks](#4-high-performance-statestore--distributed-locks)
  - [5. Schema Discovery & Drift Detection](#5-schema-discovery--drift-detection)
  - [6. Policy-as-Code Engine](#6-policy-as-code-engine)
  - [7. Read-Only AI Incident Reasoning](#7-read-only-ai-incident-reasoning)
  - [8. Enterprise Systems Administration & Remote Fleet (ServiceNow, Active Directory, PowerShell, Paramiko)](#8-enterprise-systems-administration--remote-fleet)
  - [9. Distributed Cron Scheduling & Vectorized Data Analytics (PyYAML, Requests, Pandas)](#9-distributed-cron-scheduling--vectorized-data-analytics)
  - [10. Enterprise Cloud Orchestration & AI-Assisted Scripting (Ansible, Azure Automation, Power Platform, AI Guardrails)](#10-enterprise-cloud-orchestration--ai-assisted-scripting)
- [Distributed Observability & Telemetry](#-distributed-observability--telemetry)
- [API Gateway Reference](#-api-gateway-reference)
- [Architecture Decision Records (ADRs)](#-architecture-decision-records-adrs)
- [Verification & Automated Test Suite](#-verification--automated-test-suite)
- [Security & Compliance](#-security--compliance)
- [Contributing & License](#-contributing--license)

---

## Executive Summary

Modern enterprise infrastructure is deeply fragmented across legacy ERPs (SAP, Oracle), modern cloud data warehouses, relational stores (PostgreSQL, MySQL), message brokers, and third-party SaaS vendors. Traditional integration solutions present severe compromises:
1. **Public SaaS iPaaS** (Zapier, Workato, MuleSoft Cloud) requires shipping sensitive corporate data and database credentials off-premises, violating strict data sovereignty regulations (GDPR, HIPAA, SOC 2).
2. **Heavy Legacy Middleware** imposes million-dollar licensing models, brittle vendor lock-in, and fragile operations.
3. **Homegrown Cron/Bespoke Scripts** lack distributed tracing, schema evolution governance, transactional state recovery, and granular multi-tenant isolation.

**FlowMesh resolves this trilemma.** It delivers an open, modern, high-throughput integration backbone built on Python (FastAPI), Go, Next.js 15, NATS JetStream, and PostgreSQL/Redis, with zero cloud runtime dependencies.

---

## Why FlowMesh?

| Capability | FlowMesh | Traditional Cloud iPaaS | Legacy Enterprise Service Bus | Custom In-House Glue Code |
| :--- | :---: | :---: | :---: | :---: |
| **Data Sovereignty** | **100% Self-Hosted** | Cloud Multi-Tenant | On-Premise | Self-Hosted |
| **Firewall Inbound Ports** | **Zero (Outbound mTLS)** | Requires Open Ports / Bastions | Complex VPNs | Varied |
| **Execution Security** | **No Arbitrary RCE (Signed)** | Remote Code Execution | Heavy JVM plugins | Unaudited Scripts |
| **State Engine** | **Redis / RediForge / Memory** | Proprietary Blackbox | Relational DB bottleneck | Ad-hoc / None |
| **Observability** | **W3C OpenTelemetry Native** | Vendor Portal Only | Complex JMX tooling | Custom Print Logs |
| **Licensing Cost** | **Zero (Apache 2.0)** | $50k - $250k / year | High Multi-Year Contracts | High Maintenance Dev Cost |

---

## Key Capabilities & Architectural Tenets

- **Zero-Inbound Attack Surface ([ADR-0001](docs/adr/ADR-0001-agent-outbound-only.md))**: FlowMesh Edge Agents poll the control plane over outbound-only mTLS/WebSocket tunnels. Customer firewalls remain fully sealed with zero listening ports.
- **Strictly Signed Structural Actions ([ADR-0002](docs/adr/ADR-0002-no-remote-code-execution.md))**: Eliminates Remote Code Execution (RCE). All tasks execute declarative, schema-validated connector invocations verified by local Ed25519 signatures and allowlists.
- **Pluggable StateStore Abstraction ([ADR-0003](docs/adr/ADR-0003-statestore-abstraction.md))**: Interchangeable backends for state management, atomic distributed leases, and circuit breakers supporting Redis, RediForge, and in-memory caches.
- **Immutable Workflow Versioning ([ADR-0004](docs/adr/ADR-0004-immutable-workflow-versions.md))**: Deploys create immutable $N+1$ version snapshots. Running executions finish on their pinned version; rollbacks instantly repoint the active pointer to $N-1$ without downtime.
- **Envelope-Encrypted Credentials**: Master Key Encryption Keys (KEK) dynamically decrypt tenant Data Encryption Keys (DEK) via AES-256-GCM. Secret values are never stored in plain text or emitted to logs.
- **Multi-Tenant Row-Level Isolation**: The `TenantScopedRepository` architectural pattern enforces mandatory tenant scoping across all database operations, preventing cross-tenant data leakage.
- **High-Resilience Message Pipeline**: NATS JetStream provides persistent at-least-once message streaming, message deduplication, exponential backoff retries with full jitter, and Dead Letter Queues (DLQ).
- **Automated Schema Drift Detection**: Detects baseline schema divergence across enterprise databases and classifies changes into non-breaking `WARNING` or breaking `CRITICAL` alerts.

---

## System Architecture

FlowMesh cleanly decouples the **Control Plane**, **Data Plane**, and **Customer Edge Execution Plane**:

```text
                                  FLOWMESH ARCHITECTURE
                                            │
                       ┌────────────────────┴────────────────────┐
                       ▼                                         ▼
            CONTROL PLANE (PORT 8000)                 DATA PLANE ENGINE
              FastAPI / Python 3.12+                  Workflow State Machine
          ├── 17 Domain Routers                   ├── Topological DAG Resolver
          ├── RBAC & Auth Guard                   ├── Step Dispatcher & Retries
          └── TenantScopedRepository              └── Circuit Breaker & DLQ
                       │                                         │
                       ├────────────────────┬────────────────────┤
                       ▼                    ▼                    ▼
                NATS JetStream        PostgreSQL 16         Redis / RediForge
               (Event Bus & DLQ)    (System of Record)    (StateStore & Locks)
                       │                    │                    │
                       └────────────────────┼────────────────────┘
                                            │
                                   mTLS / Outbound Pull
                                     (Zero Inbound)
                                            │
                       ┌────────────────────▼────────────────────┐
                       │        CUSTOMER PRIVATE NETWORK         │
                       │                                         │
                       │          FLOWMESH EDGE AGENT            │
                       │         (Go 1.23 Static Daemon)         │
                       │  ├── Policy Engine (Deny-by-Default)    │
                       │  ├── Local SQLite Spool Buffer          │
                       │  ├── Cryptographic Signature Verifier   │
                       │  └── Sandboxed Connector Executions     │
                       │                                         │
                       │  ┌────────────┬───────────┬───────────┐ │
                       │  ▼            ▼           ▼           │ │
                       │ Postgres   REST APIs   Stripe/SAP     │ │
                       │  ▼            ▼           ▼           │ │
                       │ ServiceNow ActiveDir   Win/PowerShell │ │
                       │  ▼            ▼           ▼           │ │
                       │ SSH/SFTP   CronJobs    Pandas ETL     │ │
                       │  └────────────┴───────────┴───────────┘ │
                       └─────────────────────────────────────────┘
```

For comprehensive technical specifications, refer to [ARCHITECTURE.md](./ARCHITECTURE.md).

---

## Monorepo Directory Layout

```text
flowmesh/
├── apps/
│   ├── web/                    # Next.js 15 App Router Enterprise Web Console
│   ├── api/                    # FastAPI Control & Data Plane Gateway
│   └── agent/                  # FlowMesh Edge Agent (Go Static Daemon)
├── services/
│   ├── enterprise-worker/      # Spring Boot 3 Java Enterprise Integration Worker
│   ├── dotnet-worker/          # ASP.NET Core 8.0 WebAPI Worker & Batch Service
│   ├── workflow-engine/        # Resumable State-Machine, Cron Scheduler & Validation Engine
│   ├── event-router/           # Event Ingress & Bus Routing Engine
│   └── incident-manager/       # Automated Failure Correlation & DLQ Replay
├── packages/
│   ├── auth/                   # RBAC, Ed25519 Signing & Envelope Encryption
│   ├── connector-sdk/          # Unified Protocols, PowerShellRunner & FlowMeshHttpClient (Requests)
│   ├── data-transform/         # High-Performance DataFrame ETL & Polars / Pandas Engine
│   ├── search-engine/          # BM25 Tokenizer, Semantic Ranking & Typos
│   ├── state-store/            # Pluggable StateStore (Redis, RediForge, Memory)
│   └── workflow-schema/        # Workflow DAG JSON Schemas, PyYAML Parser & Drift Detectors
├── connectors/
│   ├── active_directory/       # Active Directory (AD DS) Identity, Group & Audit Connector
│   ├── airflow/                # Apache Airflow Pipeline Trigger Connector
│   ├── datalake/               # S3 / Parquet / Delta Data Lake Connector
│   ├── ibmmq/                  # IBM MQ Enterprise Messaging Connector
│   ├── mongodb/                # MongoDB NoSQL Document Store Connector
│   ├── mssql/                  # Microsoft SQL Server Enterprise Connector
│   ├── mysql/                  # MySQL Relational Database Connector
│   ├── oracle/                 # Oracle Enterprise Database Connector
│   ├── postgres/               # PostgreSQL Query & Introspection Connector
│   ├── rest/                   # HTTP/HTTPS REST Client Connector
│   ├── servicenow/             # ServiceNow Enterprise ITSM (Table API / CMDB) Connector
│   ├── ssh/                    # Paramiko SSH Remote Execution & SFTP Fleet Connector
│   ├── stripe/                 # Stripe Payments & Invoicing Connector
│   └── windows_admin/          # Windows Server Administration & PowerShell Connector
├── scripts/
│   ├── seed_demo.py            # Complete Demo Tenant, DAG & Agent Provisioner
│   ├── demo_e2e_showcase.py    # Master 90s Reviewer Walkthrough Demonstration
│   ├── start_backend.py        # Backend FastAPI Gateway Launcher
│   ├── flowmesh_doctor.py      # Multi-Language Preflight Diagnostic Tool
│   ├── run_sonar_scan.ps1      # PowerShell SonarQube Scanner Automation
│   └── run_sonar_scan.sh       # Bash SonarQube Scanner Automation
├── infra/
│   ├── ansible/                # Configuration Management & Agent Deployment
│   ├── docker/                 # Multi-Stage Dockerfiles & Compose Profiles
│   ├── grafana/                # Provisioned Dashboards & OpenTelemetry
│   ├── helm/                   # Production Kubernetes Helm Chart
│   ├── kubernetes/             # Production K8s Manifests (Deployments, HPA)
│   ├── openshift/              # Red Hat OpenShift Enterprise Manifests
│   ├── prometheus/             # Scrape Configurations & Alerting Rules
│   ├── sonarqube/              # Local SonarQube Quality Gate Compose Stack
│   ├── systemd/                # Hardened Edge Agent systemd Unit
│   └── terraform/              # Cloud-Neutral Infrastructure Modules
├── docs/
│   ├── guides/                 # Enterprise Architecture & Operations Runbooks
│   ├── adr/                    # Architecture Decision Records (ADR-0001 to ADR-0004)
│   ├── security/               # STRIDE Threat Model & Cryptographic Key Specs
│   ├── i18n/                   # Global Language Translations (JA, ZH, HI, FR, KO, ES)
│   └── README.md               # Master Technical Documentation Index
└── tests/
    ├── unit/                   # Fast Isolated Unit Tests (176+ Tests across 8 Enterprise Suites)
    ├── integration/            # Multi-Tenant & End-to-End API Audits (20 Tests)
    ├── e2e/                    # Selenium UI & Orchestration Verification
    ├── bdd/                    # Behavior-Driven Gherkin Acceptance Suites
    ├── chaos/                  # Fault Injection & Circuit Breaker Contention
    └── conftest.py             # Pytest Root Configuration & Fixtures
```

---

## Enterprise Java Backend & Concurrency

The **FlowMesh Enterprise Worker** (`services/enterprise-worker`) is a high-throughput, polyglot integration service engineered on **Spring Boot 3.3** and **Java 17/21 LTS**. It processes mission-critical financial transactions, coordinates atomic multi-system ledger reconciliations, and connects enterprise ERPs (SAP, Oracle) with modern event streams.

### Key Java Capabilities & Design Patterns

1. **SLF4J & Logback Enterprise Logging**:
   - **Structured JSON Logging**: Non-blocking asynchronous logging via `AsyncAppender` and `LogstashEncoder` outputting standard OpenTelemetry fields (`@timestamp`, `service.name`, `traceId`, `tenantId`).
   - **MDC Distributed Tracing**: [`MdcLoggingFilter.java`](services/enterprise-worker/src/main/java/io/flowmesh/enterprise/logging/MdcLoggingFilter.java) captures incoming `X-Trace-ID` and `X-Tenant-ID` headers, propagates correlation IDs, and **guarantees `MDC.clear()` in a `finally` block** to eliminate ThreadLocal memory leaks in worker pools.
   - **Immutable Audit Trails**: [`AuditLoggingService.java`](services/enterprise-worker/src/main/java/io/flowmesh/enterprise/logging/AuditLoggingService.java) logs tamper-evident financial and security audit records compliant with SOC 2 Type II and ISO 27001.
   - **AOP Performance Profiling**: `@LogExecutionTime` annotation and [`LoggingAspect.java`](services/enterprise-worker/src/main/java/io/flowmesh/enterprise/logging/LoggingAspect.java) track latency with nanosecond precision and alert on SLA breaches (>500ms).

2. **Advanced Java Concurrency in Distributed Systems**:
   - **Scatter-Gather Parallel Reconciliation**: [`ConcurrentLedgerReconciliationService.java`](services/enterprise-worker/src/main/java/io/flowmesh/enterprise/concurrency/ConcurrentLedgerReconciliationService.java) fans out parallel verification RPCs across distributed ledgers using `CompletableFuture.supplyAsync()`, non-blocking timeouts (`.orTimeout(1500, TimeUnit.MILLISECONDS)`), fallback recovery, and `CompletableFuture.allOf()` fan-in.
   - **Bounded ThreadPool with Backpressure**: [`ThreadPoolConfig.java`](services/enterprise-worker/src/main/java/io/flowmesh/enterprise/concurrency/ThreadPoolConfig.java) configures bounded queue executors with `ThreadPoolExecutor.CallerRunsPolicy`, naturally throttling ingress under load without dropping transactions.
   - **Lock-Free Concurrency & CAS**: [`LockFreeTokenBucketRateLimiter.java`](services/enterprise-worker/src/main/java/io/flowmesh/enterprise/concurrency/LockFreeTokenBucketRateLimiter.java) uses hardware atomic `Compare-And-Swap` (CAS via `AtomicLong`) to eliminate mutex locks and thread parking overhead.
   - **Partition-Striped Locking**: [`TenantConcurrencyStripingManager.java`](services/enterprise-worker/src/main/java/io/flowmesh/enterprise/concurrency/TenantConcurrencyStripingManager.java) partitions concurrency into power-of-two stripes, serializing transactions on the identical tenant to prevent double-spending while running different tenants in full parallel multi-core execution.
   - **Java 21 Project Loom Ready**: Dynamic detection and support for Virtual Threads (`Thread.ofVirtual().factory()`).

3. **JVM Memory Management & GC Tuning**:
   - **Real-Time JVM Telemetry**: [`JvmDiagnosticsController.java`](services/enterprise-worker/src/main/java/io/flowmesh/enterprise/diagnostics/JvmDiagnosticsController.java) exposes live metrics for Heap (Eden, Survivor, Old Gen), Non-Heap (Metaspace, CodeCache), Garbage Collector pause frequencies, and thread contention states.
   - **Production GC Tuning Profiles**: [`jvm.options`](services/enterprise-worker/jvm.options) specifies tuned parameters for **G1GC** (predictable <200ms latency, region-based reclamation) and **Generational ZGC** (sub-millisecond pause times for ultra-low latency SLAs).
   - **Crash Diagnostics & OOM Safety**: Configured with `-XX:+HeapDumpOnOutOfMemoryError` and `-XX:+ExitOnOutOfMemoryError` for deterministic post-mortem diagnosis.
   - **Deep Technical Guide**: See [`docs/guides/JAVA_ENTERPRISE_SYSTEMS.md`](docs/guides/JAVA_ENTERPRISE_SYSTEMS.md) for an exhaustive architectural reference on JVM memory regions, GC algorithms, memory leak prevention, and interview questions.

---

## Code Quality & SonarQube Quality Gates

FlowMesh strictly enforces a **"Clean as You Code"** policy across Python, Java, TypeScript, and Go using **SonarQube Enterprise**:

- **Quality Gate Standards**:
  - **Code Coverage**: $\ge 80\%$ on new code (enforced via JaCoCo for Java and Pytest-cov for Python).
  - **Vulnerabilities & Bugs**: **0 Blocker**, **0 Critical** issues.
  - **Security Hotspots**: 100% reviewed across encryption, deserialization, and authentication gates.
  - **Code Duplication**: $< 3.0\%$ duplication density.
- **Unified Multi-Language Configuration**: Centralized in [`sonar-project.properties`](sonar-project.properties).
- **Automated CI/CD Workflows**:
  - GitHub Actions: [`.github/workflows/sonar.yml`](.github/workflows/sonar.yml) compiles Java, generates JaCoCo XML, runs Pytest/LCOV, and enforces quality gate timeouts.
  - Jenkins Pipeline: [`Jenkinsfile`](Jenkinsfile) stages SonarQube analysis with `waitForQualityGate abortPipeline: true`.
- **Local Scanner & Infrastructure**:
  - One-command local SonarQube stack: `docker compose -f infra/sonarqube/docker-compose.sonar.yml up -d`
  - Automated scanner scripts: [`./scripts/run_sonar_scan.ps1`](scripts/run_sonar_scan.ps1) (PowerShell) and [`./scripts/run_sonar_scan.sh`](scripts/run_sonar_scan.sh) (Bash).
  - Documentation: Detailed runbook in [`docs/guides/SONARQUBE_QUALITY_GATES.md`](docs/guides/SONARQUBE_QUALITY_GATES.md).

---

## Agile Engineering & Scrum Delivery Framework

FlowMesh engineering squads operate on a structured **2-week sprint cycle** implementing mature Scrum practices:

- **Agile Issue Templates**:
  - [**User Story Template**](.github/ISSUE_TEMPLATE/01_user_story.md): Formatted with Persona ("As a... I want... So that..."), BDD Acceptance Criteria (Given/When/Then), Fibonacci Story Points, and Definition of Ready (DoR) gate.
  - [**Defect Report Template**](.github/ISSUE_TEMPLATE/02_bug_report.md): Structured triage with severity matrix (P1–P4), reproduction steps, diagnostic telemetry, and mandatory regression tests.
  - [**Technical Spike Template**](.github/ISSUE_TEMPLATE/03_technical_spike.md): Timeboxed architectural enablers producing Architecture Decision Records (ADRs).
- **Pull Request Template & Definition of Done (DoD)**:
  - [`.github/PULL_REQUEST_TEMPLATE.md`](.github/PULL_REQUEST_TEMPLATE.md) enforces an automated and peer-reviewed Definition of Done gate prior to merge (coverage $\ge 80\%$, 0 SonarQube blocker issues, thread-safety review, and `MDC.clear()` memory verification).
- **Delivery Framework Guide**: See [`docs/guides/AGILE_DEVELOPMENT_LIFECYCLE.md`](docs/guides/AGILE_DEVELOPMENT_LIFECYCLE.md) for sprint ceremony schedules, Planning Poker sizing rubrics, trunk-based branching, and velocity tracking.

---

## Quickstart Guide

### Prerequisites

| Component | Minimum Version | Notes |
| :--- | :--- | :--- |
| **Java** | `17 LTS` or `21 LTS` | Required for Enterprise Worker (`services/enterprise-worker`) |
| **Python** | `3.12+` | Managed via `uv` or `pip` |
| **Node.js** | `20 LTS+` | Package manager: `pnpm 9+` |
| **Go** | `1.23+` | Required for building the Edge Agent daemon |
| **Docker** | `24+` & Compose `v2+` | Recommended for containerized deployment |

---

### Option A: Production Docker Compose Stack (Recommended)

The quickest way to evaluate the entire FlowMesh ecosystem locally:

```bash
# 1. Clone the repository
git clone https://github.com/your-org/flowmesh.git
cd flowmesh

# 2. Initialize environment configuration
cp .env.example .env

# 3. Boot all services via Docker Compose
# Starts: PostgreSQL 16, NATS JetStream, Redis 7, API Gateway, Web Console, Prometheus, Grafana
docker compose up -d

# 4. Populate demo tenant, credentials, connectors, workflows, and edge agents
python seed_demo.py
```

#### Service URLs & Credentials

| Service | URL | Default Credentials | Description |
| :--- | :--- | :--- | :--- |
| **Web Console** | `http://localhost:3000` | Pre-authenticated | Next.js 15 Enterprise Management UI |
| **Workflows Studio** | `http://localhost:3000/workflows` | — | Visual DAG builder and executor |
| **Execution Runs** | `http://localhost:3000/runs` | — | Trace viewer & AI incident reasoning |
| **Connections & Drift** | `http://localhost:3000/connections` | — | Schema discovery & drift inspector |
| **Observability** | `http://localhost:3000/observability` | — | Metrics, logs, and telemetry dashboard |
| **API Swagger Docs** | `http://localhost:8000/docs` | `bearer demo-token` | FastAPI Interactive OpenAPI Explorer |
| **API Healthcheck** | `http://localhost:8000/health` | Public | System liveness probe |
| **Prometheus Metrics**| `http://localhost:8000/metrics` | Public | OpenMetrics scraping target |
| **Grafana** | `http://localhost:3001` | `admin` / `admin` | Production monitoring dashboards |

---

### Option B: Local Bare-Metal Development

```bash
# 1. Install Node & Python dependencies
pnpm install
pip install -e .

# 2. Run the complete automated test suite
python -m pytest tests/unit tests/chaos -v

# 3. Seed demo data into local SQLite database
python seed_demo.py

# 4. Launch API Control Plane (Terminal 1)
python apps/api/app/main.py

# 5. Launch Next.js Web Console (Terminal 2)
pnpm --filter web dev

# 6. Build and start Edge Agent Daemon (Terminal 3)
cd apps/agent
go test ./... -v
go build -o bin/flowmesh-agent ./cmd/flowmesh-agent
./bin/flowmesh-agent --id agent-local-01 --tenant tenant_acme --control-plane-url http://localhost:8000
```

---

### Option C: Kubernetes & Helm Deployment

Deploy FlowMesh into production Kubernetes clusters (EKS, GKE, AKS, or bare metal):

```bash
# 1. Add and inspect Helm values
helm inspect values ./infra/helm/flowmesh > my-values.yaml

# 2. Deploy to a dedicated namespace
helm install flowmesh ./infra/helm/flowmesh \
  --namespace flowmesh \
  --create-namespace \
  --values my-values.yaml

# 3. Alternatively, apply native Kubernetes manifests directly
kubectl apply -f infra/kubernetes/namespace.yaml
kubectl apply -f infra/kubernetes/configmap-and-secrets.yaml
kubectl apply -f infra/kubernetes/stateful-services.yaml
kubectl apply -f infra/kubernetes/api-and-web.yaml
```

---

### Option D: Hardened Edge Agent Deployment (Linux systemd)

For on-premise customer VPCs and DMZ environments:

```bash
# 1. Run the one-line unattended agent installer
curl -fsSL https://get.flowmesh.io/agent | sudo bash -s -- \
  --token <ENROLLMENT_TOKEN> \
  --control-plane https://flowmesh.your-org.com

# 2. Verify agent daemon status under systemd
sudo systemctl status flowmesh-agent
sudo journalctl -u flowmesh-agent -f
```

---

## Core Functional Modules

### 1. Visual & Code-Native Workflow Engine
Workflows in FlowMesh are represented as declarative, directed acyclic graph (DAG) schemas.
- **Topological Sorting**: Steps execute in deterministic order with dependency tracking.
- **Resumable Execution**: If an external system fails, the workflow pauses and maintains state in the `StateStore`. Once recovered, execution resumes from the exact failed step without re-executing previous steps.
- **Execution Branches & Merging**: Parallel conditional branching (`switch`, `parallel`, `join`).

### 2. Secure Edge Agent (Outbound-Only mTLS)
The Go-based Edge Agent executes within customer environments:
- **Zero Firewall Ingress**: Connects outbound to the Control Plane using HTTP/2 or WebSockets protected by mutual TLS (mTLS).
- **No Arbitrary Code Execution**: Only registered, declarative connectors (`postgres`, `rest`, `sftp`) can execute. Arbitrary shell commands or unsanitized scripts are strictly rejected by the local policy parser.
- **Local Spool Buffer**: Includes an embedded SQLite queue to buffer telemetry and results during intermittent WAN network disconnections.

### 3. Enterprise Security & Envelope Encryption
- **AES-256-GCM Envelope Encryption**: Connection credentials (API keys, database passwords) are encrypted under a unique Data Encryption Key (DEK) per tenant, which is encrypted under a Master Key Encryption Key (KEK).
- **Role-Based Access Control (RBAC)**: Built-in granular roles: `owner`, `operator`, `developer`, `viewer`.
- **Append-Only Audit Logs**: Every configuration mutation, workflow trigger, and secret access generates an immutable audit entry with cryptographic hash chaining.

### 4. High-Performance StateStore & Distributed Locks
- Implemented in `packages/state-store/` with unified drivers for **Redis**, **RediForge**, and **In-Memory** backends.
- Includes atomic distributed locking using redlock-compatible lease renewal Lua scripts.
- Implements atomic circuit breakers: `CLOSED` $\rightarrow$ `OPEN` $\rightarrow$ `HALF_OPEN`.

### 5. Schema Discovery & Drift Detection
- Connectors support schema introspection, generating canonical representations of relational tables, columns, constraints, and REST API contracts.
- **Drift Engine**: Compares active schema snapshots against verified baselines.
- Changes are categorized into non-breaking additions (`WARNING`) and breaking modifications or column deletions (`CRITICAL`).

### 6. Policy-as-Code Engine
Pre-flight safety rules evaluate workflows prior to deployment:
- Enforces mandatory timeouts and maximum retry ceilings.
- Validates the presence of Dead Letter Queues (DLQ) for all asynchronous triggers.
- Prevents raw, unmasked credential expressions in step inputs.
- Validates connector allowlists against environment boundaries (e.g., preventing staging agents from connecting to production databases).

### 7. Read-Only AI Incident Reasoning
FlowMesh includes a reliability-focused AI incident diagnostic assistant:
- **Non-Destructive & Read-Only**: Analyzes OpenTelemetry traces, failure logs, and circuit breaker metrics to identify root causes (e.g., pool exhaustion, gateway timeouts).
- **Human-in-the-Loop**: The assistant generates diagnosis reports and remediation plans but cannot perform write operations or deploy changes without explicit operator confirmation.

### 8. Enterprise Systems Administration & Remote Fleet
FlowMesh provides a hardened, unified interface for legacy on-premise infrastructure, Active Directory domain controllers, ITSM ticketing platforms, and remote server fleets:
- **ServiceNow ITSM & CMDB Connector (`connectors/servicenow`)**: Built on the ServiceNow Table API v2. Supports bidirectional Incident synchronization (`create_incident`, `get_incident`), Change Request approval governance (`create_change_request`), and automated Configuration Item (CI) queries against the ServiceNow CMDB.
- **Active Directory (AD DS) Identity & Compliance (`connectors/active_directory`)**: Native enterprise directory service supporting LDAP/LDAPS. Enforces employee lifecycle automation (`get_user`, `create_user`, `disable_user`, `unlock_user`), security group reconciliation (`add_user_to_group`), and scheduled stale account compliance auditing (`audit_stale_accounts`) for SOC 2 and ISO 27001 readiness.
- **Windows Server Administration & Native PowerShell (`connectors/windows_admin`, `packages/connector-sdk`)**: `PowerShellRunner` executes native Windows cmdlets and scripts in isolated processes with `-NoProfile -NonInteractive -ExecutionPolicy Bypass` and structured JSON serialization (`ConvertTo-Json`). The connector manages Windows Services (`Get-Service`, `Restart-Service`), Event Log auditing (`Get-WinEvent`), and hardware/system health telemetry via CIM/WMI.
- **Paramiko SSH / SFTP Fleet Management (`connectors/ssh`)**: Hardened SSHv2 and SFTP client built on `paramiko`. Supports authenticated remote execution (`exec_command`), strict host-key verification policy, and buffered file transfer operations (`sftp_upload`, `sftp_download`, `sftp_list`) for secure cross-datacenter settlement files.

### 9. Distributed Cron Scheduling & Vectorized Data Analytics
- **Scheduled Jobs & Cron Parser (`services/workflow-engine/flowmesh_engine/scheduler.py`)**: `CronScheduleParser` evaluates standard 5-part cron expressions (`minute hour dom month dow`), standard macros (`@hourly`, `@daily`, `@weekly`, `@monthly`), and custom interval timers. `WorkflowScheduler` maintains an in-memory or persisted job registry, coordinating with `StateStore` atomic distributed locks to prevent duplicate execution across horizontal worker nodes.
- **PyYAML Workflow DAG Serialization (`packages/workflow-schema/flowmesh_workflow/yaml_parser.py`)**: `YamlWorkflowParser` provides safe loading (`yaml.safe_load`), validation against strict Pydantic workflow schemas, syntax error diagnostics, and lossless round-trip serialization between YAML files and the Web DAG Studio.
- **Resilient Requests HTTP Client (`packages/connector-sdk/flowmesh_connector/http_client.py`)**: `FlowMeshHttpClient` encapsulates `requests.Session` with connection pooling (`pool_connections`, `pool_maxsize`), automatic retry adapters with exponential backoff and jitter (`urllib3.util.Retry`), and pluggable authentication providers (Bearer, Basic, API Key).
- **Pandas Vectorized Data Transformation Engine (`packages/data-transform/flowmesh_transform/dataframe_engine.py`)**: `DataFrameEngine` delivers high-performance in-memory ETL: vectorized transformations, statistical profiling (`statistical_summary`), interquartile range anomaly detection (`detect_outliers_iqr`), multi-source dataset merges (inner, left, right, outer joins), multidimensional aggregations (`aggregate_by_dimension`), and CSV export capabilities.

### 10. Enterprise Cloud Orchestration & AI-Assisted Scripting
FlowMesh expands its enterprise execution boundary into hybrid cloud, configuration management, and guardrailed generative automation:
- **Ansible Automation Controller (`connectors/ansible`)**: Native integration with Ansible control nodes, AWX, and Ansible Automation Platform (AAP). Supports declarative playbook dispatch (`run_playbook`), ad-hoc collection module execution (`execute_module`), inventory fact introspection (`get_facts`), and dry-run syntax verification (`check_syntax`) with structured `PLAY RECAP` telemetry.
- **Azure Automation & Hybrid Runbook Workers (`connectors/azure_automation`)**: Cloud and on-premise execution across Azure Automation Accounts via Microsoft Entra ID (Azure AD) OAuth 2.0 service principals. Manages PowerShell and Python runbooks (`start_runbook`, `get_job_status`, `get_job_output`, `list_runbooks`), hybrid worker group routing, and encrypted variable assets (`get_variable`).
- **Microsoft Power Platform & Dataverse (`connectors/power_platform`)**: Seamless bridge between FlowMesh distributed workflows and Microsoft Power Automate cloud/desktop RPA flows (`trigger_flow`, `get_flow_run`, `list_flows`) and Microsoft Dataverse (Common Data Service) OData v4 web API entities (`query_dataverse`, `create_dataverse_record`).
- **AI-Assisted Scripting Engine & Guardrails (`packages/ai-scripting`, `apps/api/app/routers/scripting.py`)**: Multi-language code synthesis and automated remediation for PowerShell, Bash, Python, SQL, and Ansible. Features strict static AST security guardrails that detect and reject high-risk operations (unbounded `DELETE`/`UPDATE`, destructive disk formatting, recursive root directory deletions, `eval`/`exec` injection), line-by-line code explanation, and automated error diagnostics.


---

## Distributed Observability & Telemetry

FlowMesh includes built-in observability conforming to the OpenTelemetry standard:

```text
HTTP Request ──[TraceContext W3C]──► API Gateway ──► NATS JetStream ──► Edge Agent ──► Target Connector
  (traceparent)                        (span)            (span)           (span)            (span)
```

- **OpenTelemetry Tracing**: Trace context (`traceparent`, `tracestate`) propagates across HTTP ingress, NATS message headers, and agent task dispatches.
- **Prometheus Metrics**: Exposes operational metrics at `/metrics`:
  - `flowmesh_workflow_executions_total`: Execution count partitioned by status and tenant.
  - `flowmesh_workflow_execution_duration_seconds`: Histogram of workflow execution latency.
  - `flowmesh_circuit_breaker_state`: Current state of connector circuit breakers.
  - `flowmesh_agent_heartbeat_timestamp`: Real-time liveness timestamp of all enrolled edge agents.
- **Grafana Dashboard**: Pre-configured dashboards located at `infra/grafana/dashboards/flowmesh-overview.json`.

---

## API Gateway Reference

The FastAPI Control Plane exposes 17 domain routers:

| Domain Router | Base Path | Key Capabilities |
| :--- | :--- | :--- |
| **Workflows** | `/api/v1/workflows` | Workflow CRUD, versioning, DAG validation, compile |
| **Runs** | `/api/v1/runs` | Trigger executions, step replay, cancel, state inspection |
| **Agents** | `/api/v1/agents` | Agent enrollment, heartbeat dispatch, command queue polling |
| **Connections** | `/api/v1/connections` | Credential storage, envelope encryption, connectivity test |
| **Drift** | `/api/v1/drift` | Schema introspection, baseline locking, drift diffing |
| **Policies** | `/api/v1/policies` | Policy-as-code governance, pre-flight safety validation |
| **Incidents** | `/api/v1/incidents` | Incident correlation, root cause analysis, AI diagnostics |
| **State** | `/api/v1/state` | StateStore inspection, distributed lock telemetry |
| **Audit** | `/api/v1/audit` | Append-only immutable tenant audit log queries |
| **Observability** | `/api/v1/observability` | Live trace search, span correlation, system health metrics |

Full OpenAPI specification is accessible at `http://localhost:8000/docs`.

---

## Architecture Decision Records (ADRs)

Key architectural decisions are formally documented in [`docs/adr/`](docs/adr/):

- **[ADR-0001: Outbound-Only Architecture for Edge Agent](docs/adr/ADR-0001-agent-outbound-only.md)** — Zero inbound open ports on customer firewalls.
- **[ADR-0002: Rejection of Arbitrary Remote Code Execution](docs/adr/ADR-0002-no-remote-code-execution.md)** — Elimination of RCE in favor of cryptographically signed structural actions.
- **[ADR-0003: Generic StateStore Abstraction for Redis & RediForge](docs/adr/ADR-0003-statestore-abstraction.md)** — Universal state storage interface with atomic distributed locking and circuit breakers.
- **[ADR-0004: Immutable Workflow Versioning and Pinning](docs/adr/ADR-0004-immutable-workflow-versions.md)** — Immutable $N+1$ deployment model with pinned execution and safe rollbacks.

---

## Verification & Automated Test Suite

FlowMesh includes a comprehensive test suite covering all operational planes:

```bash
# 1. Java Enterprise Worker (JUnit 5, Concurrency & JaCoCo Coverage)
cd services/enterprise-worker
mvn clean test jacoco:report -B

# 2. Python API, Connectors & StateStore Unit Tests (176+ Tests)
python -m pytest tests/unit -v --cov=apps --cov=connectors --cov-report=xml:coverage.xml

# 3. Enterprise Connectors, PowerShell, Paramiko, Scheduler & Pandas Tests (28 Tests)
python -m pytest tests/unit/test_servicenow_connector.py \
  tests/unit/test_active_directory_connector.py \
  tests/unit/test_windows_admin_and_powershell.py \
  tests/unit/test_paramiko_ssh_connector.py \
  tests/unit/test_scheduled_jobs.py \
  tests/unit/test_yaml_workflow_parser.py \
  tests/unit/test_requests_http_client.py \
  tests/unit/test_pandas_transformations.py -v

# 3. Chaos and Failure-Injection Tests
python -m pytest tests/chaos -v

# 4. Go Edge Agent Unit & Race-Condition Detection
cd apps/agent && go test -race -v ./...

# 5. Frontend Linting, Typechecking & Unit Test Coverage
pnpm --filter web lint
pnpm --filter web test:cov
pnpm --filter web build

# 6. Execute Unified Multi-Language SonarQube Scan
./scripts/run_sonar_scan.ps1   # PowerShell (Windows)
./scripts/run_sonar_scan.sh    # Bash (Linux/macOS)
```

---

## Security & Compliance

FlowMesh is designed to meet strict enterprise security standards:
- **SOC 2 Type II / ISO 27001 Ready**: Comprehensive audit trails, least-privilege RBAC, and zero persistent credential storage.
- **Data Privacy (GDPR / HIPAA)**: Customer payloads are processed inside the customer's perimeter via the Edge Agent. Raw data never leaves the client's private network.
- **Vulnerability Disclosure**: Please submit security vulnerability reports directly to `ashutosh4tech@gmail.com`. Do not file public GitHub issues for security vulnerabilities.

---

## Contributing & License

We welcome community contributions. Please review our contributing guidelines and pull request checklists before submitting code.

FlowMesh is open-source software licensed under the **Apache License, Version 2.0**.
See [LICENSE](LICENSE) for details.
