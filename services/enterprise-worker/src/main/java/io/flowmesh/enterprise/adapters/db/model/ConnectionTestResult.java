package io.flowmesh.enterprise.adapters.db.model;

import java.time.Instant;

public record ConnectionTestResult(
        boolean successful,
        String databaseType,
        String databaseProduct,
        String databaseVersion,
        long latencyMs,
        Instant testedAt,
        String message,
        String activePool
) {}
