package io.flowmesh.enterprise.adapters.db.model;

public record PoolStats(
        String poolName,
        int activeConnections,
        int idleConnections,
        int totalConnections,
        int maxPoolSize,
        int threadsAwaitingConnection,
        long totalConnectionCreated
) {}
