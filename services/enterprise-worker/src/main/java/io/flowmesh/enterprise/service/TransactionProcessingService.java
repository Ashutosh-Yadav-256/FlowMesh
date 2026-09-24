package io.flowmesh.enterprise.service;

import io.flowmesh.enterprise.concurrency.TenantConcurrencyStripingManager;
import io.flowmesh.enterprise.logging.AuditLoggingService;
import io.flowmesh.enterprise.logging.LogExecutionTime;
import io.flowmesh.enterprise.model.EnterpriseTransaction;
import io.flowmesh.enterprise.repository.EnterpriseTransactionRepository;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.kafka.annotation.KafkaListener;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.math.BigDecimal;
import java.util.List;
import java.util.Map;

@Service
public class TransactionProcessingService {

    private static final Logger log = LoggerFactory.getLogger(TransactionProcessingService.class);

    private final EnterpriseTransactionRepository repository;
    private final TenantConcurrencyStripingManager stripingManager;
    private final AuditLoggingService auditLoggingService;

    public TransactionProcessingService(
            EnterpriseTransactionRepository repository,
            TenantConcurrencyStripingManager stripingManager,
            AuditLoggingService auditLoggingService) {
        this.repository = repository;
        this.stripingManager = stripingManager;
        this.auditLoggingService = auditLoggingService;
    }

    @LogExecutionTime(thresholdMs = 250, operation = "transaction.process")
    public EnterpriseTransaction processTransaction(
            String tenantId,
            String reference,
            BigDecimal amount,
            String currency,
            String sourceSystem,
            String targetSystem) {

        try {
            return stripingManager.executeInTenantStripe(tenantId, () -> {
                log.info("Processing enterprise transaction ref='{}' tenant='{}' amount={} {}",
                        reference, tenantId, amount, currency);

                EnterpriseTransaction txn = new EnterpriseTransaction(
                    tenantId,
                    reference,
                    amount,
                    currency,
                    sourceSystem,
                    targetSystem,
                    "COMMITTED"
                );

                EnterpriseTransaction saved = persistTransaction(txn);

                auditLoggingService.recordAudit(
                    AuditLoggingService.AuditAction.TRANSACTION_CREATED,
                    "EnterpriseWorker",
                    reference,
                    AuditLoggingService.AuditOutcome.SUCCESS,
                    Map.of(
                        "amount", amount,
                        "currency", currency,
                        "source", sourceSystem,
                        "target", targetSystem
                    )
                );

                return saved;
            });
        } catch (Exception e) {
            log.error("Failed to process transaction ref='{}' tenant='{}'", reference, tenantId, e);
            throw new RuntimeException("Transaction processing error: " + e.getMessage(), e);
        }
    }

    @Transactional
    public EnterpriseTransaction persistTransaction(EnterpriseTransaction txn) {
        return repository.save(txn);
    }

    @Transactional(readOnly = true)
    @LogExecutionTime(thresholdMs = 100, operation = "transaction.listByTenant")
    public List<EnterpriseTransaction> getTenantTransactions(String tenantId) {
        return repository.findByTenantId(tenantId);
    }

    @KafkaListener(topics = "flowmesh.enterprise.events", groupId = "enterprise-worker-group", autoStartup = "false")
    public void onEnterpriseEvent(String eventPayload) {
        log.info("Received Kafka CloudEvent payload='{}'", eventPayload);
    }
}
