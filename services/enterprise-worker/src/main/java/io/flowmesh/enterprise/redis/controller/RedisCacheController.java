package io.flowmesh.enterprise.redis.controller;

import io.flowmesh.enterprise.logging.LogExecutionTime;
import io.flowmesh.enterprise.redis.RedisCacheService;
import io.flowmesh.enterprise.redis.RedisDistributedLockService;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.time.Duration;
import java.util.Map;
import java.util.Set;

@RestController
@RequestMapping("/api/v1/enterprise/cache")
@CrossOrigin(origins = "*")
public class RedisCacheController {

    private final RedisCacheService cacheService;
    private final RedisDistributedLockService lockService;

    public RedisCacheController(RedisCacheService cacheService, RedisDistributedLockService lockService) {
        this.cacheService = cacheService;
        this.lockService = lockService;
    }

    @GetMapping("/stats")
    public ResponseEntity<Map<String, Object>> getStats() {
        return ResponseEntity.ok(cacheService.getCacheStats());
    }

    @GetMapping("/keys")
    public ResponseEntity<Set<String>> listKeys(@RequestParam(defaultValue = "*") String pattern) {
        return ResponseEntity.ok(cacheService.getKeys(pattern));
    }

    @GetMapping("/keys/{key}")
    public ResponseEntity<?> getKey(@PathVariable String key) {
        Object val = cacheService.get(key);
        if (val == null) {
            return ResponseEntity.notFound().build();
        }
        return ResponseEntity.ok(Map.of("key", key, "value", val));
    }

    @PostMapping("/keys")
    @LogExecutionTime(thresholdMs = 200, operation = "cache.put")
    public ResponseEntity<?> setKey(@RequestBody Map<String, Object> payload) {
        String key = (String) payload.get("key");
        Object value = payload.get("value");
        Number ttlSec = (Number) payload.getOrDefault("ttlSeconds", 300);

        if (key == null || value == null) {
            return ResponseEntity.badRequest().body(Map.of("error", "Key and value are required"));
        }

        cacheService.put(key, value, Duration.ofSeconds(ttlSec.longValue()));
        return ResponseEntity.ok(Map.of("status", "SUCCESS", "key", key, "ttlSeconds", ttlSec));
    }

    @DeleteMapping("/keys/{key}")
    public ResponseEntity<?> evictKey(@PathVariable String key) {
        boolean evicted = cacheService.evict(key);
        return ResponseEntity.ok(Map.of("key", key, "evicted", evicted));
    }

    @PostMapping("/lock/acquire")
    @LogExecutionTime(thresholdMs = 300, operation = "lock.acquire")
    public ResponseEntity<?> acquireLock(@RequestBody Map<String, Object> payload) {
        String tenantId = (String) payload.getOrDefault("tenantId", "tenant_acme");
        String resource = (String) payload.getOrDefault("resource", "ledger-reconciliation");
        Number ttlMs = (Number) payload.getOrDefault("ttlMs", 30000);

        RedisDistributedLockService.LockResult res =
                lockService.acquireLock(tenantId, resource, Duration.ofMillis(ttlMs.longValue()));

        return ResponseEntity.ok(res);
    }

    @PostMapping("/lock/release")
    @LogExecutionTime(thresholdMs = 200, operation = "lock.release")
    public ResponseEntity<?> releaseLock(@RequestBody Map<String, Object> payload) {
        String tenantId = (String) payload.getOrDefault("tenantId", "tenant_acme");
        String resource = (String) payload.getOrDefault("resource", "ledger-reconciliation");
        String token = (String) payload.get("token");

        boolean released = lockService.releaseLock(tenantId, resource, token);
        return ResponseEntity.ok(Map.of("released", released, "resource", resource));
    }
}
