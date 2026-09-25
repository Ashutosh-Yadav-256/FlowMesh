package io.flowmesh.enterprise.adapters.db.model;

import java.time.Instant;
import java.util.List;
import java.util.Map;

public record DatabaseQueryResponse(
        String databaseType,
        String executedQuery,
        List<String> columnNames,
        List<Map<String, Object>> rows,
        int rowCount,
        long executionTimeMs,
        Instant executedAt,
        String status,
        String errorMessage
) {
    public static DatabaseQueryResponse success(
            String databaseType,
            String query,
            List<String> columnNames,
            List<Map<String, Object>> rows,
            long executionTimeMs) {
        return new DatabaseQueryResponse(
                databaseType,
                query,
                columnNames,
                rows,
                rows != null ? rows.size() : 0,
                executionTimeMs,
                Instant.now(),
                "SUCCESS",
                null
        );
    }

    public static DatabaseQueryResponse error(
            String databaseType,
            String query,
            String errorMessage,
            long executionTimeMs) {
        return new DatabaseQueryResponse(
                databaseType,
                query,
                List.of(),
                List.of(),
                0,
                executionTimeMs,
                Instant.now(),
                "ERROR",
                errorMessage
        );
    }
}
