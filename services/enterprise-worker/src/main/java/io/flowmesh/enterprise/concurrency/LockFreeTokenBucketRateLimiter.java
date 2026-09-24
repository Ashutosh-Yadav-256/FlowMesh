package io.flowmesh.enterprise.concurrency;

import org.springframework.stereotype.Component;

import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.atomic.AtomicLong;

@Component
public class LockFreeTokenBucketRateLimiter {

    private final ConcurrentHashMap<String, AtomicBucketState> tenantBuckets = new ConcurrentHashMap<>();

    private static final long DEFAULT_CAPACITY = 100L;
    private static final long DEFAULT_REFILL_RATE_PER_SEC = 20L;

    public boolean tryAcquire(String tenantId, long permits) {
        AtomicBucketState bucket = tenantBuckets.computeIfAbsent(
                tenantId,
                id -> new AtomicBucketState(DEFAULT_CAPACITY, DEFAULT_REFILL_RATE_PER_SEC)
        );
        return bucket.tryConsume(permits);
    }

    static class AtomicBucketState {
        private final long capacity;
        private final long refillRatePerSec;
        
        private final AtomicLong availableTokens;
        private final AtomicLong lastRefillTimestampNanos;

        public AtomicBucketState(long capacity, long refillRatePerSec) {
            this.capacity = capacity;
            this.refillRatePerSec = refillRatePerSec;
            this.availableTokens = new AtomicLong(capacity);
            this.lastRefillTimestampNanos = new AtomicLong(System.nanoTime());
        }

        public boolean tryConsume(long tokensRequested) {
            if (tokensRequested <= 0) return true;

            while (true) {
                refillTokens();

                long current = availableTokens.get();
                if (current < tokensRequested) {
                    return false;
                }

                long updated = current - tokensRequested;
                if (availableTokens.compareAndSet(current, updated)) {
                    return true;
                }
            }
        }

        private void refillTokens() {
            long now = System.nanoTime();
            long lastRefill = lastRefillTimestampNanos.get();
            long elapsedNanos = now - lastRefill;

            if (elapsedNanos <= 0) return;

            long tokensToAdd = (elapsedNanos * refillRatePerSec) / 1_000_000_000L;

            if (tokensToAdd > 0) {
                if (lastRefillTimestampNanos.compareAndSet(lastRefill, now)) {
                    while (true) {
                        long current = availableTokens.get();
                        long updated = Math.min(capacity, current + tokensToAdd);
                        if (availableTokens.compareAndSet(current, updated)) {
                            break;
                        }
                    }
                }
            }
        }

        public long getAvailableTokens() {
            refillTokens();
            return availableTokens.get();
        }
    }
}
