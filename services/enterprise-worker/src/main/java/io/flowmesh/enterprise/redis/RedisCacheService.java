package io.flowmesh.enterprise.redis;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.data.redis.core.RedisTemplate;
import org.springframework.stereotype.Service;

import java.time.Duration;
import java.util.*;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.atomic.AtomicLong;

@Service
public class RedisCacheService {

    private static final Logger log = LoggerFactory.getLogger(RedisCacheService.class);

    private final RedisTemplate<String, Object> redisTemplate;
    private final Map<String, Object> fallbackCache = new ConcurrentHashMap<>();
    private final AtomicLong hitCount = new AtomicLong(0);
    private final AtomicLong missCount = new AtomicLong(0);

    @Autowired(required = false)
    public RedisCacheService(RedisTemplate<String, Object> redisTemplate) {
        this.redisTemplate = redisTemplate;
        // Pre-populate demo entries
        putFallback("tenant:tenant_acme:config", Map.of("currency", "USD", "rateLimit", 500, "region", "us-east-1"));
        putFallback("tenant:tenant_prod:config", Map.of("currency", "EUR", "rateLimit", 2000, "region", "eu-west-1"));
        putFallback("catalog:adapters:active", List.of("POSTGRESQL", "ORACLE", "SQL_SERVER"));
    }

    public void put(String key, Object value, Duration ttl) {
        try {
            if (redisTemplate != null) {
                if (ttl != null) {
                    redisTemplate.opsForValue().set(key, value, ttl);
                } else {
                    redisTemplate.opsForValue().set(key, value);
                }
                return;
            }
        } catch (Exception e) {
            log.debug("Redis unavailable, using local fallback cache: {}", e.getMessage());
        }
        putFallback(key, value);
    }

    public Object get(String key) {
        try {
            if (redisTemplate != null) {
                Object val = redisTemplate.opsForValue().get(key);
                if (val != null) {
                    hitCount.incrementAndGet();
                    return val;
                }
            }
        } catch (Exception e) {
            log.debug("Redis read exception: {}", e.getMessage());
        }

        Object local = fallbackCache.get(key);
        if (local != null) {
            hitCount.incrementAndGet();
            return local;
        } else {
            missCount.incrementAndGet();
            return null;
        }
    }

    public boolean evict(String key) {
        boolean evicted = false;
        try {
            if (redisTemplate != null) {
                Boolean res = redisTemplate.delete(key);
                evicted = Boolean.TRUE.equals(res);
            }
        } catch (Exception e) {
            log.debug("Redis evict error: {}", e.getMessage());
        }
        if (fallbackCache.remove(key) != null) {
            evicted = true;
        }
        return evicted;
    }

    public Set<String> getKeys(String pattern) {
        Set<String> keys = new HashSet<>();
        try {
            if (redisTemplate != null) {
                Set<String> rKeys = redisTemplate.keys(pattern != null ? pattern : "*");
                if (rKeys != null) keys.addAll(rKeys);
            }
        } catch (Exception e) {
            log.debug("Redis keys scan error: {}", e.getMessage());
        }
        keys.addAll(fallbackCache.keySet());
        return keys;
    }

    public Map<String, Object> getCacheStats() {
        long hits = hitCount.get();
        long misses = missCount.get();
        long total = hits + misses;
        double ratio = total > 0 ? (double) hits / total : 1.0;

        boolean liveConnected = false;
        try {
            if (redisTemplate != null && redisTemplate.getConnectionFactory() != null) {
                String ping = redisTemplate.getConnectionFactory().getConnection().ping();
                liveConnected = "PONG".equalsIgnoreCase(ping);
            }
        } catch (Exception ignored) {}

        Map<String, Object> stats = new LinkedHashMap<>();
        stats.put("connected", liveConnected);
        stats.put("mode", liveConnected ? "STANDALONE_REDIS_7" : "EMBEDDED_MEMORY_HYBRID");
        stats.put("hitCount", hits);
        stats.put("missCount", misses);
        stats.put("hitRatio", Math.round(ratio * 1000.0) / 1000.0);
        stats.put("totalCachedKeys", getKeys("*").size());
        stats.put("sampleKeys", getKeys("*").stream().limit(10).toList());
        return stats;
    }

    private void putFallback(String key, Object value) {
        fallbackCache.put(key, value);
    }
}
