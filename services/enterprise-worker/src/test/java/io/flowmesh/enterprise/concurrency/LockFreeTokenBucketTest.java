package io.flowmesh.enterprise.concurrency;

import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;

import java.util.concurrent.*;
import java.util.concurrent.atomic.AtomicInteger;

import static org.junit.jupiter.api.Assertions.*;

@DisplayName("Lock-Free Concurrency & CAS Rate Limiter Tests")
class LockFreeTokenBucketTest {

    @Test
    @DisplayName("Should enforce token bounds under high-contention concurrent access")
    void testConcurrentAccessUnderContention() throws InterruptedException {
        LockFreeTokenBucketRateLimiter rateLimiter = new LockFreeTokenBucketRateLimiter();
        String tenantId = "high-volume-tenant";

        int threadCount = 30;
        int requestsPerThread = 10;
        ExecutorService pool = Executors.newFixedThreadPool(threadCount);
        CountDownLatch startSignal = new CountDownLatch(1);
        CountDownLatch doneSignal = new CountDownLatch(threadCount);

        AtomicInteger acceptedCount = new AtomicInteger(0);
        AtomicInteger rejectedCount = new AtomicInteger(0);

        for (int i = 0; i < threadCount; i++) {
            pool.submit(() -> {
                try {
                    startSignal.await();
                    for (int j = 0; j < requestsPerThread; j++) {
                        if (rateLimiter.tryAcquire(tenantId, 1)) {
                            acceptedCount.incrementAndGet();
                        } else {
                            rejectedCount.incrementAndGet();
                        }
                    }
                } catch (InterruptedException e) {
                    Thread.currentThread().interrupt();
                } finally {
                    doneSignal.countDown();
                }
            });
        }

        startSignal.countDown();
        boolean completed = doneSignal.await(5, TimeUnit.SECONDS);
        pool.shutdown();

        assertTrue(completed, "All concurrent tasks should complete without deadlock");
        int totalRequests = acceptedCount.get() + rejectedCount.get();
        assertEquals(threadCount * requestsPerThread, totalRequests);

        assertTrue(acceptedCount.get() <= 105, "Accepted tokens should not exceed burst bucket capacity");
        assertTrue(rejectedCount.get() > 0, "Excess requests must be rejected under lock-free rate limiting");
    }
}
