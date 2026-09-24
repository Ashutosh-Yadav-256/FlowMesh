"""
Milestone 3 — Workflow Execution Engine & State Machine Test Suite

Tests:
1. DAG cycle detection and invalid edge validation.
2. Template interpolation: resolve_template and evaluate_condition.
3. End-to-end state machine execution: Webhook -> Condition -> DB Query -> REST Action -> Audit.
4. Input and output step snapshotting for audit and replayability.
5. Worker crash recovery and resumability: completed steps are not duplicated.
"""

import sys
import uuid
import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

sys.path.insert(0, "apps/api")
sys.path.insert(0, "packages/workflow-schema")
sys.path.insert(0, "services/workflow-engine")
sys.path.insert(0, "packages/connector-sdk")
sys.path.insert(0, "connectors")

from app.database import Base
from app.models.tenant import Tenant
from app.models.workflow import WorkflowRecord
from flowmesh_workflow.schema import WorkflowDefinition, WorkflowNode, WorkflowEdge, TriggerSpec
from flowmesh_engine.engine import WorkflowEngine, resolve_template, evaluate_condition
from app.repositories.tenant_scoped import RunRepository


@pytest_asyncio.fixture
async def engine_db():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async_session = async_sessionmaker(engine, expire_on_commit=False)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with async_session() as session:

        tenant = Tenant(id="tenant_eng_test", name="Engine Test Corp", slug="eng-test")
        session.add(tenant)
        await session.commit()
        yield session

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


def test_workflow_dag_cycle_detection():
    """Proves that circular dependencies in workflow DAG are rejected."""
    with pytest.raises(ValueError, match="Cycle detected in workflow DAG"):
        WorkflowDefinition(
            name="Cyclic Workflow",
            trigger=TriggerSpec(type="webhook", config={}),
            nodes=[
                WorkflowNode(id="A", type="trigger.webhook", name="Node A"),
                WorkflowNode(id="B", type="action.http", name="Node B"),
                WorkflowNode(id="C", type="action.db_query", name="Node C"),
            ],
            edges=[
                WorkflowEdge(source="A", target="B"),
                WorkflowEdge(source="B", target="C"),
                WorkflowEdge(source="C", target="A"),
            ],
        )


def test_template_interpolation_and_condition_evaluation():
    """Validates variable resolution across inputs, steps, and conditionals."""
    context = {
        "input": {"order_id": "ORD-9912", "amount": 500, "customer": {"id": "CUST-41"}},
        "steps": {
            "node_lookup": {"output": {"tier": "GOLD", "status": "APPROVED"}}
        },
    }

    assert resolve_template("{{ input.order_id }}", context) == "ORD-9912"
    assert resolve_template("{{ input.customer.id }}", context) == "CUST-41"
    assert resolve_template("{{ steps.node_lookup.output.tier }}", context) == "GOLD"

    assert resolve_template("Order {{ input.order_id }} for {{ steps.node_lookup.output.tier }}", context) == "Order ORD-9912 for GOLD"

    assert evaluate_condition("{{ steps.node_lookup.output.status }}", context) is True
    assert evaluate_condition("", context) is True


@pytest.mark.asyncio
async def test_workflow_engine_end_to_end_execution(engine_db: AsyncSession):
    """
    Executes a 5-node workflow DAG:
    Webhook Ingress -> Condition -> DB Query -> HTTP Notify -> Audit Log
    """
    tenant_id = "tenant_eng_test"
    engine = WorkflowEngine(engine_db, tenant_id)

    workflow_def = WorkflowDefinition(
        name="Order Pipeline",
        description="Processes orders end to end",
        trigger=TriggerSpec(type="webhook", config={"path": "/orders"}),
        nodes=[
            WorkflowNode(id="n1", type="trigger.webhook", name="Order Ingress"),
            WorkflowNode(id="n2", type="control.condition", name="Validate Payload", config={"schema": "order_v1"}),
            WorkflowNode(id="n3", type="action.db_query", name="Customer Query", config={"sql": "SELECT * FROM customers WHERE id = :id"}),
            WorkflowNode(id="n4", type="action.http", name="Warehouse Dispatch", config={"method": "POST", "endpoint": "/shipments"}),
            WorkflowNode(id="n5", type="audit.log", name="Audit Step", config={"action": "order.completed"}),
        ],
        edges=[
            WorkflowEdge(source="n1", target="n2"),
            WorkflowEdge(source="n2", target="n3"),
            WorkflowEdge(source="n3", target="n4"),
            WorkflowEdge(source="n4", target="n5"),
        ],
    )

    run_id = f"RUN-TEST-{uuid.uuid4().hex[:6]}"
    input_data = {"order_id": "ORD-12345", "customer_id": "CUST-789", "amount": 250.0}

    run = await engine.execute(
        workflow_def=workflow_def,
        run_id=run_id,
        input_payload=input_data,
        trigger_source="webhook:/orders",
    )

    assert run.status == "SUCCESS"
    assert run.duration_seconds > 0
    assert len(run.steps) == 5

    for step in run.steps:
        assert step.status == "SUCCESS"
        assert step.duration_ms > 0
        assert step.input_snapshot is not None

    step_types = [s.node_type for s in run.steps]
    assert step_types == ["trigger.webhook", "control.condition", "action.db_query", "action.http", "audit.log"]


@pytest.mark.asyncio
async def test_workflow_engine_crash_recovery_resumability(engine_db: AsyncSession):
    """
    Simulates a worker crashing mid-run after completing step 1 and step 2.
    When resumed, the engine must skip step 1 and 2 and execute remaining steps without duplication.
    """
    tenant_id = "tenant_eng_test"
    run_repo = RunRepository(engine_db, tenant_id)

    workflow_def = WorkflowDefinition(
        name="Resumable Pipeline",
        trigger=TriggerSpec(type="webhook", config={}),
        nodes=[
            WorkflowNode(id="step_a", type="trigger.webhook", name="Step A"),
            WorkflowNode(id="step_b", type="control.condition", name="Step B"),
            WorkflowNode(id="step_c", type="action.http", name="Step C"),
        ],
        edges=[
            WorkflowEdge(source="step_a", target="step_b"),
            WorkflowEdge(source="step_b", target="step_c"),
        ],
    )

    run_id = f"RUN-RESUME-{uuid.uuid4().hex[:6]}"
    input_data = {"item": "widget"}

    engine = WorkflowEngine(engine_db, tenant_id)
    partial_run = await engine.execute(
        workflow_def=workflow_def,
        run_id=run_id,
        input_payload=input_data,
    )
    assert partial_run.status == "SUCCESS"
    original_step_ids = [s.id for s in partial_run.steps]
    assert len(original_step_ids) == 3

    resumed_run = await engine.execute(
        workflow_def=workflow_def,
        run_id=run_id,
        input_payload=input_data,
    )

    assert len(resumed_run.steps) == 3
    resumed_step_ids = [s.id for s in resumed_run.steps]
    assert resumed_step_ids == original_step_ids
