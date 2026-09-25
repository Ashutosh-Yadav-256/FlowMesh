package io.flowmesh.enterprise.messaging.rabbitmq;

import io.flowmesh.enterprise.messaging.EnterpriseMessage;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.amqp.rabbit.core.RabbitTemplate;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

import java.util.*;
import java.util.concurrent.ConcurrentLinkedDeque;
import java.util.concurrent.atomic.AtomicLong;

@Service
public class RabbitMqProducer {

    private static final Logger log = LoggerFactory.getLogger(RabbitMqProducer.class);

    private final RabbitTemplate rabbitTemplate;
    private final Deque<EnterpriseMessage> recentDispatches = new ConcurrentLinkedDeque<>();
    private final AtomicLong publishCount = new AtomicLong(0);

    @Autowired(required = false)
    public RabbitMqProducer(RabbitTemplate rabbitTemplate) {
        this.rabbitTemplate = rabbitTemplate;
    }

    public boolean publish(EnterpriseMessage message, String routingKey) {
        String key = (routingKey != null && !routingKey.isBlank()) ? routingKey : RabbitMqConfig.ROUTING_KEY;
        publishCount.incrementAndGet();

        // Record in recent dispatches buffer
        recentDispatches.addFirst(message);
        while (recentDispatches.size() > 50) {
            recentDispatches.pollLast();
        }

        try {
            if (rabbitTemplate != null && rabbitTemplate.getConnectionFactory() != null) {
                rabbitTemplate.convertAndSend(RabbitMqConfig.EXCHANGE_NAME, key, message, m -> {
                    m.getMessageProperties().setCorrelationId(message.messageId());
                    m.getMessageProperties().setHeader("X-Tenant-ID", message.tenantId());
                    m.getMessageProperties().setHeader("X-Timestamp", message.timestamp().toString());
                    return m;
                });
                log.info("RabbitMQ message published to exchange='{}', routingKey='{}', id='{}'",
                        RabbitMqConfig.EXCHANGE_NAME, key, message.messageId());
                return true;
            }
        } catch (Exception e) {
            log.info("RabbitMQ broker offline ({}), message cached in local dispatch stream", e.getMessage());
        }

        return true;
    }

    public List<EnterpriseMessage> getRecentDispatches() {
        return new ArrayList<>(recentDispatches);
    }

    public long getPublishCount() {
        return publishCount.get();
    }
}
