package io.flowmesh.enterprise.controller;

import io.flowmesh.enterprise.concurrency.BatchReconciliationSummary;
import io.flowmesh.enterprise.concurrency.ConcurrentLedgerReconciliationService;
import io.flowmesh.enterprise.concurrency.LockFreeTokenBucketRateLimiter;
import io.flowmesh.enterprise.logging.LogExecutionTime;
import io.flowmesh.enterprise.model.EnterpriseTransaction;
import io.flowmesh.enterprise.service.TransactionProcessingService;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.math.BigDecimal;
import java.util.List;
import java.util.Map;
import java.util.concurrent.CompletableFuture;

@RestController
@RequestMapping("/api/v1/enterprise/transactions")
public class EnterpriseTransactionController {

    private static final Logger log = LoggerFactory.getLogger(EnterpriseTransactionController.class);

    private final TransactionProcessingService service;
    private final ConcurrentLedgerReconciliationService reconciliationService;
    private final LockFreeTokenBucketRateLimiter rateLimiter;

    public EnterpriseTransactionController(
            TransactionProcessingService service,
            ConcurrentLedgerReconciliationService reconciliationService,
            LockFreeTokenBucketRateLimiter rateLimiter) {
        this.service = service;
        this.reconciliationService = reconciliationService;
        this.rateLimiter = rateLimiter;
    }

    @PostMapping
    @LogExecutionTime(thresholdMs = 300, operation = "controller.recordTransaction")
    public ResponseEntity<?> recordTransaction(
            @RequestHeader(value = "X-Tenant-ID", defaultValue = "default_tenant") String tenantHeader,
            @RequestBody Map<String, Object> payload) {

        String tenantId = (String) payload.getOrDefault("tenant_id", tenantHeader);

        if (!rateLimiter.tryAcquire(tenantId, 1)) {
            log.warn("Rate limit exceeded for tenant='{}'", tenantId);
            return ResponseEntity.status(HttpStatus.TOO_MANY_REQUESTS)
                    .body(Map.of("error", "RATE_LIMIT_EXCEEDED", "tenantId", tenantId));
        }

        String ref = (String) payload.getOrDefault("reference", "REF-001");
        BigDecimal amount = new BigDecimal(payload.getOrDefault("amount", "0.0").toString());
        String currency = (String) payload.getOrDefault("currency", "USD");
        String src = (String) payload.getOrDefault("source_system", "REST_INGRESS");
        String tgt = (String) payload.getOrDefault("target_system", "ORACLE_LEDGER");

        EnterpriseTransaction created = service.processTransaction(tenantId, ref, amount, currency, src, tgt);
        return ResponseEntity.ok(created);
    }

    @GetMapping
    public ResponseEntity<List<EnterpriseTransaction>> listTransactions(
            @RequestHeader(value = "X-Tenant-ID", defaultValue = "default_tenant") String tenantId) {
        List<EnterpriseTransaction> list = service.getTenantTransactions(tenantId);
        return ResponseEntity.ok(list);
    }

    @PostMapping("/reconcile-batch")
    @LogExecutionTime(thresholdMs = 2500, operation = "controller.reconcileBatch")
    public CompletableFuture<ResponseEntity<BatchReconciliationSummary>> reconcileBatch(
            @RequestHeader(value = "X-Tenant-ID", defaultValue = "default_tenant") String tenantId,
            @RequestParam(defaultValue = "1500") long timeoutMs,
            @RequestBody(required = false) List<EnterpriseTransaction> customBatch) {

        List<EnterpriseTransaction> batch = (customBatch != null && !customBatch.isEmpty())
                ? customBatch
                : service.getTenantTransactions(tenantId);

        return reconciliationService.reconcileBatchAsync("BATCH-API", tenantId, batch, timeoutMs)
                .thenApply(ResponseEntity::ok);
    }
}
