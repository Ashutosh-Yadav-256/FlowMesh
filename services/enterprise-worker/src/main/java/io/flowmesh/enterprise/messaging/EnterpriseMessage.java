package io.flowmesh.enterprise.messaging;

import java.time.Instant;
import java.util.Map;
import java.util.UUID;

public record EnterpriseMessage(
        String messageId,
        String tenantId,
        String destination,
        String brokerType,
        Object payload,
        Map<String, Object> headers,
        Instant timestamp
) {
    public static EnterpriseMessage of(String tenantId, String destination, String brokerType, Object payload) {
        return new EnterpriseMessage(
                UUID.randomUUID().toString(),
                tenantId != null ? tenantId : "default_tenant",
                destination,
                brokerType,
                payload,
                Map.of("X-Trace-ID", UUID.randomUUID().toString(), "X-FlowMesh-Version", "2.4.0"),
                Instant.now()
        );
    }
}
