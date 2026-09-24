import asyncio
import sys
import pytest

sys.path.insert(0, "packages/state-store")
from flowmesh_state.interface import MemoryStateStore, RedisStateStore


@pytest.mark.asyncio
async def test_concurrent_failures_atomic_memory():
    store = MemoryStateStore()
    connection_id = "conn_concurrent_test"

    tasks = [
        store.record_circuit_failure(connection_id, threshold=5)
        for _ in range(10)
    ]
    results = await asyncio.gather(*tasks)

    final_state = await store.get_circuit_breaker_state(connection_id)
    assert final_state == "OPEN"

    assert "OPEN" in results


@pytest.mark.asyncio
async def test_redis_state_store_eval_mock():

    class MockRedisClient:
        def __init__(self):
            self.store = {}

        async def eval(self, script, numkeys, *keys_and_args):
            keys = keys_and_args[:numkeys]
            args = keys_and_args[numkeys:]

            if "local count = redis.call(\"INCR\", KEYS[3])" in script:

                state_key, opened_key, fail_key = keys[0], keys[1], keys[2]
                threshold, now_ts = int(args[0]), args[1]

                current_state = self.store.get(state_key, "CLOSED")
                if current_state == "HALF-OPEN":
                    self.store[state_key] = "OPEN"
                    self.store[opened_key] = now_ts
                    return b"OPEN"

                count = self.store.get(fail_key, 0) + 1
                self.store[fail_key] = count
                if count >= threshold:
                    self.store[state_key] = "OPEN"
                    self.store[opened_key] = now_ts
                    return b"OPEN"
                return b"CLOSED"

            elif "HALF-OPEN" in script:

                state_key, opened_key = keys[0], keys[1]
                cooldown, now_ts = float(args[0]), float(args[1])
                current_state = self.store.get(state_key, "CLOSED")
                if current_state == "OPEN":
                    opened_at = float(self.store.get(opened_key, 0))
                    if (now_ts - opened_at) >= cooldown:
                        self.store[state_key] = "HALF-OPEN"
                        return b"HALF-OPEN"
                return current_state.encode()

            return b"OK"

    redis_store = RedisStateStore(redis_url="redis://dummy")
    redis_store._client = MockRedisClient()

    st1 = await redis_store.get_circuit_breaker_state("conn_test_mock")
    assert st1 == "CLOSED"

    for _ in range(4):
        s = await redis_store.record_circuit_failure("conn_test_mock", threshold=5)
        assert s == "CLOSED"

    s_trip = await redis_store.record_circuit_failure("conn_test_mock", threshold=5)
    assert s_trip == "OPEN"

    st2 = await redis_store.get_circuit_breaker_state("conn_test_mock", cooldown_seconds=60)
    assert st2 == "OPEN"

    st3 = await redis_store.get_circuit_breaker_state("conn_test_mock", cooldown_seconds=0.0)
    assert st3 == "HALF-OPEN"
