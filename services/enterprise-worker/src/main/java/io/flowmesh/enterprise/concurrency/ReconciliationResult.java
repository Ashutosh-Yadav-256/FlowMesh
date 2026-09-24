package io.flowmesh.enterprise.concurrency;

import java.io.Serializable;
import java.math.BigDecimal;
import java.time.Instant;

public record ReconciliationResult(
        String transactionId,
        String tenantId,
        String targetLedger,
        BigDecimal sourceAmount,
        BigDecimal targetAmount,
        boolean isReconciled,
        String status,
        long latencyMs,
        String remarks,
        Instant processedAt
) implements Serializable {

    public static ReconciliationResult matched(
            String txnId,
            String tenantId,
            String ledger,
            BigDecimal amount,
            long latencyMs) {
        return new ReconciliationResult(
                txnId,
                tenantId,
                ledger,
                amount,
                amount,
                true,
                "MATCHED",
                latencyMs,
                "Ledger verified with exact parity",
                Instant.now()
        );
    }

    public static ReconciliationResult discrepancy(
            String txnId,
            String tenantId,
            String ledger,
            BigDecimal srcAmount,
            BigDecimal tgtAmount,
            long latencyMs,
            String reason) {
        return new ReconciliationResult(
                txnId,
                tenantId,
                ledger,
                srcAmount,
                tgtAmount,
                false,
                "DISCREPANCY",
                latencyMs,
                reason,
                Instant.now()
        );
    }

    public static ReconciliationResult failed(
            String txnId,
            String tenantId,
            String ledger,
            BigDecimal amount,
            long latencyMs,
            String error) {
        return new ReconciliationResult(
                txnId,
                tenantId,
                ledger,
                amount,
                null,
                false,
                "FAILED",
                latencyMs,
                "Downstream error: " + error,
                Instant.now()
        );
    }
}
