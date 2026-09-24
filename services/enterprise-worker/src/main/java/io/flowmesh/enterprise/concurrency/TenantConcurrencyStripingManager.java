package io.flowmesh.enterprise.concurrency;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Component;

import java.util.concurrent.Callable;
import java.util.concurrent.locks.ReentrantLock;

@Component
public class TenantConcurrencyStripingManager {

    private static final Logger log = LoggerFactory.getLogger(TenantConcurrencyStripingManager.class);

    private static final int STRIPE_COUNT = 64;
    private static final int STRIPE_MASK = STRIPE_COUNT - 1;

    private final ReentrantLock[] lockStripes;

    public TenantConcurrencyStripingManager() {
        this.lockStripes = new ReentrantLock[STRIPE_COUNT];
        for (int i = 0; i < STRIPE_COUNT; i++) {
            this.lockStripes[i] = new ReentrantLock(false);
        }
    }

    public <T> T executeInTenantStripe(String partitionKey, Callable<T> task) throws Exception {
        int stripeIndex = resolveStripeIndex(partitionKey);
        ReentrantLock lock = lockStripes[stripeIndex];

        lock.lock();
        try {
            log.debug("Acquired concurrency stripe index={} for key='{}'", stripeIndex, partitionKey);
            return task.call();
        } finally {
            lock.unlock();
            log.debug("Released concurrency stripe index={} for key='{}'", stripeIndex, partitionKey);
        }
    }

    private int resolveStripeIndex(String key) {
        if (key == null) return 0;
        int h = key.hashCode();
        h ^= (h >>> 16);
        return Math.abs(h & STRIPE_MASK);
    }
}
