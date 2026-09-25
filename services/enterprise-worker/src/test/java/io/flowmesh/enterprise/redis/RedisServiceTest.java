package io.flowmesh.enterprise.redis;

import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;

import java.time.Duration;
import java.util.Map;
import java.util.Set;

import static org.junit.jupiter.api.Assertions.*;

@DisplayName("Redis Distributed Caching & Distributed Locks Tests")
class RedisServiceTest {

    private RedisCacheService cacheService;
    private RedisDistributedLockService lockService;

    @BeforeEach
    void setUp() {
        cacheService = new RedisCacheService(null); // Local fallback mode
        lockService = new RedisDistributedLockService(null);
    }

    @Test
    @DisplayName("Should put, get, and evict keys in cache")
    void testCacheOperations() {
        String key = "test:tenant:key";
        String value = "flowmesh-cache-payload";

        cacheService.put(key, value, Duration.ofMinutes(5));
        assertEquals(value, cacheService.get(key));

        Set<String> keys = cacheService.getKeys("test:*");
        assertTrue(keys.contains(key));

        boolean evicted = cacheService.evict(key);
        assertTrue(evicted);
        assertNull(cacheService.get(key));
    }

    @Test
    @DisplayName("Should calculate hit ratio and provide telemetry")
    void testCacheTelemetry() {
        cacheService.put("k1", "v1", null);
        cacheService.get("k1"); // Hit
        cacheService.get("non_existent_key"); // Miss

        Map<String, Object> stats = cacheService.getCacheStats();
        assertNotNull(stats);
        assertTrue(stats.containsKey("hitRatio"));
        assertTrue(stats.containsKey("totalCachedKeys"));
    }

    @Test
    @DisplayName("Should acquire and safely release distributed lock")
    void testDistributedLockLifecycle() {
        String tenant = "tenant_acme";
        String resource = "reconciliation-batch-001";

        RedisDistributedLockService.LockResult lock1 =
                lockService.acquireLock(tenant, resource, Duration.ofSeconds(10));

        assertTrue(lock1.acquired());
        assertNotNull(lock1.token());

        // Second acquire on same resource while held should fail
        RedisDistributedLockService.LockResult lock2 =
                lockService.acquireLock(tenant, resource, Duration.ofSeconds(10));
        assertFalse(lock2.acquired());

        // Releasing with wrong token should fail
        boolean falseRelease = lockService.releaseLock(tenant, resource, "wrong-token");
        assertFalse(falseRelease);

        // Releasing with correct token should succeed
        boolean successRelease = lockService.releaseLock(tenant, resource, lock1.token());
        assertTrue(successRelease);

        // Now should be acquirable again
        RedisDistributedLockService.LockResult lock3 =
                lockService.acquireLock(tenant, resource, Duration.ofSeconds(10));
        assertTrue(lock3.acquired());
    }
}
