"""
FlowMesh StateStore Abstraction

Decouples workflow orchestration and reliability primitives (distributed locks,
rate limiters, circuit breakers, idempotency keys, execution leases) from the
underlying storage engine (Redis, RediForge, or In-Memory).
"""

from abc import ABC, abstractmethod
from typing import Optional, Dict, Any


class StateStore(ABC):
    """Abstract StateStore interface implemented by Redis, RediForge, and Memory."""

    @abstractmethod
    async def get(self, key: str) -> Optional[str]:
        """Fetch a value by key."""
        pass

    @abstractmethod
    async def set(self, key: str, value: str, ttl_seconds: Optional[int] = None) -> bool:
        """Store a value with optional expiration."""
        pass

    @abstractmethod
    async def delete(self, key: str) -> bool:
        """Remove a key."""
        pass

    @abstractmethod
    async def acquire_lock(self, lock_name: str, owner_id: str, ttl_ms: int = 5000) -> bool:
        """Acquire a distributed lock atomically."""
        pass

    @abstractmethod
    async def release_lock(self, lock_name: str, owner_id: str) -> bool:
        """Release a distributed lock safely only if owned by owner_id."""
        pass

    @abstractmethod
    async def get_circuit_breaker_state(self, connection_id: str) -> str:
        """Returns circuit state: 'CLOSED', 'OPEN', 'HALF-OPEN'."""
        pass

    @abstractmethod
    async def record_circuit_failure(self, connection_id: str, threshold: int = 5) -> str:
        """Records a failure and trips circuit if threshold exceeded."""
        pass

    @abstractmethod
    async def record_circuit_success(self, connection_id: str) -> str:
        """Records a successful operation; recovers from HALF-OPEN to CLOSED."""
        pass

    @abstractmethod
    async def reset_circuit_breaker(self, connection_id: str) -> None:
        """Resets circuit breaker to 'CLOSED' state."""
        pass


class MemoryStateStore(StateStore):
    """In-memory StateStore implementation for zero-dependency local development and testing."""

    def __init__(self, default_cooldown_seconds: float = 5.0) -> None:
        self._data: Dict[str, str] = {}
        self._locks: Dict[str, str] = {}
        self._circuit_failures: Dict[str, int] = {}
        self._circuit_state: Dict[str, str] = {}
        self._circuit_opened_at: Dict[str, float] = {}
        self.default_cooldown_seconds = default_cooldown_seconds

    async def get(self, key: str) -> Optional[str]:
        return self._data.get(key)

    async def set(self, key: str, value: str, ttl_seconds: Optional[int] = None) -> bool:
        self._data[key] = value
        return True

    async def delete(self, key: str) -> bool:
        if key in self._data:
            del self._data[key]
            return True
        return False

    async def acquire_lock(self, lock_name: str, owner_id: str, ttl_ms: int = 5000) -> bool:
        if lock_name in self._locks:
            return False
        self._locks[lock_name] = owner_id
        return True

    async def release_lock(self, lock_name: str, owner_id: str) -> bool:
        if self._locks.get(lock_name) == owner_id:
            del self._locks[lock_name]
            return True
        return False

    async def get_circuit_breaker_state(self, connection_id: str, cooldown_seconds: Optional[float] = None) -> str:
        import time
        current_state = self._circuit_state.get(connection_id, "CLOSED")
        if current_state == "OPEN":
            cooldown = cooldown_seconds if cooldown_seconds is not None else self.default_cooldown_seconds
            opened_at = self._circuit_opened_at.get(connection_id, 0.0)
            if time.time() - opened_at >= cooldown:
                self._circuit_state[connection_id] = "HALF-OPEN"
                return "HALF-OPEN"
        return current_state

    async def record_circuit_failure(self, connection_id: str, threshold: int = 5) -> str:
        import time
        current_state = self._circuit_state.get(connection_id, "CLOSED")
        if current_state == "HALF-OPEN":

            self._circuit_state[connection_id] = "OPEN"
            self._circuit_opened_at[connection_id] = time.time()
            return "OPEN"

        count = self._circuit_failures.get(connection_id, 0) + 1
        self._circuit_failures[connection_id] = count
        if count >= threshold:
            self._circuit_state[connection_id] = "OPEN"
            self._circuit_opened_at[connection_id] = time.time()
            return "OPEN"
        return "CLOSED"

    async def record_circuit_success(self, connection_id: str) -> str:

        self._circuit_failures[connection_id] = 0
        self._circuit_state[connection_id] = "CLOSED"
        self._circuit_opened_at.pop(connection_id, None)
        return "CLOSED"

    async def reset_circuit_breaker(self, connection_id: str) -> None:
        self._circuit_failures[connection_id] = 0
        self._circuit_state[connection_id] = "CLOSED"
        self._circuit_opened_at.pop(connection_id, None)


class RedisStateStore(StateStore):
    """
    Production-grade StateStore backed by Redis or RediForge via redis.asyncio.
    Supports atomic distributed locks (NX/PX), safe Lua release, and circuit breaker tracking.
    """

    def __init__(
        self,
        redis_url: str = "redis://localhost:6379/0",
        default_cooldown_seconds: float = 5.0,
    ) -> None:
        import redis.asyncio as aioredis

        self.redis_url = redis_url
        self._client = aioredis.from_url(redis_url, decode_responses=True)
        self.default_cooldown_seconds = default_cooldown_seconds

    async def get(self, key: str) -> Optional[str]:
        return await self._client.get(key)

    async def set(self, key: str, value: str, ttl_seconds: Optional[int] = None) -> bool:
        if ttl_seconds:
            await self._client.set(key, value, ex=ttl_seconds)
        else:
            await self._client.set(key, value)
        return True

    async def delete(self, key: str) -> bool:
        res = await self._client.delete(key)
        return bool(res > 0)

    async def acquire_lock(self, lock_name: str, owner_id: str, ttl_ms: int = 5000) -> bool:
        res = await self._client.set(f"lock:{lock_name}", owner_id, px=ttl_ms, nx=True)
        return bool(res)

    async def release_lock(self, lock_name: str, owner_id: str) -> bool:
        lua = """
        if redis.call("get", KEYS[1]) == ARGV[1] then
            return redis.call("del", KEYS[1])
        else
            return 0
        end
        """
        res = await self._client.eval(lua, 1, f"lock:{lock_name}", owner_id)
        return bool(res == 1)

    async def get_circuit_breaker_state(
        self, connection_id: str, cooldown_seconds: Optional[float] = None
    ) -> str:
        import time

        cooldown = (
            cooldown_seconds
            if cooldown_seconds is not None
            else self.default_cooldown_seconds
        )
        lua = """
        local state = redis.call("GET", KEYS[1]) or "CLOSED"
        if state == "OPEN" then
            local opened_at_str = redis.call("GET", KEYS[2])
            local opened_at = tonumber(opened_at_str) or 0
            local now = tonumber(ARGV[2])
            local cooldown = tonumber(ARGV[1])
            if (now - opened_at) >= cooldown then
                redis.call("SET", KEYS[1], "HALF-OPEN")
                return "HALF-OPEN"
            end
        end
        return state
        """
        result = await self._client.eval(
            lua, 2,
            f"cb:{connection_id}:state",
            f"cb:{connection_id}:opened_at",
            str(cooldown),
            str(time.time()),
        )
        return result.decode() if isinstance(result, bytes) else result

    async def record_circuit_failure(self, connection_id: str, threshold: int = 5) -> str:
        import time

        lua = """
        local state = redis.call("GET", KEYS[1]) or "CLOSED"
        if state == "HALF-OPEN" then
            redis.call("SET", KEYS[1], "OPEN")
            redis.call("SET", KEYS[2], ARGV[2])
            return "OPEN"
        end
        local count = redis.call("INCR", KEYS[3])
        if tonumber(count) >= tonumber(ARGV[1]) then
            redis.call("SET", KEYS[1], "OPEN")
            redis.call("SET", KEYS[2], ARGV[2])
            return "OPEN"
        end
        return "CLOSED"
        """
        result = await self._client.eval(
            lua, 3,
            f"cb:{connection_id}:state",
            f"cb:{connection_id}:opened_at",
            f"cb:{connection_id}:failures",
            str(threshold),
            str(time.time()),
        )
        return result.decode() if isinstance(result, bytes) else result

    async def record_circuit_success(self, connection_id: str) -> str:
        await self._client.delete(f"cb:{connection_id}:failures")
        await self._client.set(f"cb:{connection_id}:state", "CLOSED")
        await self._client.delete(f"cb:{connection_id}:opened_at")
        return "CLOSED"

    async def reset_circuit_breaker(self, connection_id: str) -> None:
        await self._client.delete(f"cb:{connection_id}:failures")
        await self._client.set(f"cb:{connection_id}:state", "CLOSED")
        await self._client.delete(f"cb:{connection_id}:opened_at")

    async def close(self) -> None:
        await self._client.aclose()


_global_state_store: Optional[StateStore] = None


def get_state_store(
    provider: Optional[str] = None, redis_url: Optional[str] = None
) -> StateStore:
    """Returns the configured global StateStore singleton (defaults to MemoryStateStore)."""
    global _global_state_store
    if _global_state_store is None:
        import os

        selected = provider or os.environ.get("STATE_STORE_PROVIDER", "memory").lower()
        if selected in ("redis", "rediforge"):
            url = redis_url or os.environ.get("REDIS_URL", "redis://localhost:6379/0")
            _global_state_store = RedisStateStore(redis_url=url)
        else:
            _global_state_store = MemoryStateStore()
    return _global_state_store


def set_state_store(store: StateStore) -> None:
    """Sets the global StateStore instance."""
    global _global_state_store
    _global_state_store = store
