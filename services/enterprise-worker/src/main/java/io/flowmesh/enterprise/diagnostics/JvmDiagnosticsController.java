package io.flowmesh.enterprise.diagnostics;

import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import java.util.LinkedHashMap;
import java.util.Map;

@RestController
@RequestMapping("/api/v1/enterprise/diagnostics")
public class JvmDiagnosticsController {

    private final JvmDiagnosticsService diagnosticsService;

    public JvmDiagnosticsController(JvmDiagnosticsService diagnosticsService) {
        this.diagnosticsService = diagnosticsService;
    }

    @GetMapping("/memory")
    public ResponseEntity<Map<String, Object>> getMemoryTelemetry() {
        return ResponseEntity.ok(diagnosticsService.getMemoryTelemetry());
    }

    @GetMapping("/gc")
    public ResponseEntity<Map<String, Object>> getGarbageCollectorTelemetry() {
        return ResponseEntity.ok(diagnosticsService.getGarbageCollectorTelemetry());
    }

    @GetMapping("/threads")
    public ResponseEntity<Map<String, Object>> getThreadTelemetry() {
        return ResponseEntity.ok(diagnosticsService.getThreadTelemetry());
    }

    @GetMapping("/health-summary")
    public ResponseEntity<Map<String, Object>> getHealthSummary() {
        Map<String, Object> summary = new LinkedHashMap<>();
        summary.put("status", "HEALTHY");
        summary.put("memory", diagnosticsService.getMemoryTelemetry());
        summary.put("gc", diagnosticsService.getGarbageCollectorTelemetry());
        summary.put("threads", diagnosticsService.getThreadTelemetry());
        return ResponseEntity.ok(summary);
    }
}
