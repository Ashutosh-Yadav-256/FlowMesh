package io.flowmesh.enterprise.concurrency;

import io.flowmesh.enterprise.logging.AuditLoggingService;
import io.flowmesh.enterprise.logging.LogExecutionTime;
import io.flowmesh.enterprise.logging.MdcLoggingFilter;
import io.flowmesh.enterprise.model.EnterpriseTransaction;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.slf4j.MDC;
import org.springframework.beans.factory.annotation.Qualifier;
import org.springframework.stereotype.Service;

import java.math.BigDecimal;
import java.util.ArrayList;
import java.util.Collections;
import java.util.List;
import java.util.Map;
import java.util.UUID;
import java.util.concurrent.*;
import java.util.concurrent.atomic.AtomicInteger;
import java.util.concurrent.atomic.LongAdder;

@Service
public class ConcurrentLedgerReconciliationService {

    private static final Logger log = LoggerFactory.getLogger(ConcurrentLedgerReconciliationService.class);

    private final Executor reconciliationExecutor;
    private final AuditLoggingService auditLoggingService;

    public ConcurrentLedgerReconciliationService(
            @Qualifier("reconciliationExecutor") Executor reconciliationExecutor,
            AuditLoggingService auditLoggingService) {
        this.reconciliationExecutor = reconciliationExecutor;
        this.auditLoggingService = auditLoggingService;
    }

    @LogExecutionTime(thresholdMs = 2000, operation = "reconciliation.scatterGatherBatch")
    public CompletableFuture<BatchReconciliationSummary> reconcileBatchAsync(
            String batchId,
            String tenantId,
            List<EnterpriseTransaction> transactions,
            long perTaskTimeoutMs) {

        long startTimeNanos = System.nanoTime();
        final String effectiveBatchId = (batchId != null) ? batchId : "BATCH-" + UUID.randomUUID().toString().substring(0, 8);
        
        final Map<String, String> parentMdcContext = MDC.getCopyOfContextMap();

        log.info("Initiating concurrent batch reconciliation batchId={} tenantId={} itemCount={}",
                effectiveBatchId, tenantId, transactions.size());

        LongAdder matchedCounter = new LongAdder();
        LongAdder discrepancyCounter = new LongAdder();
        LongAdder failedCounter = new LongAdder();
        List<ReconciliationResult> results = Collections.synchronizedList(new ArrayList<>(transactions.size()));

        List<CompletableFuture<Void>> futures = transactions.stream()
                .map(txn -> reconcileSingleTransactionAsync(txn, perTaskTimeoutMs, parentMdcContext)
                        .thenAccept(result -> {
                            results.add(result);
                            if ("MATCHED".equals(result.status())) {
                                matchedCounter.increment();
                            } else if ("DISCREPANCY".equals(result.status())) {
                                discrepancyCounter.increment();
                            } else {
                                failedCounter.increment();
                            }
                        }))
                .toList();

        CompletableFuture<Void> allOfFuture = CompletableFuture.allOf(futures.toArray(new CompletableFuture[0]));

        return allOfFuture.thenApply(v -> {
            long durationMillis = (System.nanoTime() - startTimeNanos) / 1_000_000;
            double throughput = (transactions.isEmpty() || durationMillis == 0)
                    ? 0.0
                    : (transactions.size() * 1000.0) / durationMillis;

            BatchReconciliationSummary summary = new BatchReconciliationSummary(
                    effectiveBatchId,
                    tenantId,
                    transactions.size(),
                    matchedCounter.intValue(),
                    discrepancyCounter.intValue(),
                    failedCounter.intValue(),
                    durationMillis,
                    Math.round(throughput * 100.0) / 100.0,
                    new ArrayList<>(results)
            );

            log.info("Completed concurrent batch reconciliation batchId={} durationMs={} throughput={}/sec matched={} failed={}",
                    effectiveBatchId, durationMillis, summary.throughputPerSec(), summary.matchedCount(), summary.failedCount());

            auditLoggingService.recordAudit(
                    AuditLoggingService.AuditAction.BATCH_RECONCILIATION_COMPLETED,
                    "ReconciliationEngine",
                    effectiveBatchId,
                    AuditLoggingService.AuditOutcome.SUCCESS,
                    Map.of(
                            "total", transactions.size(),
                            "matched", summary.matchedCount(),
                            "durationMs", durationMillis
                    )
            );

            return summary;
        });
    }

    public CompletableFuture<ReconciliationResult> reconcileSingleTransactionAsync(
            EnterpriseTransaction txn,
            long timeoutMs,
            Map<String, String> mdcContext) {

        return CompletableFuture.supplyAsync(() -> {
            long taskStartNanos = System.nanoTime();
            if (mdcContext != null) {
                MDC.setContextMap(mdcContext);
            }

            try {
                return executeRemoteLedgerVerification(txn, taskStartNanos);
            } finally {
                MDC.clear();
            }
        }, reconciliationExecutor)
        .orTimeout(timeoutMs, TimeUnit.MILLISECONDS)
        .exceptionally(throwable -> {
            long elapsedMs = 0;
            String errorMessage = (throwable instanceof TimeoutException) 
                    ? "Target ledger timeout (" + timeoutMs + "ms breached)"
                    : throwable.getMessage();

            log.error("Reconciliation RPC failed for txnId={} target={} error={}",
                    txn.getId(), txn.getTargetSystem(), errorMessage);

            return ReconciliationResult.failed(
                    txn.getId() != null ? txn.getId().toString() : "N/A",
                    txn.getTenantId(),
                    txn.getTargetSystem(),
                    txn.getAmount(),
                    elapsedMs,
                    errorMessage
            );
        });
    }

    private ReconciliationResult executeRemoteLedgerVerification(EnterpriseTransaction txn, long startNanos) {
        String txnId = txn.getId() != null ? txn.getId().toString() : UUID.randomUUID().toString();
        BigDecimal sourceAmount = txn.getAmount() != null ? txn.getAmount() : BigDecimal.ZERO;

        try {
            Thread.sleep(15);
        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
            throw new CompletionException(e);
        }

        long latencyMs = (System.nanoTime() - startNanos) / 1_000_000;

        return ReconciliationResult.matched(
                txnId,
                txn.getTenantId(),
                txn.getTargetSystem() != null ? txn.getTargetSystem() : "INTERNAL_LEDGER",
                sourceAmount,
                latencyMs
        );
    }
}
