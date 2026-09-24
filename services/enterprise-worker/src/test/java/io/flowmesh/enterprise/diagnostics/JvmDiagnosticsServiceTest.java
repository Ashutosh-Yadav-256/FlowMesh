package io.flowmesh.enterprise.diagnostics;

import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;

import java.util.List;
import java.util.Map;

import static org.junit.jupiter.api.Assertions.*;

@DisplayName("JVM Memory & GC Diagnostics Telemetry Tests")
class JvmDiagnosticsServiceTest {

    private final JvmDiagnosticsService service = new JvmDiagnosticsService();

    @Test
    @DisplayName("Should retrieve live heap and non-heap memory telemetry")
    void testGetMemoryTelemetry() {
        Map<String, Object> memory = service.getMemoryTelemetry();

        assertNotNull(memory);
        assertTrue(memory.containsKey("heap"));
        assertTrue(memory.containsKey("nonHeap"));
        assertTrue(memory.containsKey("memoryPools"));

        @SuppressWarnings("unchecked")
        Map<String, Object> heap = (Map<String, Object>) memory.get("heap");
        assertNotNull(heap.get("usedBytes"));
        assertNotNull(heap.get("maxBytes"));
        assertTrue((Long) heap.get("usedBytes") > 0);
    }

    @Test
    @DisplayName("Should retrieve active garbage collector metrics")
    void testGetGarbageCollectorTelemetry() {
        Map<String, Object> gc = service.getGarbageCollectorTelemetry();

        assertNotNull(gc);
        assertTrue(gc.containsKey("collectors"));
        assertTrue(gc.containsKey("totalCollections"));
        assertTrue(gc.containsKey("vmVendor"));

        @SuppressWarnings("unchecked")
        List<Map<String, Object>> collectors = (List<Map<String, Object>>) gc.get("collectors");
        assertFalse(collectors.isEmpty(), "At least one garbage collector must be registered in the JVM");
    }

    @Test
    @DisplayName("Should retrieve active thread telemetry")
    void testGetThreadTelemetry() {
        Map<String, Object> threads = service.getThreadTelemetry();

        assertNotNull(threads);
        assertTrue(threads.containsKey("threadCount"));
        assertTrue((Integer) threads.get("threadCount") > 0);
    }
}
