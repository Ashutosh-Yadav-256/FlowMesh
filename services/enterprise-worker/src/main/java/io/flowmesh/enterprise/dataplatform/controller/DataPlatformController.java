package io.flowmesh.enterprise.dataplatform.controller;

import io.flowmesh.enterprise.dataplatform.model.OutboxEvent;
import io.flowmesh.enterprise.dataplatform.schema.DataPlatformSchemaEngine;
import io.flowmesh.enterprise.dataplatform.service.TransactionalOutboxService;
import io.flowmesh.enterprise.logging.LogExecutionTime;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.*;

@RestController
@RequestMapping("/api/v1/enterprise/dataplatform")
@CrossOrigin(origins = "*")
public class DataPlatformController {

    private final TransactionalOutboxService outboxService;
    private final DataPlatformSchemaEngine schemaEngine;

    public DataPlatformController(
            TransactionalOutboxService outboxService,
            DataPlatformSchemaEngine schemaEngine) {
        this.outboxService = outboxService;
        this.schemaEngine = schemaEngine;
    }

    @GetMapping("/outbox/pending")
    public ResponseEntity<Map<String, Object>> getPendingOutboxEvents(
            @RequestParam(defaultValue = "20") int limit) {
        List<OutboxEvent> events = outboxService.getPendingEvents(limit);
        long count = outboxService.getPendingCount();
        return ResponseEntity.ok(Map.of(
                "pendingCount", count,
                "events", events
        ));
    }

    @PostMapping("/outbox/process")
    @LogExecutionTime(thresholdMs = 500, operation = "dataplatform.outbox.process")
    public ResponseEntity<Map<String, Object>> processOutbox(
            @RequestParam(defaultValue = "25") int batchSize) {
        int processed = outboxService.processPendingEvents(batchSize);
        return ResponseEntity.ok(Map.of(
                "processedEvents", processed,
                "remainingPending", outboxService.getPendingCount()
        ));
    }

    @PostMapping("/contracts/validate")
    public ResponseEntity<DataPlatformSchemaEngine.ContractValidationResult> validateContract(
            @RequestBody Map<String, Object> body) {
        @SuppressWarnings("unchecked")
        Map<String, String> contract = (Map<String, String>) body.getOrDefault("contract", Map.of());
        @SuppressWarnings("unchecked")
        Map<String, Object> payload = (Map<String, Object>) body.getOrDefault("payload", Map.of());

        return ResponseEntity.ok(schemaEngine.validateContract(contract, payload));
    }

    @PostMapping("/contracts/drift")
    public ResponseEntity<DataPlatformSchemaEngine.SchemaDriftReport> detectSchemaDrift(
            @RequestBody Map<String, Object> body) {
        @SuppressWarnings("unchecked")
        Map<String, String> baseline = (Map<String, String>) body.getOrDefault("baseline", Map.of());
        @SuppressWarnings("unchecked")
        Map<String, String> incoming = (Map<String, String>) body.getOrDefault("incoming", Map.of());

        return ResponseEntity.ok(schemaEngine.detectDrift(baseline, incoming));
    }
}
