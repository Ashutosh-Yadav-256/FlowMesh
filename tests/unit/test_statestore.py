import sys
import pytest

sys.path.insert(0, "packages/state-store")
from flowmesh_state.interface import MemoryStateStore


@pytest.mark.asyncio
async def test_statestore_key_value():
    store = MemoryStateStore()

    await store.set("order:1001:status", "PROCESSING", ttl_seconds=60)
    val = await store.get("order:1001:status")
    assert val == "PROCESSING"

    deleted = await store.delete("order:1001:status")
    assert deleted is True
    assert await store.get("order:1001:status") is None


@pytest.mark.asyncio
async def test_statestore_distributed_locks():
    store = MemoryStateStore()

    acquired = await store.acquire_lock("run_lease:RUN-92831", owner_id="worker-node-01")
    assert acquired is True

    second_attempt = await store.acquire_lock("run_lease:RUN-92831", owner_id="worker-node-02")
    assert second_attempt is False

    invalid_release = await store.release_lock("run_lease:RUN-92831", owner_id="worker-node-02")
    assert invalid_release is False

    valid_release = await store.release_lock("run_lease:RUN-92831", owner_id="worker-node-01")
    assert valid_release is True

    reacquired = await store.acquire_lock("run_lease:RUN-92831", owner_id="worker-node-02")
    assert reacquired is True


@pytest.mark.asyncio
async def test_statestore_circuit_breaker():
    store = MemoryStateStore()

    initial_state = await store.get_circuit_breaker_state("conn_warehouse_api")
    assert initial_state == "CLOSED"

    s1 = await store.record_circuit_failure("conn_warehouse_api", threshold=3)
    assert s1 == "CLOSED"
    s2 = await store.record_circuit_failure("conn_warehouse_api", threshold=3)
    assert s2 == "CLOSED"
    s3 = await store.record_circuit_failure("conn_warehouse_api", threshold=3)
    assert s3 == "OPEN"

    assert await store.get_circuit_breaker_state("conn_warehouse_api") == "OPEN"

    await store.reset_circuit_breaker("conn_warehouse_api")
    assert await store.get_circuit_breaker_state("conn_warehouse_api") == "CLOSED"
