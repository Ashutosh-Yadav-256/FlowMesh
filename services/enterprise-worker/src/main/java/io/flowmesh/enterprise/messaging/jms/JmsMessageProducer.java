package io.flowmesh.enterprise.messaging.jms;

import io.flowmesh.enterprise.messaging.EnterpriseMessage;
import jakarta.jms.Message;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.jms.core.JmsTemplate;
import org.springframework.stereotype.Service;

import java.util.*;
import java.util.concurrent.ConcurrentLinkedDeque;
import java.util.concurrent.atomic.AtomicLong;

@Service
public class JmsMessageProducer {

    private static final Logger log = LoggerFactory.getLogger(JmsMessageProducer.class);

    private final JmsTemplate jmsTemplate;
    private final Deque<EnterpriseMessage> sentMessages = new ConcurrentLinkedDeque<>();
    private final AtomicLong sendCount = new AtomicLong(0);

    @Autowired(required = false)
    public JmsMessageProducer(JmsTemplate jmsTemplate) {
        this.jmsTemplate = jmsTemplate;
    }

    public boolean sendQueueMessage(EnterpriseMessage message) {
        return sendInternal(JmsConfig.QUEUE_NAME, message, false);
    }

    public boolean publishTopicMessage(EnterpriseMessage message) {
        return sendInternal(JmsConfig.TOPIC_NAME, message, true);
    }

    private boolean sendInternal(String destination, EnterpriseMessage message, boolean isTopic) {
        sendCount.incrementAndGet();
        sentMessages.addFirst(message);
        while (sentMessages.size() > 50) {
            sentMessages.pollLast();
        }

        try {
            if (jmsTemplate != null && jmsTemplate.getConnectionFactory() != null) {
                jmsTemplate.setPubSubDomain(isTopic);
                jmsTemplate.convertAndSend(destination, message, (Message jmsMsg) -> {
                    jmsMsg.setJMSCorrelationID(message.messageId());
                    jmsMsg.setStringProperty("X_Tenant_ID", message.tenantId());
                    jmsMsg.setStringProperty("X_Broker_Type", "JMS-2.0-Jakarta");
                    return jmsMsg;
                });
                log.info("JMS message sent to destination='{}', id='{}', isTopic={}",
                        destination, message.messageId(), isTopic);
                return true;
            }
        } catch (Exception e) {
            log.info("JMS broker offline ({}), message retained in local memory stream", e.getMessage());
        }

        return true;
    }

    public List<EnterpriseMessage> getSentMessages() {
        return new ArrayList<>(sentMessages);
    }

    public long getSendCount() {
        return sendCount.get();
    }
}
