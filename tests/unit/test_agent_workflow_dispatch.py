"""
Integration test for Workflow Engine edge agent dispatch.

Proves that:
1. When a workflow node executes against a connection configured with `agent_id`,
   the WorkflowEngine routes the execution to the Edge Agent plane.
2. The command is persisted in `agent_commands` and signed with Ed25519.
3. The step snapshot reflects `execution_plane: "edge_agent"`.
"""

import sys
import pytest
import pytest_asyncio

sys.path.insert(0, "apps/api")
sys.path.insert(0, "packages/auth")
sys.path.insert(0, "packages/connector-sdk")
sys.path.insert(0, "packages/state-store")
sys.path.insert(0, "services/workflow-engine")
sys.path.insert(0, "services/incident-manager")

from app.database import engine, Base, AsyncSessionLocal
from app.models.tenant import Tenant, ConnectionRecord
from app.models.agent import AgentRecord
from app.repositories.tenant_scoped import (
    ConnectionRepository,
    AgentRepository,
    AgentCommandRepository,
    RunRepository,
)
from flowmesh_workflow.schema import WorkflowDefinition, WorkflowNode, WorkflowEdge, TriggerSpec
from flowmesh_engine.engine import WorkflowEngine
from flowmesh_auth.signing import verify_ed25519_signature, get_control_plane_signer


@pytest_asyncio.fixture(autouse=True)
async def init_tables():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield


@pytest.mark.asyncio
async def test_workflow_engine_dispatches_to_edge_agent():
    tenant_id = "tenant_edge_test"

    async with AsyncSessionLocal() as db:

        tenant = await db.get(Tenant, tenant_id)
        if not tenant:
            db.add(Tenant(id=tenant_id, name="Edge Test Tenant", slug=tenant_id))
            await db.commit()

        agent_repo = AgentRepository(db, tenant_id)
        await agent_repo.create_agent(
            agent_id="agent-custom-01",
            name="Custom On-Premises Agent",
            version="v0.5.0",
        )

        conn_repo = ConnectionRepository(db, tenant_id)
        conn = ConnectionRecord(
            id="conn_onprem_orders",
            tenant_id=tenant_id,
            name="On-Premises Orders DB",
            type="postgres",
            agent_id="agent-custom-01",
            config_json={"host": "10.0.1.5", "port": 5432, "database": "orders_db"},
        )
        await conn_repo.create(conn)

    workflow = WorkflowDefinition(
        id="wf_edge_dispatch",
        name="Edge Dispatch Workflow",
        schema_version=1,
        trigger=TriggerSpec(type="webhook", path="/onprem-orders"),
        nodes=[
            WorkflowNode(
                id="node_trigger",
                name="Order Event Received",
                type="trigger.webhook",
            ),
            WorkflowNode(
                id="node_query_onprem",
                name="Query Internal Orders DB",
                type="action.db_query",
                connection_id="conn_onprem_orders",
                config={"operation": "query", "resource": "orders", "limit": 25},
            ),
        ],
        edges=[
            WorkflowEdge(source="node_trigger", target="node_query_onprem"),
        ],
    )

    async with AsyncSessionLocal() as db:
        engine_instance = WorkflowEngine(db, tenant_id)
        run = await engine_instance.execute(
            workflow_def=workflow,
            run_id="run_edge_001",
            input_payload={"order_id": "ORD-999"},
        )

        assert run.status == "SUCCESS"

        run_repo = RunRepository(db, tenant_id)
        run_detail = await run_repo.get_by_id("run_edge_001")
        assert run_detail is not None

        step = next(s for s in run_detail.steps if s.node_id == "node_query_onprem")
        assert step.status == "SUCCESS"
        assert step.output_snapshot["execution_plane"] == "edge_agent"
        assert step.output_snapshot["agent_id"] == "agent-custom-01"

        cmd_repo = AgentCommandRepository(db, tenant_id)
        pending = await cmd_repo.get_pending_commands("agent-custom-01")
        assert len(pending) == 1
        cmd = pending[0]
        assert cmd.operation == "query"
        assert cmd.resource == "orders"
        assert cmd.limit == 25

        signer = get_control_plane_signer()
        expected_payload = {
            "id": cmd.id,
            "type": "connector.execute",
            "connector": "postgres",
            "connection_id": "conn_onprem_orders",
            "operation": "query",
            "resource": "orders",
            "limit": 25,
            "payload": {"operation": "query", "resource": "orders", "limit": 25},
        }
        assert verify_ed25519_signature(signer.public_key_b64, expected_payload, cmd.signature) is True
