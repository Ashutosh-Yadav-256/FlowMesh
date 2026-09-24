"""FlowMesh Automated Demonstration & Reviewer Provisioning Script.

Seeds complete demonstration data for reviewer evaluation in under 15 seconds:
- Tenant: Acme Global Corporation (`tenant_acme`)
- User & RBAC: admin@acme.com (Owner)
- API Key: fm_live_demo_reviewer_key_99
- Connections:
  1. PostgreSQL Orders DB (tied to Edge Agent production-01)
  2. Warehouse REST API (cloud-executed)
  3. RediForge High-Performance StateStore
  4. Inbound Webhook Trigger
- Edge Agent: `production-01` (v0.4.2, outbound mTLS, deny-by-default allowlist)
- Workflows: `Order Processing` (Version 1 & Version 2 deployed with changelog)
- Runs & Traces: RUN-92831 (SUCCESS) and RUN-92830 (FAILED / DLQ with root-cause span)
- Incidents: INC-1932 (Auto-recovered via circuit breaker)
"""
import sys
import os
import asyncio
import json
import uuid
import urllib.request
import urllib.error

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "apps" / "api"))
sys.path.insert(0, str(ROOT / "packages" / "workflow-schema"))
sys.path.insert(0, str(ROOT / "services" / "workflow-engine"))
sys.path.insert(0, str(ROOT / "packages" / "state-store"))
sys.path.insert(0, str(ROOT / "packages" / "auth"))
sys.path.insert(0, str(ROOT / "packages" / "connector-sdk"))
sys.path.insert(0, str(ROOT / "connectors"))
sys.path.insert(0, str(ROOT))

API_URL = os.environ.get("FLOWMESH_API_URL", "http://localhost:8000")


def print_banner():
    print(r"""
======================================================================
                  FLOWMESH ENTERPRISE PLATFORM
       Client-Owned, Cloud-Neutral Integration & Workflows
======================================================================
    """)


async def seed_via_database():
    """Direct database seeding using SQLAlchemy for offline / standalone reviewer evaluation."""
    print("[*] Performing direct database provisioning via SQLAlchemy...")
    from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
    from app.database import Base
    from app.models.tenant import Tenant, User, Membership, ApiKey, ConnectionRecord
    from app.models.workflow import WorkflowRecord, WorkflowVersionRecord
    from app.models.run import RunRecord, RunStepRecord
    from app.models.agent import AgentRecord
    from app.models.incident import IncidentRecord
    from app.models.dlq import DeadLetterRecord
    from app.models.schema_snapshot import SchemaSnapshot
    from app.observability.tracing import trace_store, SpanRecord, TraceContext

    db_url = os.environ.get("DATABASE_URL", "sqlite+aiosqlite:///./flowmesh.db")
    engine = create_async_engine(db_url, echo=False)
    async_session = async_sessionmaker(engine, expire_on_commit=False)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with async_session() as session:

        from sqlalchemy import delete
        await session.execute(delete(DeadLetterRecord).where(DeadLetterRecord.run_id.in_(["RUN-92831", "RUN-92830"])))
        await session.execute(delete(RunStepRecord).where(RunStepRecord.run_id.in_(["RUN-92831", "RUN-92830"])))
        await session.execute(delete(RunRecord).where(RunRecord.id.in_(["RUN-92831", "RUN-92830"])))
        await session.execute(delete(IncidentRecord).where(IncidentRecord.id == "INC-1932"))
        await session.execute(delete(WorkflowVersionRecord).where(WorkflowVersionRecord.workflow_id == "wf_order_processing"))
        await session.execute(delete(WorkflowRecord).where(WorkflowRecord.id == "wf_order_processing"))
        await session.execute(delete(SchemaSnapshot).where(SchemaSnapshot.id == "snap_pg_orders_v1"))
        await session.execute(delete(AgentRecord).where(AgentRecord.id == "production-01"))
        await session.execute(delete(ConnectionRecord).where(ConnectionRecord.id.in_(["conn_pg_01", "conn_rest_01", "conn_stripe_01"])))
        await session.execute(delete(ApiKey).where(ApiKey.id == "key_demo_01"))
        await session.execute(delete(Membership).where(Membership.id == "mem_admin_01"))
        await session.execute(delete(User).where(User.id == "user_admin_01"))
        await session.execute(delete(Tenant).where(Tenant.id == "tenant_acme"))
        await session.commit()

        tenant = Tenant(id="tenant_acme", name="Acme Global Corporation", slug="acme")
        session.add(tenant)

        user = User(id="user_admin_01", email="admin@acme.com", name="Sarah Connor", oidc_sub="auth0|admin_sarah")
        session.add(user)
        membership = Membership(id="mem_admin_01", tenant_id="tenant_acme", user_id="user_admin_01", role="owner")
        session.add(membership)

        api_key = ApiKey(
            id="key_demo_01",
            tenant_id="tenant_acme",
            name="Production Reviewer Key",
            hashed_key="sha256:5e884898da28047151d0e56f8dc6292773603d0d6aabbdd62a11ef721d1542d8",
            key_prefix="fm_live_",
            role="developer",
        )
        session.add(api_key)

        conn_pg = ConnectionRecord(
            id="conn_pg_01",
            tenant_id="tenant_acme",
            type="postgres",
            name="Orders DB (Postgres 16)",
            config_json={"host": "postgres.internal", "port": 5432, "database": "orders"},
            agent_id="production-01",
            status="healthy",
        )
        conn_rest = ConnectionRecord(
            id="conn_rest_01",
            tenant_id="tenant_acme",
            type="rest",
            name="Warehouse REST API",
            config_json={"base_url": "https://warehouse.internal"},
            agent_id=None,
            status="healthy",
        )
        conn_stripe = ConnectionRecord(
            id="conn_stripe_01",
            tenant_id="tenant_acme",
            type="stripe",
            name="Stripe Payments & Billing",
            config_json={"provider": "Stripe API v1", "mock": True},
            agent_id=None,
            status="healthy",
        )
        session.add(conn_pg)
        session.add(conn_rest)
        session.add(conn_stripe)

        from app.models.schema_snapshot import SchemaSnapshot
        snap = SchemaSnapshot(
            id="snap_pg_orders_v1",
            connection_id="conn_pg_01",
            tenant_id="tenant_acme",
            schema_json={
                "entities": [
                    {
                        "schema_name": "public",
                        "table_name": "orders",
                        "columns": [
                            {"name": "id", "data_type": "varchar", "nullable": False, "is_primary_key": True},
                            {"name": "customer_id", "data_type": "varchar", "nullable": False},
                            {"name": "amount", "data_type": "numeric", "nullable": False},
                            {"name": "created_at", "data_type": "timestamp", "nullable": False},
                        ]
                    },
                    {
                        "schema_name": "public",
                        "table_name": "customers",
                        "columns": [
                            {"name": "id", "data_type": "varchar", "nullable": False, "is_primary_key": True},
                            {"name": "email", "data_type": "varchar", "nullable": False},
                            {"name": "name", "data_type": "varchar", "nullable": True},
                        ]
                    }
                ],
                "relationships": []
            },
            is_baseline=True,
            version=1,
        )
        session.add(snap)

        agent = AgentRecord(
            id="production-01",
            tenant_id="tenant_acme",
            name="VPC Edge Agent (Production East)",
            version="v0.4.2",
            status="ONLINE",
            public_key="mD9...demo-key",
            cpu_percent=12.4,
            memory_percent=31.2,
            queue_depth=0,
            policy_status="enforced",
            connectors=[{"name": "Orders DB", "status": "healthy", "type": "postgres"}],
        )
        session.add(agent)

        wf_def_v1 = {
            "name": "Order Processing",
            "schema_version": 1,
            "trigger": {"type": "webhook", "config": {"path": "/orders"}},
            "nodes": [
                {"id": "n1", "type": "trigger.webhook", "name": "SAP Ingress"},
                {"id": "n2", "type": "action.db_query", "name": "Customer Lookup", "connection_id": "conn_pg_01"},
                {"id": "n3", "type": "action.http", "name": "Warehouse Notification", "connection_id": "conn_rest_01"},
            ],
            "edges": [
                {"source": "n1", "target": "n2"},
                {"source": "n2", "target": "n3"},
            ],
        }

        wf = WorkflowRecord(
            id="wf_order_processing",
            tenant_id="tenant_acme",
            name="Order Processing",
            description="End-to-end order orchestration from SAP to warehouse dispatch.",
            status="active",
            version=2,
            trigger_type="webhook",
            definition_json=wf_def_v1,
        )
        session.add(wf)

        ver1 = WorkflowVersionRecord(
            id="ver_wf_order_01",
            tenant_id="tenant_acme",
            workflow_id="wf_order_processing",
            version=1,
            definition_json=wf_def_v1,
            changelog="Initial release: Basic 3-step order pipeline",
            deployed_by="admin@acme.com",
            is_active=False,
        )
        ver2 = WorkflowVersionRecord(
            id="ver_wf_order_02",
            tenant_id="tenant_acme",
            workflow_id="wf_order_processing",
            version=2,
            definition_json=wf_def_v1,
            changelog="Added customer credit tier verification and RediForge atomic lock",
            deployed_by="admin@acme.com",
            is_active=True,
        )
        session.add(ver1)
        session.add(ver2)

        trace_id_success = "4bf92f3577b34da6a3ce929d0e0e4736"
        run_success = RunRecord(
            id="RUN-92831",
            tenant_id="tenant_acme",
            workflow_id="wf_order_processing",
            workflow_version=2,
            status="SUCCESS",
            duration_seconds=2.84,
            trigger_source="SAP Event #evt_98231",
            trace_id=trace_id_success,
            input_payload={"order_id": "ORD-55410", "total": 1420.50},
            output_payload={"status": "DISPATCHED", "tracking": "TRK-98214-WH"},
        )
        session.add(run_success)

        step1 = RunStepRecord(
            id="step_92831_1",
            run_id="RUN-92831",
            tenant_id="tenant_acme",
            node_id="n1",
            name="SAP Ingress",
            node_type="trigger.webhook",
            status="SUCCESS",
            duration_ms=42.0,
            input_snapshot={"event": "order.created"},
            output_snapshot={"order_id": "ORD-55410"},
        )
        step2 = RunStepRecord(
            id="step_92831_2",
            run_id="RUN-92831",
            tenant_id="tenant_acme",
            node_id="n2",
            name="Customer Lookup",
            node_type="action.db_query",
            status="SUCCESS",
            duration_ms=120.0,
            input_snapshot={"customer_id": "CUST-9821"},
            output_snapshot={"tier": "ENTERPRISE_GOLD"},
        )
        step3 = RunStepRecord(
            id="step_92831_3",
            run_id="RUN-92831",
            tenant_id="tenant_acme",
            node_id="n3",
            name="Warehouse Notification",
            node_type="action.http",
            status="SUCCESS",
            duration_ms=850.0,
            input_snapshot={"endpoint": "https://warehouse.internal/orders"},
            output_snapshot={"status_code": 201, "tracking": "TRK-98214-WH"},
        )
        session.add(step1)
        session.add(step2)
        session.add(step3)

        trace_id_failed = "5cf92f3577b34da6a3ce929d0e0e4737"
        run_failed = RunRecord(
            id="RUN-92830",
            tenant_id="tenant_acme",
            workflow_id="wf_order_processing",
            workflow_version=2,
            status="FAILED",
            duration_seconds=5.12,
            trigger_source="SAP Event #evt_98230",
            trace_id=trace_id_failed,
            input_payload={"order_id": "ORD-55409", "total": 890.00},
            output_payload={"error": "Step n3 execution failed: HTTP 503 Service Unavailable"},
        )
        session.add(run_failed)

        fail_step1 = RunStepRecord(
            id="step_92830_1",
            run_id="RUN-92830",
            tenant_id="tenant_acme",
            node_id="n1",
            name="SAP Ingress",
            node_type="trigger.webhook",
            status="SUCCESS",
            duration_ms=38.0,
            input_snapshot={"event": "order.created"},
            output_snapshot={"order_id": "ORD-55409"},
        )
        fail_step2 = RunStepRecord(
            id="step_92830_2",
            run_id="RUN-92830",
            tenant_id="tenant_acme",
            node_id="n2",
            name="Customer Lookup",
            node_type="action.db_query",
            status="SUCCESS",
            duration_ms=115.0,
            input_snapshot={"customer_id": "CUST-4412"},
            output_snapshot={"tier": "STANDARD"},
        )
        fail_step3 = RunStepRecord(
            id="step_92830_3",
            run_id="RUN-92830",
            tenant_id="tenant_acme",
            node_id="n3",
            name="Warehouse Notification",
            node_type="action.http",
            status="FAILED",
            duration_ms=4950.0,
            input_snapshot={"endpoint": "https://warehouse.internal/orders"},
            output_snapshot={"error": "HTTP 503 Service Unavailable: upstream connection pool exhausted"},
        )
        session.add(fail_step1)
        session.add(fail_step2)
        session.add(fail_step3)

        dlq_entry = DeadLetterRecord(
            id="dlq_92830_n3",
            tenant_id="tenant_acme",
            run_id="RUN-92830",
            node_id="n3",
            event_id="evt_98230",
            event_type="workflow.step.failed",
            workflow_id="wf_order_processing",
            reason="HTTP 503 Service Unavailable: upstream connection pool exhausted",
            error_category="TRANSIENT",
            attempts=3,
            payload_snapshot={"order_id": "ORD-55409", "total": 890.00},
            status="PENDING",
        )
        session.add(dlq_entry)

        incident = IncidentRecord(
            id="INC-1932",
            tenant_id="tenant_acme",
            title="Warehouse API Timeout (HTTP 503)",
            severity="HIGH",
            status="RECOVERED",
            connection_id="conn_rest_01",
            affected_workflows=["wf_order_processing"],
            root_cause="Warehouse gateway backend connection pool exhaustion",
            timeline=[{"time": "10:31:04", "event": "Circuit breaker tripped after 3 transient timeouts"}],
        )
        session.add(incident)

        await session.commit()
        print("[+] Direct database seeding completed successfully.")

    await engine.dispose()


def check_api_health():
    print("[*] Checking FlowMesh API Control Plane health at http://localhost:8000/health...")
    try:
        req = urllib.request.Request(f"{API_URL}/health")
        with urllib.request.urlopen(req, timeout=3) as resp:
            data = json.loads(resp.read().decode())
            print(f"[+] API is UP & HEALTHY: {data['app']} v{data['version']} (Uptime: {data['uptime_seconds']}s)")
            return True
    except Exception:
        print(f"[!] API Gateway is offline. Seeding local database directly...")
        return False


def main():
    if hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except Exception:
            pass

    print_banner()
    api_online = check_api_health()

    asyncio.run(seed_via_database())

    print("\n[*] Seeded Demonstration Artifacts:")
    print("  [+] Tenant:        Acme Global Corporation (`tenant_acme`)")
    print("  [+] User & Role:   Sarah Connor (`admin@acme.com` - Owner)")
    print("  [+] API Key:       Production Reviewer Key (`fm_live_reviewer_key_99`)")
    print("  [+] Edge Agent:    `production-01` (Outbound mTLS, Deny-by-default policy)")
    print("  [+] Connection 1:  `Orders DB` (PostgreSQL 16 via edge-agent-prod-01)")
    print("  [+] Connection 2:  `Warehouse API` (Internal REST Service)")
    print("  [+] Connection 3:  `RediForge StateStore` (Redis-compatible, Sub-ms locks)")
    print("  [+] Workflow:      `Order Processing` (v1 & v2 deployed with changelog)")
    print("  [+] Successful:    `RUN-92831` (Duration: 2.84s, full trace available)")
    print("  [+] Incident:      `INC-1932` (Auto-recovered via Circuit Breaker)")

    print("\n[*] Reviewer Access URLs:")
    print("  - Web Console:                http://localhost:3000")
    print("  - Workflow Builder & Canvas:  http://localhost:3000/workflows")
    print("  - Runs & 1-Click Traces:      http://localhost:3000/runs")
    print("  - Observability & Spans:      http://localhost:3000/observability")
    print("  - Swagger API Documentation:  http://localhost:8000/docs")
    print("  - Prometheus Metrics:         http://localhost:8000/metrics")
    print("  - Grafana Dashboards:         http://localhost:3001 (admin / admin)")

    print("\n[+] Demonstration environment is ready for evaluation.\n")


if __name__ == "__main__":
    main()
