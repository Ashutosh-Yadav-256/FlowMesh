package io.flowmesh.enterprise.monitoring.jmx;

public interface FlowMeshWorkerMonitorMBean {

    int getActiveTenantCount();

    long getProcessedTransactions();

    long getFailedTransactions();

    double getAverageLatencyMs();

    double getCacheHitRatio();

    int getDatabaseActiveConnections();

    long getRabbitMqDispatchedMessages();

    long getJmsSentMessages();

    String getDeploymentMode();

    String getJvmUptime();

    long getFreeMemoryBytes();

    long getTotalMemoryBytes();

    void resetCounters();

    void evictAllCaches();

    void triggerGarbageCollection();

    String runHealthCheck();
}
