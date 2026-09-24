package io.flowmesh.enterprise.concurrency;

import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;

import java.util.concurrent.*;
import java.util.concurrent.atomic.AtomicInteger;

import static org.junit.jupiter.api.Assertions.*;

@DisplayName("Tenant Concurrency Striped Locking Tests")
class TenantConcurrencyStripingTest {

    @Test
    @DisplayName("Should serialize operations for the identical partition key while running distinct partitions in parallel")
    void testTenantStripedSerialization() throws Exception {
        TenantConcurrencyStripingManager manager = new TenantConcurrencyStripingManager();
        String sameTenant = "tenant-fintech-alpha";

        ExecutorService executor = Executors.newFixedThreadPool(4);
        AtomicInteger concurrentExecutionCounter = new AtomicInteger(0);
        AtomicInteger maxObservedConcurrencySameTenant = new AtomicInteger(0);

        CountDownLatch latch = new CountDownLatch(5);

        for (int i = 0; i < 5; i++) {
            executor.submit(() -> {
                try {
                    manager.executeInTenantStripe(sameTenant, () -> {
                        int active = concurrentExecutionCounter.incrementAndGet();
                        maxObservedConcurrencySameTenant.updateAndGet(current -> Math.max(current, active));
                        Thread.sleep(20);
                        concurrentExecutionCounter.decrementAndGet();
                        return "OK";
                    });
                } catch (Exception e) {
                    fail("Stripe execution failed: " + e.getMessage());
                } finally {
                    latch.countDown();
                }
            });
        }

        assertTrue(latch.await(3, TimeUnit.SECONDS));
        executor.shutdown();

        assertEquals(1, maxObservedConcurrencySameTenant.get(),
                "Stripe lock must strictly serialize execution for the identical tenant key");
    }
}
