package io.flowmesh.enterprise.messaging.jms.controller;

import io.flowmesh.enterprise.logging.LogExecutionTime;
import io.flowmesh.enterprise.messaging.EnterpriseMessage;
import io.flowmesh.enterprise.messaging.jms.JmsConfig;
import io.flowmesh.enterprise.messaging.jms.JmsMessageConsumer;
import io.flowmesh.enterprise.messaging.jms.JmsMessageProducer;
import jakarta.jms.Connection;
import jakarta.jms.ConnectionFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.*;

@RestController
@RequestMapping("/api/v1/enterprise/messaging/jms")
@CrossOrigin(origins = "*")
public class JmsController {

    private final JmsMessageProducer producer;
    private final JmsMessageConsumer consumer;
    private final ConnectionFactory connectionFactory;

    @Autowired
    public JmsController(
            JmsMessageProducer producer,
            JmsMessageConsumer consumer,
            @Autowired(required = false) ConnectionFactory connectionFactory) {
        this.producer = producer;
        this.consumer = consumer;
        this.connectionFactory = connectionFactory;
    }

    @PostMapping("/queue/send")
    @LogExecutionTime(thresholdMs = 200, operation = "jms.queue.send")
    public ResponseEntity<EnterpriseMessage> sendQueueMessage(@RequestBody Map<String, Object> body) {
        String tenantId = (String) body.getOrDefault("tenantId", "tenant_acme");
        Object payload = body.getOrDefault("payload", Map.of("transactionId", "TXN-JMS-1001", "action", "POST_LEDGER"));

        EnterpriseMessage message = EnterpriseMessage.of(
                tenantId,
                JmsConfig.QUEUE_NAME,
                "JMS-Queue-P2P",
                payload
        );

        producer.sendQueueMessage(message);
        // Also record to consumer for immediate testing feedback
        consumer.recordMessage(message);

        return ResponseEntity.ok(message);
    }

    @PostMapping("/topic/publish")
    @LogExecutionTime(thresholdMs = 200, operation = "jms.topic.publish")
    public ResponseEntity<EnterpriseMessage> publishTopicMessage(@RequestBody Map<String, Object> body) {
        String tenantId = (String) body.getOrDefault("tenantId", "tenant_acme");
        Object payload = body.getOrDefault("payload", Map.of("event", "ORDER_FULFILLED", "orderId", "ORD-8921"));

        EnterpriseMessage message = EnterpriseMessage.of(
                tenantId,
                JmsConfig.TOPIC_NAME,
                "JMS-Topic-PubSub",
                payload
        );

        producer.publishTopicMessage(message);
        consumer.recordMessage(message);

        return ResponseEntity.ok(message);
    }

    @GetMapping("/status")
    public ResponseEntity<Map<String, Object>> getStatus() {
        boolean brokerConnected = false;
        try {
            if (connectionFactory != null) {
                Connection conn = connectionFactory.createConnection();
                brokerConnected = (conn != null);
                if (conn != null) conn.close();
            }
        } catch (Exception ignored) {}

        Map<String, Object> status = new LinkedHashMap<>();
        status.put("brokerConnected", brokerConnected);
        status.put("brokerEngine", "Apache ActiveMQ Artemis (Jakarta JMS 3.1)");
        status.put("pointToPointQueue", JmsConfig.QUEUE_NAME);
        status.put("pubSubTopic", JmsConfig.TOPIC_NAME);
        status.put("totalSent", producer.getSendCount());
        status.put("totalReceived", consumer.getReceiveCount());

        return ResponseEntity.ok(status);
    }

    @GetMapping("/messages/recent")
    public ResponseEntity<Map<String, Object>> getRecentMessages() {
        Map<String, Object> result = new LinkedHashMap<>();
        result.put("sent", producer.getSentMessages());
        result.put("received", consumer.getReceivedMessages());
        return ResponseEntity.ok(result);
    }
}
