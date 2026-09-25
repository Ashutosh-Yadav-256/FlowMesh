package io.flowmesh.enterprise.adapters.db;

import io.flowmesh.enterprise.adapters.db.model.*;

import java.util.List;

public interface DatabaseAdapter {

    DatabaseType getType();

    String getDisplayName();

    ConnectionTestResult testConnection();

    DatabaseQueryResponse executeQuery(DatabaseQueryRequest request);

    List<TableMetadata> introspectTables(String schemaFilter);

    PoolStats getPoolStatistics();
}
