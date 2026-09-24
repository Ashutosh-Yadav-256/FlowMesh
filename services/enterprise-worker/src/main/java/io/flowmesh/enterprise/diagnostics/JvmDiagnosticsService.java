package io.flowmesh.enterprise.diagnostics;

import org.springframework.stereotype.Service;

import java.lang.management.*;
import java.util.*;

@Service
public class JvmDiagnosticsService {

    private final MemoryMXBean memoryMXBean = ManagementFactory.getMemoryMXBean();
    private final ThreadMXBean threadMXBean = ManagementFactory.getThreadMXBean();
    private final List<GarbageCollectorMXBean> gcBeans = ManagementFactory.getGarbageCollectorMXBeans();
    private final List<MemoryPoolMXBean> poolBeans = ManagementFactory.getMemoryPoolMXBeans();

    public Map<String, Object> getMemoryTelemetry() {
        Map<String, Object> report = new LinkedHashMap<>();

        MemoryUsage heapUsage = memoryMXBean.getHeapMemoryUsage();
        Map<String, Object> heap = new LinkedHashMap<>();
        heap.put("initBytes", heapUsage.getInit());
        heap.put("usedBytes", heapUsage.getUsed());
        heap.put("committedBytes", heapUsage.getCommitted());
        heap.put("maxBytes", heapUsage.getMax());
        heap.put("usedMb", toMb(heapUsage.getUsed()));
        heap.put("maxMb", toMb(heapUsage.getMax()));
        heap.put("utilizationPercentage", calculatePercentage(heapUsage.getUsed(), heapUsage.getMax()));
        report.put("heap", heap);

        MemoryUsage nonHeapUsage = memoryMXBean.getNonHeapMemoryUsage();
        Map<String, Object> nonHeap = new LinkedHashMap<>();
        nonHeap.put("usedBytes", nonHeapUsage.getUsed());
        nonHeap.put("committedBytes", nonHeapUsage.getCommitted());
        nonHeap.put("usedMb", toMb(nonHeapUsage.getUsed()));
        report.put("nonHeap", nonHeap);

        Map<String, Object> pools = new LinkedHashMap<>();
        for (MemoryPoolMXBean pool : poolBeans) {
            MemoryUsage usage = pool.getUsage();
            Map<String, Object> poolDetail = new LinkedHashMap<>();
            poolDetail.put("type", pool.getType().name());
            poolDetail.put("usedMb", toMb(usage.getUsed()));
            poolDetail.put("committedMb", toMb(usage.getCommitted()));
            poolDetail.put("maxMb", toMb(usage.getMax()));
            poolDetail.put("peakUsedMb", toMb(pool.getPeakUsage().getUsed()));
            pools.put(pool.getName(), poolDetail);
        }
        report.put("memoryPools", pools);

        return report;
    }

    public Map<String, Object> getGarbageCollectorTelemetry() {
        Map<String, Object> report = new LinkedHashMap<>();
        List<Map<String, Object>> collectors = new ArrayList<>();

        long totalGcCount = 0;
        long totalGcTimeMs = 0;

        for (GarbageCollectorMXBean gcBean : gcBeans) {
            Map<String, Object> gc = new LinkedHashMap<>();
            long count = gcBean.getCollectionCount();
            long time = gcBean.getCollectionTime();

            gc.put("name", gcBean.getName());
            gc.put("collectionCount", count);
            gc.put("collectionTimeMs", time);
            gc.put("memoryPoolNames", gcBean.getMemoryPoolNames());
            gc.put("avgPauseTimeMs", count > 0 ? (double) time / count : 0.0);

            collectors.add(gc);
            totalGcCount += count;
            totalGcTimeMs += time;
        }

        report.put("collectors", collectors);
        report.put("totalCollections", totalGcCount);
        report.put("totalPauseDurationMs", totalGcTimeMs);
        report.put("vmVendor", System.getProperty("java.vm.vendor"));
        report.put("vmVersion", System.getProperty("java.vm.version"));

        return report;
    }

    public Map<String, Object> getThreadTelemetry() {
        Map<String, Object> report = new LinkedHashMap<>();
        report.put("threadCount", threadMXBean.getThreadCount());
        report.put("peakThreadCount", threadMXBean.getPeakThreadCount());
        report.put("totalStartedThreadCount", threadMXBean.getTotalStartedThreadCount());
        report.put("daemonThreadCount", threadMXBean.getDaemonThreadCount());
        report.put("isThreadContentionMonitoringSupported", threadMXBean.isThreadContentionMonitoringSupported());
        return report;
    }

    private static double toMb(long bytes) {
        if (bytes < 0) return -1.0;
        return Math.round((bytes / (1024.0 * 1024.0)) * 100.0) / 100.0;
    }

    private static double calculatePercentage(long used, long max) {
        if (max <= 0) return 0.0;
        return Math.round(((double) used / max) * 10000.0) / 100.0;
    }
}
