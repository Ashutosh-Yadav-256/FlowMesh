package io.flowmesh.enterprise.messaging;

import io.flowmesh.enterprise.messaging.jms.JmsMessageConsumer;
import io.flowmesh.enterprise.messaging.jms.JmsMessageProducer;
import io.flowmesh.enterprise.messaging.rabbitmq.RabbitMqConsumer;
import io.flowmesh.enterprise.messaging.rabbitmq.RabbitMqProducer;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;

import java.util.Map;

import static org.junit.jupiter.api.Assertions.*;

@DisplayName("Enterprise Messaging (RabbitMQ & JMS) Tests")
class MessagingServiceTest {

    private RabbitMqProducer rabbitProducer;
    private RabbitMqConsumer rabbitConsumer;

    private JmsMessageProducer jmsProducer;
    private JmsMessageConsumer jmsConsumer;

    @BeforeEach
    void setUp() {
        rabbitProducer = new RabbitMqProducer(null);
        rabbitConsumer = new RabbitMqConsumer();

        jmsProducer = new JmsMessageProducer(null);
        jmsConsumer = new JmsMessageConsumer();
    }

    @Test
    @DisplayName("RabbitMQ producer and consumer should record message flow")
    void testRabbitMqMessaging() {
        EnterpriseMessage msg = EnterpriseMessage.of(
                "tenant_acme",
                "flowmesh.direct -> transaction.process",
                "RabbitMQ",
                Map.of("amount", 2500.0, "currency", "USD")
        );

        boolean sent = rabbitProducer.publish(msg, "transaction.process");
        assertTrue(sent);
        assertEquals(1, rabbitProducer.getPublishCount());
        assertFalse(rabbitProducer.getRecentDispatches().isEmpty());

        rabbitConsumer.recordMessage(msg);
        assertEquals(1, rabbitConsumer.getConsumedCount());
        assertEquals("tenant_acme", rabbitConsumer.getRecentReceived().get(0).tenantId());
    }

    @Test
    @DisplayName("JMS producer and consumer should record queue and topic flow")
    void testJmsMessaging() {
        EnterpriseMessage p2pMsg = EnterpriseMessage.of(
                "tenant_acme",
                "flowmesh.jms.queue",
                "JMS-Queue",
                Map.of("orderId", "ORD-12345")
        );

        boolean queueSent = jmsProducer.sendQueueMessage(p2pMsg);
        assertTrue(queueSent);

        EnterpriseMessage topicMsg = EnterpriseMessage.of(
                "tenant_prod",
                "flowmesh.jms.topic",
                "JMS-Topic",
                Map.of("event", "SYSTEM_ALERT")
        );
        boolean topicSent = jmsProducer.publishTopicMessage(topicMsg);
        assertTrue(topicSent);

        assertEquals(2, jmsProducer.getSendCount());

        jmsConsumer.recordMessage(p2pMsg);
        assertEquals(1, jmsConsumer.getReceiveCount());
        assertEquals("tenant_acme", jmsConsumer.getReceivedMessages().get(0).tenantId());
    }
}
