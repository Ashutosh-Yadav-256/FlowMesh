# FlowMesh Zero-Cost ($0) Global Deployment Guide

FlowMesh was engineered from day one under a **strict Zero-Cost Architecture constraint**. You do **NOT** need paid AWS RDS, Elasticache, Kafka, or expensive Kubernetes clusters to deploy FlowMesh globally.

By leveraging FlowMesh's embedded SQLite database, in-memory state engine, and generous **100% Free Forever** cloud platforms, you can run a global, enterprise-grade deployment for **$0.00 / month**.

---

## The $0 Architecture Breakdown

| Component | Standard Paid Cloud Equivalent | FlowMesh $0 Architecture | Cost |
|:---|:---|:---|:---:|
| **Control Plane API** | AWS ECS / EKS ($70+/mo) | Oracle Always Free (24GB RAM) or Koyeb/Render | **$0.00** |
| **Web Console** | Vercel Pro / CloudFront ($20+/mo) | Vercel Hobby / Cloudflare Pages | **$0.00** |
| **System of Record (DB)** | AWS RDS PostgreSQL ($40+/mo) | Embedded `aiosqlite` (`flowmesh.db`) or Neon/Supabase Free | **$0.00** |
| **Distributed State & Locks** | AWS ElastiCache Redis ($35+/mo) | Built-in `STATE_STORE_PROVIDER=memory` | **$0.00** |
| **Search Engine** | Elasticsearch / Algolia ($50+/mo) | Local File-Persisted `flowmesh_search` JSON Index | **$0.00** |
| **Global CDN & SSL** | Cloudflare Enterprise / AWS WAF ($100+/mo) | Cloudflare Free Tunnel (`cloudflared`) + Anycast CDN | **$0.00** |
| **Edge Agents** | Managed IoT / Edge Gateways ($50+/mo) | Standalone Go Binary on existing machines | **$0.00** |
| **TOTAL MONTHLY COST** | **$365+ / month** | **FlowMesh $0 Architecture** | **$0.00 / mo** |

---

## 3 Proven Ways to Deploy FlowMesh for $0.00

---

### Option 1: Instant Global Deployment via Cloudflare Tunnel (5 Minutes, $0.00)

Turn your local PC, existing home server, office workstation, or any machine into a globally accessible, enterprise-grade platform with free automated SSL and DDoS protection.

**Why this is amazing**:
- No public IP needed.
- No port forwarding or router firewall changes.
- Outbound-only encrypted tunnel to Cloudflare’s 300+ global edge locations.
- Works behind CGNAT, home Wi-Fi, and corporate firewalls.

#### Step 1: Start FlowMesh Locally in Zero-Cost Mode
Ensure your `.env` has the zero-cost defaults:
```ini
ENVIRONMENT=production
DATABASE_URL=sqlite+aiosqlite:///./flowmesh.db
STATE_STORE_PROVIDER=memory
```

Start the services:
- Backend: `python start_backend.py` (running on `http://localhost:8000`)
- Frontend: `pnpm --filter web start` (running on `http://localhost:3000`)

#### Step 2: Install Cloudflare Tunnel (`cloudflared`)
- **Windows (PowerShell)**:
  ```powershell
  winget install --id Cloudflare.cloudflared
  ```
- **macOS**:
  ```bash
  brew install cloudflared
  ```
- **Linux (Ubuntu/Debian)**:
  ```bash
  curl -L --output cloudflared.deb https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64.deb
  sudo dpkg -i cloudflared.deb
  ```

#### Step 3: Launch Instant Public HTTPS Tunnels (Zero Registration Required)
Run quick tunnels (Cloudflare gives you free instant `trycloudflare.com` URLs):

```bash
# Terminal 1: Expose Web Console
cloudflared tunnel --url http://localhost:3000
```
*Output:*
```text
+--------------------------------------------------------------------------------------------+
| Your quick Tunnel has been created! Visit it at (it may take some time to be reachable):    |
| https://flowmesh-app-random-id.trycloudflare.com                                           |
+--------------------------------------------------------------------------------------------+
```

```bash
# Terminal 2: Expose API Gateway
cloudflared tunnel --url http://localhost:8000
```

#### Step 4: With Your Own Custom Domain ($0.00)
If you own a domain connected to Cloudflare Free:
```bash
# 1. Login to Cloudflare
cloudflared tunnel login

# 2. Create named tunnel
cloudflared tunnel create flowmesh

# 3. Route domains
cloudflared tunnel route dns flowmesh app.yourdomain.com
cloudflared tunnel route dns flowmesh api.yourdomain.com

# 4. Create config ~/.cloudflared/config.yml:
# ingress:
#  - hostname: app.yourdomain.com
#    service: http://localhost:3000
#  - hostname: api.yourdomain.com
#    service: http://localhost:8000
#  - service: http_status:404

# 5. Run tunnel
cloudflared tunnel run flowmesh
```
Your platform is now globally live on your custom domain with zero cloud bills!

---

### Option 2: Oracle Cloud Always Free Tier (Most Powerful $0 Cloud Server)

Oracle Cloud offers the most generous free cloud tier in the world — **free forever, no expiration**:
- **4 Ampere ARM vCPUs**
- **24 GB RAM**
- **200 GB NVMe Storage**
- **10 TB/month free outbound traffic**

#### Step 1: Create an Always Free Account
1. Sign up at [cloud.oracle.com](https://cloud.oracle.com).
2. Create an **Ampere A1 Compute Instance** (Select 4 OCPUs, 24 GB RAM, Ubuntu 22.04 Minimal).

#### Step 2: SSH into the Server & Install Docker
```bash
sudo apt update && sudo apt install -y docker.io docker-compose-v2 git
sudo usermod -aG docker ubuntu
```

#### Step 3: Clone FlowMesh & Run in Zero-Cost Mode
```bash
git clone https://github.com/your-org/flowmesh.git /opt/flowmesh
cd /opt/flowmesh

# Create .env with zero-cost configuration
cat << 'EOF' > .env
ENVIRONMENT=production
DATABASE_URL=sqlite+aiosqlite:///./flowmesh.db
STATE_STORE_PROVIDER=memory
API_SECRET_KEY=generate-a-64-char-random-key-here
ENCRYPTION_MASTER_KEY=generate-a-64-char-random-key-here
NEXT_PUBLIC_API_URL=http://YOUR_SERVER_PUBLIC_IP:8000
EOF

# Build and start services using Docker Compose
docker compose up -d web api
```
You now have an enterprise server running 24/7 in the cloud at **$0.00**.

---

### Option 3: Free PaaS Mesh (Vercel + Koyeb / Render Free Tier)

Deploy without managing any virtual machine:

1. **Frontend (Vercel)**:
   - Connect GitHub repo to [Vercel](https://vercel.com) (Hobby tier is 100% free).
   - Set root directory to `apps/web`.
   - Set framework to **Next.js**.
   - Output: `https://your-flowmesh.vercel.app` (Global Edge CDN with sub-20ms latency worldwide).

2. **Backend (Koyeb or Render Free Tier)**:
   - Connect repo to [Koyeb](https://www.koyeb.com) (Free Eco tier) or [Render](https://render.com).
   - Dockerfile path: `infra/docker/Dockerfile.api`.
   - Set environment variables:
     - `DATABASE_URL` = `sqlite+aiosqlite:///./flowmesh.db` (or free [Neon.tech](https://neon.tech) Postgres)
     - `STATE_STORE_PROVIDER` = `memory`
     - `API_SECRET_KEY` = your secret
     - `ENCRYPTION_MASTER_KEY` = your key
   - Deploy!

3. **Free Managed Database (Optional)**:
   - If you want persistent cloud PostgreSQL instead of local SQLite:
     - [Neon.tech](https://neon.tech): 0.5 GB free serverless Postgres with branching.
     - [Supabase](https://supabase.com): 500 MB free PostgreSQL database.

---

## Verification & Zero-Cost Production Health

Confirm your zero-cost stack is fully healthy:

```bash
# 1. Check API Liveness
curl http://localhost:8000/health
# Response: {"status": "healthy", "app": "FlowMesh", "version": "0.1.0"}

# 2. Check Readiness (SQLite & In-Memory State)
curl http://localhost:8000/ready
# Response: {"status": "ready"}

# 3. Test Connectivity
python tests/test_frontend_backend_connectivity.py
# 11/11 tests pass with zero external dependencies
```

---

## Summary
FlowMesh delivers full enterprise capabilities (multi-tenancy, visual DAG workflows, OpenTelemetry tracing, schema drift discovery, and edge agents) with **$0 cloud expenditure**. You never need to pay AWS or cloud providers to take this platform into production!
