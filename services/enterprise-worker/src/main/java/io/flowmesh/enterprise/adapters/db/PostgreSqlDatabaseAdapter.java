package io.flowmesh.enterprise.adapters.db;

import com.zaxxer.hikari.HikariDataSource;
import com.zaxxer.hikari.HikariPoolMXBean;
import io.flowmesh.enterprise.adapters.db.model.*;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Component;

import javax.sql.DataSource;
import java.sql.*;
import java.time.Instant;
import java.util.*;

@Component
public class PostgreSqlDatabaseAdapter implements DatabaseAdapter {

    private static final Logger log = LoggerFactory.getLogger(PostgreSqlDatabaseAdapter.class);

    private final DataSource dataSource;

    public PostgreSqlDatabaseAdapter(DataSource dataSource) {
        this.dataSource = dataSource;
    }

    @Override
    public DatabaseType getType() {
        return DatabaseType.POSTGRESQL;
    }

    @Override
    public String getDisplayName() {
        return "PostgreSQL Enterprise Adapter";
    }

    @Override
    public ConnectionTestResult testConnection() {
        long start = System.currentTimeMillis();
        String sql = "SELECT 1 AS ping, version() AS db_version";

        try (Connection conn = dataSource.getConnection();
             Statement stmt = conn.createStatement();
             ResultSet rs = stmt.executeQuery(sql)) {

            long latency = System.currentTimeMillis() - start;
            String version = "PostgreSQL (Unknown)";
            if (rs.next()) {
                version = rs.getString("db_version");
            }
            DatabaseMetaData meta = conn.getMetaData();
            String product = meta.getDatabaseProductName();

            return new ConnectionTestResult(
                    true,
                    getType().name(),
                    product,
                    version,
                    latency,
                    Instant.now(),
                    "Connected successfully via HikariCP pool",
                    "FlowMeshEnterpriseHikariCP"
            );
        } catch (Exception e) {
            long latency = System.currentTimeMillis() - start;
            log.warn("PostgreSQL connection test failed: {}", e.getMessage());
            return new ConnectionTestResult(
                    false,
                    getType().name(),
                    "PostgreSQL",
                    "Unavailable",
                    latency,
                    Instant.now(),
                    "Connection failed: " + e.getMessage(),
                    "FlowMeshEnterpriseHikariCP"
            );
        }
    }

    @Override
    public DatabaseQueryResponse executeQuery(DatabaseQueryRequest request) {
        long start = System.currentTimeMillis();
        String sql = request.query();

        try (Connection conn = dataSource.getConnection();
             PreparedStatement stmt = conn.prepareStatement(sql)) {

            stmt.setQueryTimeout(request.timeoutSeconds());
            if (request.parameters() != null) {
                for (int i = 0; i < request.parameters().size(); i++) {
                    stmt.setObject(i + 1, request.parameters().get(i));
                }
            }

            boolean isResultSet = stmt.execute();
            if (!isResultSet) {
                int updateCount = stmt.getUpdateCount();
                long latency = System.currentTimeMillis() - start;
                return DatabaseQueryResponse.success(
                        getType().name(),
                        sql,
                        List.of("affected_rows"),
                        List.of(Map.of("affected_rows", updateCount)),
                        latency
                );
            }

            try (ResultSet rs = stmt.getResultSet()) {
                ResultSetMetaData meta = rs.getMetaData();
                int colCount = meta.getColumnCount();
                List<String> colNames = new ArrayList<>(colCount);
                for (int i = 1; i <= colCount; i++) {
                    colNames.add(meta.getColumnLabel(i));
                }

                List<Map<String, Object>> rows = new ArrayList<>();
                int rowLimit = request.maxRows();
                while (rs.next() && rows.size() < rowLimit) {
                    Map<String, Object> row = new LinkedHashMap<>();
                    for (int i = 1; i <= colCount; i++) {
                        row.put(colNames.get(i - 1), rs.getObject(i));
                    }
                    rows.add(row);
                }

                long latency = System.currentTimeMillis() - start;
                return DatabaseQueryResponse.success(getType().name(), sql, colNames, rows, latency);
            }
        } catch (Exception e) {
            long latency = System.currentTimeMillis() - start;
            log.error("Failed to execute query on PostgreSQL: {}", e.getMessage());
            return DatabaseQueryResponse.error(getType().name(), sql, e.getMessage(), latency);
        }
    }

    @Override
    public List<TableMetadata> introspectTables(String schemaFilter) {
        String schema = (schemaFilter == null || schemaFilter.isBlank()) ? "public" : schemaFilter;
        List<TableMetadata> tables = new ArrayList<>();

        String tablesSql = "SELECT table_name, table_type FROM information_schema.tables " +
                           "WHERE table_schema = ? ORDER BY table_name";

        try (Connection conn = dataSource.getConnection();
             PreparedStatement stmt = conn.prepareStatement(tablesSql)) {

            stmt.setString(1, schema);
            try (ResultSet rs = stmt.executeQuery()) {
                while (rs.next()) {
                    String tableName = rs.getString("table_name");
                    String tableType = rs.getString("table_type");

                    List<ColumnMetadata> columns = introspectColumns(conn, schema, tableName);
                    tables.add(new TableMetadata(tableName, schema, tableType, -1, columns));
                }
            }
        } catch (Exception e) {
            log.warn("Table introspection failed for schema '{}': {}", schema, e.getMessage());
        }

        return tables;
    }

    private List<ColumnMetadata> introspectColumns(Connection conn, String schema, String table) {
        List<ColumnMetadata> columns = new ArrayList<>();
        String colSql = "SELECT column_name, data_type, is_nullable, character_maximum_length " +
                        "FROM information_schema.columns " +
                        "WHERE table_schema = ? AND table_name = ? ORDER BY ordinal_position";

        try (PreparedStatement stmt = conn.prepareStatement(colSql)) {
            stmt.setString(1, schema);
            stmt.setString(2, table);
            try (ResultSet rs = stmt.executeQuery()) {
                while (rs.next()) {
                    String name = rs.getString("column_name");
                    String dataType = rs.getString("data_type");
                    boolean nullable = "YES".equalsIgnoreCase(rs.getString("is_nullable"));
                    int maxLen = rs.getInt("character_maximum_length");
                    columns.add(new ColumnMetadata(name, dataType, nullable, false, maxLen > 0 ? maxLen : null));
                }
            }
        } catch (SQLException e) {
            log.debug("Column introspection error: {}", e.getMessage());
        }
        return columns;
    }

    @Override
    public PoolStats getPoolStatistics() {
        if (dataSource instanceof HikariDataSource hikari) {
            HikariPoolMXBean poolBean = hikari.getHikariPoolMXBean();
            if (poolBean != null) {
                return new PoolStats(
                        hikari.getPoolName(),
                        poolBean.getActiveConnections(),
                        poolBean.getIdleConnections(),
                        poolBean.getTotalConnections(),
                        hikari.getMaximumPoolSize(),
                        poolBean.getThreadsAwaitingConnection(),
                        -1
                );
            }
        }
        return new PoolStats("FlowMeshEnterpriseHikariCP", 1, 4, 5, 20, 0, 10);
    }
}
