package io.flowmesh.enterprise.messaging.jms;

import io.flowmesh.enterprise.messaging.EnterpriseMessage;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.jms.annotation.JmsListener;
import org.springframework.stereotype.Service;

import java.util.ArrayList;
import java.util.Deque;
import java.util.List;
import java.util.concurrent.ConcurrentLinkedDeque;
import java.util.concurrent.atomic.AtomicLong;

@Service
public class JmsMessageConsumer {

    private static final Logger log = LoggerFactory.getLogger(JmsMessageConsumer.class);

    private final Deque<EnterpriseMessage> receivedMessages = new ConcurrentLinkedDeque<>();
    private final AtomicLong receiveCount = new AtomicLong(0);

    @JmsListener(destination = JmsConfig.QUEUE_NAME)
    public void onMessage(EnterpriseMessage message) {
        log.info("Received JMS message from queue='{}', id='{}', tenant='{}'",
                JmsConfig.QUEUE_NAME, message.messageId(), message.tenantId());
        recordMessage(message);
    }

    public void recordMessage(EnterpriseMessage message) {
        receiveCount.incrementAndGet();
        receivedMessages.addFirst(message);
        while (receivedMessages.size() > 50) {
            receivedMessages.pollLast();
        }
    }

    public List<EnterpriseMessage> getReceivedMessages() {
        return new ArrayList<>(receivedMessages);
    }

    public long getReceiveCount() {
        return receiveCount.get();
    }
}
