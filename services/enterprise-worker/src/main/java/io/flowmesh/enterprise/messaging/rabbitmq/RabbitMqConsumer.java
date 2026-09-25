package io.flowmesh.enterprise.messaging.rabbitmq;

import io.flowmesh.enterprise.messaging.EnterpriseMessage;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.amqp.rabbit.annotation.RabbitListener;
import org.springframework.stereotype.Service;

import java.util.ArrayList;
import java.util.Deque;
import java.util.List;
import java.util.concurrent.ConcurrentLinkedDeque;
import java.util.concurrent.atomic.AtomicLong;

@Service
public class RabbitMqConsumer {

    private static final Logger log = LoggerFactory.getLogger(RabbitMqConsumer.class);

    private final Deque<EnterpriseMessage> receivedMessages = new ConcurrentLinkedDeque<>();
    private final AtomicLong consumedCount = new AtomicLong(0);

    @RabbitListener(
            queues = RabbitMqConfig.QUEUE_NAME,
            autoStartup = "${spring.rabbitmq.listener.simple.auto-startup:false}"
    )
    public void onMessage(EnterpriseMessage message) {
        log.info("Received message from RabbitMQ queue='{}', id='{}', tenant='{}'",
                RabbitMqConfig.QUEUE_NAME, message.messageId(), message.tenantId());
        recordMessage(message);
    }

    public void recordMessage(EnterpriseMessage message) {
        consumedCount.incrementAndGet();
        receivedMessages.addFirst(message);
        while (receivedMessages.size() > 50) {
            receivedMessages.pollLast();
        }
    }

    public List<EnterpriseMessage> getRecentReceived() {
        return new ArrayList<>(receivedMessages);
    }

    public long getConsumedCount() {
        return consumedCount.get();
    }
}
