package io.flowmesh.enterprise.concurrency;

import java.io.Serializable;
import java.util.List;

public record BatchReconciliationSummary(
        String batchId,
        String tenantId,
        int totalTransactions,
        int matchedCount,
        int discrepancyCount,
        int failedCount,
        long totalDurationMs,
        double throughputPerSec,
        List<ReconciliationResult> results
) implements Serializable {
}
