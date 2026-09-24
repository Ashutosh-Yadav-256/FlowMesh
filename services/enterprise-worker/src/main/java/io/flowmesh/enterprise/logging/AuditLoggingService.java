package io.flowmesh.enterprise.logging;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.slf4j.MDC;
import org.springframework.stereotype.Service;

import java.time.Instant;
import java.util.Map;

@Service
public class AuditLoggingService {

    private static final Logger auditLogger = LoggerFactory.getLogger("io.flowmesh.enterprise.audit");

    public enum AuditAction {
        TRANSACTION_CREATED,
        TRANSACTION_SETTLED,
        TRANSACTION_REVERTED,
        BATCH_RECONCILIATION_STARTED,
        BATCH_RECONCILIATION_COMPLETED,
        SECURITY_POLICY_EVALUATED,
        ACCESS_DENIED,
        TENANT_CONFIG_MUTATED
    }

    public enum AuditOutcome {
        SUCCESS,
        FAILURE,
        DENIED,
        ERROR
    }

    public void recordAudit(
            AuditAction action,
            String actor,
            String targetResource,
            AuditOutcome outcome,
            Map<String, Object> metadata) {

        String tenantId = MDC.get(MdcLoggingFilter.MDC_TENANT_ID);
        String traceId = MDC.get(MdcLoggingFilter.MDC_TRACE_ID);

        try {
            MDC.put("actor", actor != null ? actor : "system");
            MDC.put("auditAction", action.name());
            MDC.put("targetResource", targetResource);
            MDC.put("outcome", outcome.name());

            auditLogger.info(
                "AUDIT_RECORD action={} outcome={} actor={} resource={} tenant={} timestamp={} meta={}",
                action,
                outcome,
                actor,
                targetResource,
                tenantId != null ? tenantId : "system",
                Instant.now(),
                metadata
            );
        } finally {
            MDC.remove("actor");
            MDC.remove("auditAction");
            MDC.remove("targetResource");
            MDC.remove("outcome");
        }
    }
}
