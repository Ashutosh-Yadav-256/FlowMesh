package io.flowmesh.enterprise.adapters.db.model;

import java.util.List;

public record TableMetadata(
        String tableName,
        String tableSchema,
        String tableType,
        long estimatedRowCount,
        List<ColumnMetadata> columns
) {}
