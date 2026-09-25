package io.flowmesh.enterprise.messaging.rabbitmq.controller;

import io.flowmesh.enterprise.logging.LogExecutionTime;
import io.flowmesh.enterprise.messaging.EnterpriseMessage;
import io.flowmesh.enterprise.messaging.rabbitmq.RabbitMqConfig;
import io.flowmesh.enterprise.messaging.rabbitmq.RabbitMqConsumer;
import io.flowmesh.enterprise.messaging.rabbitmq.RabbitMqProducer;
import org.springframework.amqp.rabbit.connection.ConnectionFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.*;

@RestController
@RequestMapping("/api/v1/enterprise/messaging/rabbitmq")
@CrossOrigin(origins = "*")
public class RabbitMqController {

    private final RabbitMqProducer producer;
    private final RabbitMqConsumer consumer;
    private final ConnectionFactory connectionFactory;

    @Autowired
    public RabbitMqController(
            RabbitMqProducer producer,
            RabbitMqConsumer consumer,
            @Autowired(required = false) ConnectionFactory connectionFactory) {
        this.producer = producer;
        this.consumer = consumer;
        this.connectionFactory = connectionFactory;
    }

    @PostMapping("/publish")
    @LogExecutionTime(thresholdMs = 200, operation = "rabbitmq.publish")
    public ResponseEntity<EnterpriseMessage> publishMessage(@RequestBody Map<String, Object> body) {
        String tenantId = (String) body.getOrDefault("tenantId", "tenant_acme");
        String routingKey = (String) body.getOrDefault("routingKey", RabbitMqConfig.ROUTING_KEY);
        Object payload = body.getOrDefault("payload", Map.of("action", "LEDGER_SYNC", "amount", 1000.0));

        EnterpriseMessage message = EnterpriseMessage.of(
                tenantId,
                RabbitMqConfig.EXCHANGE_NAME + " -> " + routingKey,
                "RabbitMQ-AMQP-0.9.1",
                payload
        );

        producer.publish(message, routingKey);
        // Also feed consumer buffer for immediate UI feedback in test/dev
        consumer.recordMessage(message);

        return ResponseEntity.ok(message);
    }

    @GetMapping("/status")
    public ResponseEntity<Map<String, Object>> getStatus() {
        boolean brokerConnected = false;
        try {
            if (connectionFactory != null) {
                var conn = connectionFactory.createConnection();
                brokerConnected = conn.isOpen();
                conn.close();
            }
        } catch (Exception ignored) {}

        Map<String, Object> status = new LinkedHashMap<>();
        status.put("brokerConnected", brokerConnected);
        status.put("brokerType", "RabbitMQ 3.13 (AMQP 0-9-1)");
        status.put("exchange", RabbitMqConfig.EXCHANGE_NAME);
        status.put("deadLetterExchange", RabbitMqConfig.DLX_NAME);
        status.put("queue", RabbitMqConfig.QUEUE_NAME);
        status.put("deadLetterQueue", RabbitMqConfig.DLQ_NAME);
        status.put("routingKey", RabbitMqConfig.ROUTING_KEY);
        status.put("totalPublished", producer.getPublishCount());
        status.put("totalConsumed", consumer.getConsumedCount());

        return ResponseEntity.ok(status);
    }

    @GetMapping("/messages/recent")
    public ResponseEntity<Map<String, Object>> getRecentMessages() {
        Map<String, Object> result = new LinkedHashMap<>();
        result.put("dispatched", producer.getRecentDispatches());
        result.put("received", consumer.getRecentReceived());
        return ResponseEntity.ok(result);
    }
}
