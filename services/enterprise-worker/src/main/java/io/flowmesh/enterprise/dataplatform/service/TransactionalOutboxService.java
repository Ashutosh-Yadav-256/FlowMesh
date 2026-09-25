package io.flowmesh.enterprise.dataplatform.service;

import com.fasterxml.jackson.databind.ObjectMapper;
import io.flowmesh.enterprise.dataplatform.model.OutboxEvent;
import io.flowmesh.enterprise.dataplatform.repository.OutboxEventRepository;
import io.flowmesh.enterprise.messaging.EnterpriseMessage;
import io.flowmesh.enterprise.messaging.rabbitmq.RabbitMqProducer;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.data.domain.PageRequest;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.List;

@Service
public class TransactionalOutboxService {

    private static final Logger log = LoggerFactory.getLogger(TransactionalOutboxService.class);
    private static final ObjectMapper MAPPER = new ObjectMapper();

    private final OutboxEventRepository outboxRepository;
    private final RabbitMqProducer rabbitProducer;

    public TransactionalOutboxService(
            OutboxEventRepository outboxRepository,
            @Autowired(required = false) RabbitMqProducer rabbitProducer) {
        this.outboxRepository = outboxRepository;
        this.rabbitProducer = rabbitProducer;
    }

    @Transactional
    public OutboxEvent appendOutboxEvent(
            String tenantId,
            String aggregateType,
            String aggregateId,
            String eventType,
            Object payload) {

        String jsonPayload = "{}";
        try {
            jsonPayload = MAPPER.writeValueAsString(payload);
        } catch (Exception e) {
            log.warn("Failed to serialize outbox payload to JSON: {}", e.getMessage());
        }

        OutboxEvent event = new OutboxEvent(tenantId, aggregateType, aggregateId, eventType, jsonPayload);
        OutboxEvent saved = outboxRepository.save(event);
        log.info("Transactional Outbox event appended: id={}, type={}, aggregateId={}",
                saved.getId(), eventType, aggregateId);
        return saved;
    }

    @Transactional
    public int processPendingEvents(int batchSize) {
        List<OutboxEvent> pending = outboxRepository.findPendingEvents(PageRequest.of(0, Math.min(batchSize, 100)));
        if (pending.isEmpty()) {
            return 0;
        }

        int processed = 0;
        for (OutboxEvent event : pending) {
            try {
                if (rabbitProducer != null) {
                    EnterpriseMessage msg = EnterpriseMessage.of(
                            event.getTenantId(),
                            "flowmesh.cdc.outbox." + event.getAggregateType().toLowerCase(),
                            "RabbitMQ-Outbox-CDC",
                            event.getPayload()
                    );
                    rabbitProducer.publish(msg, "event.outbox");
                }
                event.markProcessed();
                outboxRepository.save(event);
                processed++;
            } catch (Exception e) {
                log.error("Failed to dispatch outbox event id={}: {}", event.getId(), e.getMessage());
                break;
            }
        }
        return processed;
    }

    public List<OutboxEvent> getPendingEvents(int limit) {
        return outboxRepository.findPendingEvents(PageRequest.of(0, Math.min(limit, 50)));
    }

    public long getPendingCount() {
        return outboxRepository.countByProcessedFalse();
    }
}
