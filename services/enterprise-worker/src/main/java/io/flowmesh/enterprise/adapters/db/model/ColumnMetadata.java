package io.flowmesh.enterprise.adapters.db.model;

public record ColumnMetadata(
        String name,
        String dataType,
        boolean nullable,
        boolean primaryKey,
        Integer maxLength
) {}
