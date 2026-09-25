package io.flowmesh.enterprise.dataplatform;

import io.flowmesh.enterprise.dataplatform.model.OutboxEvent;
import io.flowmesh.enterprise.dataplatform.repository.OutboxEventRepository;
import io.flowmesh.enterprise.dataplatform.service.TransactionalOutboxService;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.orm.jpa.DataJpaTest;
import org.springframework.boot.test.autoconfigure.orm.jpa.TestEntityManager;
import org.springframework.context.annotation.Import;
import org.springframework.test.context.ActiveProfiles;

import java.util.List;
import java.util.Map;

import static org.junit.jupiter.api.Assertions.*;

@DataJpaTest
@Import(TransactionalOutboxService.class)
@ActiveProfiles("test")
@DisplayName("Data Platform Engineering: Transactional Outbox Pattern TDD Suite")
class TransactionalOutboxTest {

    @Autowired
    private TestEntityManager entityManager;

    @Autowired
    private OutboxEventRepository outboxRepository;

    @Autowired
    private TransactionalOutboxService outboxService;

    @Test
    @DisplayName("TDD: Should atomically append OutboxEvent and transition status upon dispatch")
    void testOutboxLifecycle() {
        OutboxEvent event = outboxService.appendOutboxEvent(
                "tenant_acme",
                "TRANSACTION",
                "REF-OUTBOX-991",
                "TRANSACTION_COMMITTED",
                Map.of("amount", 5000.0, "currency", "USD")
        );

        entityManager.flush();
        assertNotNull(event.getId());
        assertFalse(event.isProcessed());
        assertEquals(1, outboxService.getPendingCount());

        // Process pending events
        int processedCount = outboxService.processPendingEvents(10);
        entityManager.flush();
        entityManager.clear();

        assertEquals(1, processedCount);
        assertEquals(0, outboxService.getPendingCount());

        OutboxEvent dispatched = outboxRepository.findById(event.getId()).orElseThrow();
        assertTrue(dispatched.isProcessed());
        assertNotNull(dispatched.getProcessedAt());
    }
}
