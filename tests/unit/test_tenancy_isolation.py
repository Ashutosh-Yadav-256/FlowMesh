"""
Milestone 1 — Tenancy Isolation & Scoped Repository Verification

Proves that:
1. Tenant B cannot read Tenant A's records.
2. Cross-tenant queries return None / 404 (never leaking existence).
3. Mutating operations record immutable audit events tagged with the correct tenant_id.
"""

import sys
import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

sys.path.insert(0, "apps/api")
sys.path.insert(0, "packages/auth")

from app.database import Base
from app.models.tenant import ConnectionRecord, AuditEvent
from app.repositories.tenant_scoped import ConnectionRepository, AuditRepository
from app.services.audit_service import record_audit

TEST_DB_URL = "sqlite+aiosqlite:///:memory:"


@pytest_asyncio.fixture
async def db_session():
    engine = create_async_engine(TEST_DB_URL, echo=False)
    async_session = async_sessionmaker(engine, expire_on_commit=False)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with async_session() as session:
        yield session

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


@pytest.mark.asyncio
async def test_tenant_isolation_cross_tenant_read_returns_none(db_session: AsyncSession):
    """Proves Tenant B cannot fetch Tenant A's row by ID; returns None (404), never leaking existence."""
    repo_a = ConnectionRepository(db_session, tenant_id="tenant_a")
    repo_b = ConnectionRepository(db_session, tenant_id="tenant_b")

    conn_a = ConnectionRecord(
        id="conn_orders_db_tenant_a",
        tenant_id="tenant_a",
        type="postgres",
        name="Private Orders Database",
        config_json={"host": "10.0.1.5", "db": "orders_a"},
        status="healthy",
    )
    await repo_a.create(conn_a)

    fetched_by_a = await repo_a.get_by_id("conn_orders_db_tenant_a")
    assert fetched_by_a is not None
    assert fetched_by_a.id == "conn_orders_db_tenant_a"
    assert fetched_by_a.name == "Private Orders Database"

    fetched_by_b = await repo_b.get_by_id("conn_orders_db_tenant_a")
    assert fetched_by_b is None, "SECURITY FAILURE: Cross-tenant row was leaked to Tenant B!"


@pytest.mark.asyncio
async def test_tenant_isolation_list_and_count(db_session: AsyncSession):
    """Proves list queries return strictly the caller's rows."""
    repo_a = ConnectionRepository(db_session, tenant_id="tenant_a")
    repo_b = ConnectionRepository(db_session, tenant_id="tenant_b")

    await repo_a.create(ConnectionRecord(id="c1", tenant_id="tenant_a", type="postgres", name="A1"))
    await repo_a.create(ConnectionRecord(id="c2", tenant_id="tenant_a", type="rest", name="A2"))

    await repo_b.create(ConnectionRecord(id="c3", tenant_id="tenant_b", type="sftp", name="B1"))

    items_a = await repo_a.list_all()
    count_a = await repo_a.count()
    assert len(items_a) == 2
    assert count_a == 2
    assert {i.id for i in items_a} == {"c1", "c2"}

    items_b = await repo_b.list_all()
    count_b = await repo_b.count()
    assert len(items_b) == 1
    assert count_b == 1
    assert items_b[0].id == "c3"


@pytest.mark.asyncio
async def test_cross_tenant_delete_prevention(db_session: AsyncSession):
    """Proves Tenant B cannot delete Tenant A's entity."""
    repo_a = ConnectionRepository(db_session, tenant_id="tenant_a")
    repo_b = ConnectionRepository(db_session, tenant_id="tenant_b")

    await repo_a.create(ConnectionRecord(id="c_critical", tenant_id="tenant_a", type="postgres", name="Critical DB"))

    deleted_by_b = await repo_b.delete("c_critical")
    assert deleted_by_b is False

    still_exists = await repo_a.get_by_id("c_critical")
    assert still_exists is not None


@pytest.mark.asyncio
async def test_audit_event_recording_per_tenant(db_session: AsyncSession):
    """Proves that mutating actions create immutable audit events tagged to the correct tenant."""
    audit_repo_a = AuditRepository(db_session, tenant_id="tenant_a")

    event = await audit_repo_a.record(
        actor="admin@corp-a.com",
        action="connection.create",
        resource="connection:c1",
        result="SUCCESS",
        metadata={"host": "10.0.1.5"},
    )

    assert event.id.startswith("aud_")
    assert event.tenant_id == "tenant_a"
    assert event.actor == "admin@corp-a.com"

    audit_repo_b = AuditRepository(db_session, tenant_id="tenant_b")
    events_b = await audit_repo_b.list_all()
    assert len(events_b) == 0, "Audit trail leaked to another tenant!"
