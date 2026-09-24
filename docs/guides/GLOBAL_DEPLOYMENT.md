# FlowMesh Global Deployment Guide

This guide details how to deploy **FlowMesh** globally with enterprise-grade resilience, multi-region redundancy, zero-trust edge execution, and sovereign data residency compliance (GDPR, HIPAA, SOC 2).

---

## 1. Global Architecture Overview

FlowMesh's dual-plane design makes global deployment exceptionally efficient and resilient compared to traditional monolithic workflow platforms:

```mermaid
graph TD
    subgraph "Global Edge Layer (Anycast & CDN)"
        Users[Global Enterprise Users] -->|Route 53 / Anycast GeoDNS| CDN[Cloudflare / AWS CloudFront]
        CDN -->|Static Assets & SSR| WebConsole[Next.js 15 Web Console]
        CDN -->|API Requests| GlobalLB[AWS Global Accelerator / Envoy Anycast]
    end

    subgraph "Primary Region (e.g. us-east-1)"
        GlobalLB --> API_US[FlowMesh FastAPI Control Plane]
        API_US --> DB_US[(Aurora PostgreSQL Primary)]
        API_US --> Redis_US[(Redis Cluster / Leases)]
        API_US --> NATS_US[(NATS JetStream Cluster)]
    end

    subgraph "Secondary / DR Region (e.g. eu-central-1)"
        GlobalLB -.->|Failover / Regional Ingress| API_EU[FlowMesh FastAPI Control Plane]
        API_EU --> DB_EU[(Aurora PostgreSQL Read/Promote Replica)]
        API_EU --> Redis_EU[(Redis Cluster)]
        API_EU --> NATS_EU[(NATS JetStream Cluster)]
        NATS_US <-->|NATS Supercluster Gateway| NATS_EU
    end

    subgraph "Distributed Data Plane: Edge Agents (50+ Locations)"
        Agent_US[On-Premise / Edge Agent: USA] -->|Outbound mTLS Only| GlobalLB
        Agent_EU[VPC Edge Agent: Frankfurt] -->|Outbound mTLS Only| GlobalLB
        Agent_APAC[Customer Datacenter: Tokyo] -->|Outbound mTLS Only| GlobalLB
        
        Agent_US --> LocalData1[(Local ERP / Postgres)]
        Agent_EU --> LocalData2[(Local SAP / SFTP)]
        Agent_APAC --> LocalData3[(Local Production Line / IoT)]
    end
```

### Key Architectural Invariants:
1. **Control Plane vs. Data Plane Separation**:
   - The **Control Plane** (Web UI, API, Orchestration DAGs, Metrics) can be hosted centrally or active-active across 2-3 cloud regions.
   - The **Data Plane** (Execution Agents) runs directly in the target environment (customer VPCs, on-prem datacenters, sovereign cloud regions).
2. **Zero Inbound Edge Ports**:
   - Edge agents communicate with the Control Plane via **outbound-only TLS 1.3 / mTLS** (port 443).
   - No NAT punching, public IPs, or firewall holes are ever required at customer edge sites.
3. **Sovereign Data Residency**:
   - Sensitive payloads (PII, financial transactions, HIPAA data) execute locally on the edge agent. Only execution state tokens and telemetry flow back to the Control Plane.

---

## 2. Deployment Topologies

Choose the topology that matches your scale, budget, and compliance requirements:

| Topology | Best For | Infrastructure Cost | RPO / RTO | Complexity |
|:---|:---|:---|:---|:---|
| **Topology A: Hybrid Cloud / Edge-First** *(Recommended)* | Enterprise SaaS & B2B Integration | Low ($100–$500/mo) | RPO < 1m, RTO < 5m | Low–Medium |
| **Topology B: Multi-Region Active-Active Cloud** | Tier-1 Mission Critical Global Enterprises | High ($1,500+/mo) | RPO ≈ 0s, RTO < 30s | High |
| **Topology C: Sovereign Single-Tenant / Private Mesh** | Regulated Defense, Banking, Healthcare | Zero to Low ($0–$150/mo) | Local snapshots | Low |

> [!TIP]
> **Zero-Cost ($0.00/mo) Cloud Deployment**: If you want to deploy FlowMesh with **$0 cloud cost**, see the complete [Zero-Cost Global Deployment Guide](file:///c:/Desktop/CODING%20_IS_LIFE/1%20ANTI%20GRAVITY/ENTERPISE%20WORKFLOW/docs/ZERO_COST_DEPLOYMENT.md) utilizing embedded SQLite, in-memory state stores, Cloudflare Tunnels, and Oracle Cloud Always Free Tier.

---

## 3. Step-by-Step Global Deployment Guide

### Phase 1: Build & Publish Multi-Arch Container Images

FlowMesh services support both `linux/amd64` (x86) and `linux/arm64` (AWS Graviton, Apple Silicon, edge appliances).

```bash
# 1. Login to your container registry (e.g. GitHub Container Registry or AWS ECR)
echo $CR_PAT | docker login ghcr.io -u YOUR_GITHUB_USERNAME --password-stdin

# 2. Build and push Control Plane API
docker buildx build \
  --platform linux/amd64,linux/arm64 \
  -f infra/docker/Dockerfile.api \
  -t ghcr.io/your-org/flowmesh-api:v0.1.0 \
  -t ghcr.io/your-org/flowmesh-api:latest \
  --push .

# 3. Build and push Next.js Web Console
docker buildx build \
  --platform linux/amd64,linux/arm64 \
  -f infra/docker/Dockerfile.web \
  -t ghcr.io/your-org/flowmesh-web:v0.1.0 \
  -t ghcr.io/your-org/flowmesh-web:latest \
  --push .

# 4. Build and push Go Edge Agent
docker buildx build \
  --platform linux/amd64,linux/arm64 \
  -f infra/docker/Dockerfile.agent \
  -t ghcr.io/your-org/flowmesh-agent:v0.1.0 \
  -t ghcr.io/your-org/flowmesh-agent:latest \
  --push .
```

---

### Phase 2: Database & State Store Infrastructure (Terraform)

Use the Terraform templates located in `infra/terraform/` to provision isolated VPCs, subnets, and PostgreSQL RDS instances.

```bash
cd infra/terraform

# Initialize Terraform AWS provider
terraform init

# Review execution plan
terraform plan -var="environment=production" -var="region=us-east-1"

# Apply infrastructure
terraform apply -var="environment=production" -var="region=us-east-1" -auto-approve
```

#### Multi-Region Database Replication:
To configure global PostgreSQL replication across regions (e.g., `us-east-1` primary to `eu-central-1` replica):
- **AWS Aurora Global Database**: Configure primary cluster in `us-east-1` and add a secondary cross-region replica cluster in `eu-central-1` (storage-level physical replication latency < 1 second).
- **Self-Hosted / Zero-Cost**: Utilize native PostgreSQL logical replication or Fly.io Postgres multi-region clusters.

#### Run Database Migrations:
Run Alembic migrations against the production database endpoint:
```bash
DATABASE_URL="postgresql+asyncpg://flowmesh_admin:SecurePass123!@flowmesh-production-db.c7x8y.us-east-1.rds.amazonaws.com:5432/flowmesh_prod" \
  alembic upgrade head
```

---

### Phase 3: Deploy Control Plane to Kubernetes (EKS / GKE / AKS)

FlowMesh provides pre-configured Kubernetes manifests in `infra/kubernetes/`:

1. **Create Namespace & Secrets**:
   ```bash
   kubectl apply -f infra/kubernetes/namespace.yaml
   
   # Apply production configuration & secrets
   kubectl apply -f infra/kubernetes/configmap-and-secrets.yaml
   ```

2. **Deploy Stateful Services (Redis & NATS JetStream)**:
   ```bash
   kubectl apply -f infra/kubernetes/stateful-services.yaml
   ```

3. **Deploy API & Web Deployments**:
   ```bash
   kubectl apply -f infra/kubernetes/api-and-web.yaml
   ```

4. **Verify Pod Status & Readiness**:
   ```bash
   kubectl get pods -n flowmesh
   # Output:
   # NAME                            READY   STATUS    RESTARTS   AGE
   # flowmesh-api-6b87d9f74-8k9pl   1/1     Running   0          45s
   # flowmesh-api-6b87d9f74-j2x7n   1/1     Running   0          45s
   # flowmesh-web-58f79cd46-p8z1a   1/1     Running   0          45s
   # redis-0                        1/1     Running   0          2m
   # nats-0                         1/1     Running   0          2m
   ```

---

### Phase 4: Global Ingress, Anycast CDN & DNS Routing

To ensure sub-50ms latency for global users and agents:

1. **Cloudflare Global Anycast (Recommended)**:
   - Point your apex domain (`api.flowmesh.io`) to your Kubernetes Ingress Controller or AWS ALB.
   - Enable Cloudflare Enterprise / Pro with **Argo Smart Routing** and **Tiered Caching**.
   - Configure SSL/TLS Mode: **Full (Strict)**.
   - Enforce Web Application Firewall (WAF) rules:
     - Rate limit on `/api/v1/auth/*` (10 requests per minute).
     - Global DDoS protection and TLS 1.3 minimum.

2. **AWS Global Accelerator Alternative**:
   - Provision an AWS Global Accelerator with two static Anycast IP addresses.
   - Route traffic through AWS’s private global fiber network directly to the regional ALBs in `us-east-1` and `eu-central-1`.

---

### Phase 5: Deploy Edge Agents Globally (Zero-Trust Data Plane)

Edge agents are lightweight single-binary Go daemons that can be installed on bare-metal servers, VMs, or edge appliances.

#### 1. Enroll Agent via CLI or Control Plane API
Generate an enrollment token for the remote agent:
```bash
curl -X POST https://api.flowmesh.io/api/v1/agents/enroll \
  -H "Authorization: Bearer $ADMIN_JWT" \
  -H "X-Tenant-ID: tenant_acme" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "edge-tokyo-onprem-01",
    "region": "ap-northeast-1",
    "tags": ["datacenter:tokyo", "zone:asia", "compliance:sovereign"]
  }'
```

#### 2. Run Edge Agent on Remote Site (Systemd / Linux Service)
Install the agent daemon on the remote machine:

```bash
# Download agent binary
curl -sSL https://github.com/your-org/flowmesh/releases/download/v0.1.0/flowmesh-agent-linux-amd64 -o /usr/local/bin/flowmesh-agent
chmod +x /usr/local/bin/flowmesh-agent

# Configure agent
mkdir -p /etc/flowmesh
cat <<EOF > /etc/flowmesh/config.yaml
agent_id: "edge-tokyo-onprem-01"
control_plane_url: "https://api.flowmesh.io"
tenant_id: "tenant_acme"
enrollment_token: "fm_tok_abc123456789"
log_level: "info"
buffer_dir: "/var/lib/flowmesh/spool"
max_buffer_mb: 500
heartbeat_interval_seconds: 15
EOF

# Install systemd service
cat <<EOF > /etc/systemd/system/flowmesh-agent.service
[Unit]
Description=FlowMesh Edge Execution Daemon
After=network.target

[Service]
ExecStart=/usr/local/bin/flowmesh-agent --config /etc/flowmesh/config.yaml
Restart=always
RestartSec=5
LimitNOFILE=65536
User=flowmesh
Group=flowmesh

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable --now flowmesh-agent
```

#### 3. Run Edge Agent via Docker Container
```bash
docker run -d \
  --name flowmesh-agent \
  --restart unless-stopped \
  -v /var/run/docker.sock:/var/run/docker.sock \
  -v /var/lib/flowmesh:/var/lib/flowmesh \
  -e CONTROL_PLANE_URL="https://api.flowmesh.io" \
  -e TENANT_ID="tenant_acme" \
  -e ENROLLMENT_TOKEN="fm_tok_abc123456789" \
  ghcr.io/your-org/flowmesh-agent:latest
```

---

## 4. Edge Resilience & Offline Store-and-Forward

When global network disruptions or WAN latency spikes occur:
1. **Local Policy Verification**: The Go agent evaluates local validation policies without waiting for a control plane roundtrip.
2. **SQLite Spool Buffer**: If the connection to `https://api.flowmesh.io` drops, the agent writes execution events and status transitions into its local encrypted SQLite buffer (`/var/lib/flowmesh/spool`).
3. **Exponential Backoff Replay**: Once internet connectivity restores, the agent replays buffered records in chronological order with zero data loss.

---

## 5. Global Health Monitoring & Alerts

| Health Endpoint | Description | Expected Status |
|:---|:---|:---:|
| `GET https://api.flowmesh.io/health` | Process liveness check | `200 OK` (`{"status": "healthy"}`) |
| `GET https://api.flowmesh.io/ready` | Deep database & Redis readiness | `200 OK` (`{"status": "ready", "checks": {...}}`) |
| `GET https://api.flowmesh.io/metrics` | Prometheus OpenMetrics exporter | `200 OK` (Standard scrape targets) |

### Prometheus Alerting Rules
Configure alert manager triggers for:
- `FlowMeshCircuitBreakerOpen`: Fired when an integration connector trips.
- `FlowMeshEdgeAgentHeartbeatMissing`: Fired when an edge agent fails to heartbeat for > 60 seconds.
- `FlowMeshDLQGrowthRateHigh`: Fired when dead letter queue size increases rapidly.

---

## 6. Disaster Recovery & Regional Failover Playbook

In the event of a catastrophic AWS/Cloud region failure:

1. **Automated GeoDNS Rerouting**:
   - Cloudflare or Route 53 health checks detect `us-east-1` failure and shift 100% of ingress to `eu-central-1`.
2. **Promote Standby Database**:
   - Run RDS promotion on the read replica:
     ```bash
     aws rds promote-read-replica --db-instance-identifier flowmesh-production-db-eu
     ```
3. **Update Kubernetes Configuration**:
   - Point secondary Kubernetes cluster connection string to promoted master.
4. **Agent Auto-Discovery**:
   - All edge agents globally automatically reconnect to the active endpoint through the Anycast DNS layer within 15 seconds.
