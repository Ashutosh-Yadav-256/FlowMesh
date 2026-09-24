package io.flowmesh.enterprise.concurrency;

import io.flowmesh.enterprise.logging.AuditLoggingService;
import io.flowmesh.enterprise.model.EnterpriseTransaction;
import org.junit.jupiter.api.AfterEach;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.mockito.Mockito;

import java.math.BigDecimal;
import java.util.ArrayList;
import java.util.List;
import java.util.concurrent.*;

import static org.junit.jupiter.api.Assertions.*;

@DisplayName("Java Concurrency & Scatter-Gather Reconciliation Tests")
class ConcurrentReconciliationTest {

    private ExecutorService testExecutor;
    private ConcurrentLedgerReconciliationService service;
    private AuditLoggingService mockAuditService;

    @BeforeEach
    void setUp() {
        testExecutor = Executors.newFixedThreadPool(8);
        mockAuditService = Mockito.mock(AuditLoggingService.class);
        service = new ConcurrentLedgerReconciliationService(testExecutor, mockAuditService);
    }

    @AfterEach
    void tearDown() {
        testExecutor.shutdownNow();
    }

    @Test
    @DisplayName("Should scatter-gather parallel reconciliation across transactions")
    void testParallelBatchReconciliation() throws Exception {
        int transactionCount = 20;
        List<EnterpriseTransaction> txns = new ArrayList<>();
        for (int i = 0; i < transactionCount; i++) {
            EnterpriseTransaction txn = new EnterpriseTransaction(
                    "tenant-fintech",
                    "REF-" + i,
                    new BigDecimal("100.50"),
                    "USD",
                    "STRIPE",
                    "ORACLE_ERP",
                    "COMMITTED"
            );
            txns.add(txn);
        }

        CompletableFuture<BatchReconciliationSummary> future =
                service.reconcileBatchAsync("BATCH-TEST-001", "tenant-fintech", txns, 1000);

        BatchReconciliationSummary summary = future.get(5, TimeUnit.SECONDS);

        assertNotNull(summary);
        assertEquals("BATCH-TEST-001", summary.batchId());
        assertEquals(20, summary.totalTransactions());
        assertEquals(20, summary.matchedCount());
        assertEquals(0, summary.discrepancyCount());
        assertEquals(0, summary.failedCount());
        assertTrue(summary.totalDurationMs() >= 0);
        assertTrue(summary.throughputPerSec() >= 0);
    }

    @Test
    @DisplayName("Should gracefully handle downstream ledger timeouts without cascading failure")
    void testTimeoutHandling() throws Exception {
        EnterpriseTransaction slowTxn = new EnterpriseTransaction(
                "tenant-slow",
                "REF-TIMEOUT",
                new BigDecimal("5000.00"),
                "EUR",
                "SWIFT",
                "LEGACY_MAINFRAME",
                "PENDING"
        );

        CompletableFuture<ReconciliationResult> future =
                service.reconcileSingleTransactionAsync(slowTxn, 1, null);

        ReconciliationResult result = future.get(2, TimeUnit.SECONDS);

        assertNotNull(result);
        assertEquals("FAILED", result.status());
        assertFalse(result.isReconciled());
        assertTrue(result.remarks().contains("timeout"), "Remarks should identify downstream timeout");
    }
}
