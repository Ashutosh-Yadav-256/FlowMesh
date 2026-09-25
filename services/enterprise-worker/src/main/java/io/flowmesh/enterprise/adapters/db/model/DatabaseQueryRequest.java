package io.flowmesh.enterprise.adapters.db.model;

import java.util.List;

public record DatabaseQueryRequest(
        String query,
        List<Object> parameters,
        Integer timeoutSeconds,
        Integer maxRows
) {
    public DatabaseQueryRequest {
        if (timeoutSeconds == null || timeoutSeconds <= 0) {
            timeoutSeconds = 30;
        }
        if (maxRows == null || maxRows <= 0) {
            maxRows = 100;
        }
    }
}
