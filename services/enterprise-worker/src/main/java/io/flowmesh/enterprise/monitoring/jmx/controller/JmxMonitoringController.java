package io.flowmesh.enterprise.monitoring.jmx.controller;

import io.flowmesh.enterprise.logging.LogExecutionTime;
import io.flowmesh.enterprise.monitoring.jmx.FlowMeshWorkerMonitor;
import io.flowmesh.enterprise.monitoring.jmx.JmxMonitoringService;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.lang.management.*;
import java.util.*;

@RestController
@RequestMapping("/api/v1/enterprise/monitoring/jmx")
@CrossOrigin(origins = "*")
public class JmxMonitoringController {

    private final JmxMonitoringService jmxService;

    public JmxMonitoringController(JmxMonitoringService jmxService) {
        this.jmxService = jmxService;
    }

    @GetMapping("/mbeans")
    public ResponseEntity<List<Map<String, Object>>> listMBeans(
            @RequestParam(required = false, defaultValue = "io.flowmesh") String domain) {
        return ResponseEntity.ok(jmxService.listMBeans(domain));
    }

    @GetMapping("/attributes")
    public ResponseEntity<Map<String, Object>> getWorkerAttributes() {
        return ResponseEntity.ok(jmxService.getAttributes(FlowMeshWorkerMonitor.MBEAN_NAME));
    }

    @PostMapping("/operations/{operation}")
    @LogExecutionTime(thresholdMs = 500, operation = "jmx.invokeOperation")
    public ResponseEntity<?> invokeOperation(@PathVariable String operation) {
        Object result = jmxService.invokeOperation(FlowMeshWorkerMonitor.MBEAN_NAME, operation, null, null);
        return ResponseEntity.ok(Map.of(
                "operation", operation,
                "status", "SUCCESS",
                "result", result != null ? result : "void"
        ));
    }

    @GetMapping("/jvm")
    public ResponseEntity<Map<String, Object>> getJvmTelemetry() {
        MemoryMXBean mem = ManagementFactory.getMemoryMXBean();
        ThreadMXBean threads = ManagementFactory.getThreadMXBean();
        RuntimeMXBean runtime = ManagementFactory.getRuntimeMXBean();
        OperatingSystemMXBean os = ManagementFactory.getOperatingSystemMXBean();

        Map<String, Object> data = new LinkedHashMap<>();
        data.put("jvmUptimeMs", runtime.getUptime());
        data.put("vmName", runtime.getVmName());
        data.put("vmVendor", runtime.getVmVendor());
        data.put("vmVersion", runtime.getVmVersion());

        data.put("heapUsedMB", mem.getHeapMemoryUsage().getUsed() / (1024 * 1024));
        data.put("heapMaxMB", mem.getHeapMemoryUsage().getMax() / (1024 * 1024));
        data.put("heapCommittedMB", mem.getHeapMemoryUsage().getCommitted() / (1024 * 1024));
        data.put("nonHeapUsedMB", mem.getNonHeapMemoryUsage().getUsed() / (1024 * 1024));

        data.put("activeThreadCount", threads.getThreadCount());
        data.put("peakThreadCount", threads.getPeakThreadCount());
        data.put("totalStartedThreadCount", threads.getTotalStartedThreadCount());

        data.put("availableProcessors", os.getAvailableProcessors());
        data.put("arch", os.getArch());
        data.put("osName", os.getName());

        return ResponseEntity.ok(data);
    }
}
