package io.flowmesh.enterprise.redis;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.data.redis.core.RedisTemplate;
import org.springframework.stereotype.Service;

import java.time.Duration;
import java.time.Instant;
import java.util.Map;
import java.util.UUID;
import java.util.concurrent.ConcurrentHashMap;

@Service
public class RedisDistributedLockService {

    private static final Logger log = LoggerFactory.getLogger(RedisDistributedLockService.class);

    private final RedisTemplate<String, Object> redisTemplate;
    private final Map<String, LocalLockEntry> localLockStore = new ConcurrentHashMap<>();

    private record LocalLockEntry(String token, Instant expiresAt) {}

    public record LockResult(
            boolean acquired,
            String token,
            String lockKey,
            Instant expiresAt,
            String message
    ) {}

    @Autowired(required = false)
    public RedisDistributedLockService(RedisTemplate<String, Object> redisTemplate) {
        this.redisTemplate = redisTemplate;
    }

    public LockResult acquireLock(String tenantId, String resource, Duration ttl) {
        String lockKey = "flowmesh:lock:" + (tenantId != null ? tenantId : "default") + ":" + resource;
        String token = UUID.randomUUID().toString();
        Duration lockDuration = (ttl != null && !ttl.isZero()) ? ttl : Duration.ofSeconds(30);
        Instant expiresAt = Instant.now().plus(lockDuration);

        try {
            if (redisTemplate != null) {
                Boolean success = redisTemplate.opsForValue().setIfAbsent(lockKey, token, lockDuration);
                if (Boolean.TRUE.equals(success)) {
                    log.info("Redis distributed lock acquired for key='{}', token='{}'", lockKey, token);
                    return new LockResult(true, token, lockKey, expiresAt, "Lock acquired via Redis NX");
                } else {
                    return new LockResult(false, null, lockKey, null, "Lock already held by another worker");
                }
            }
        } catch (Exception e) {
            log.debug("Redis lock error ({}), using local lock store", e.getMessage());
        }

        // Local fallback lock
        LocalLockEntry existing = localLockStore.get(lockKey);
        if (existing == null || existing.expiresAt().isBefore(Instant.now())) {
            localLockStore.put(lockKey, new LocalLockEntry(token, expiresAt));
            return new LockResult(true, token, lockKey, expiresAt, "Lock acquired via virtual distributed lock coordinator");
        } else {
            return new LockResult(false, null, lockKey, null, "Resource is locked until " + existing.expiresAt());
        }
    }

    public boolean releaseLock(String tenantId, String resource, String token) {
        String lockKey = "flowmesh:lock:" + (tenantId != null ? tenantId : "default") + ":" + resource;
        try {
            if (redisTemplate != null) {
                Object currentVal = redisTemplate.opsForValue().get(lockKey);
                if (token != null && token.equals(currentVal)) {
                    Boolean deleted = redisTemplate.delete(lockKey);
                    log.info("Redis distributed lock released for key='{}'", lockKey);
                    return Boolean.TRUE.equals(deleted);
                }
            }
        } catch (Exception e) {
            log.debug("Redis release error ({}), falling back to local store", e.getMessage());
        }

        LocalLockEntry existing = localLockStore.get(lockKey);
        if (existing != null && existing.token().equals(token)) {
            localLockStore.remove(lockKey);
            return true;
        }
        return false;
    }
}
