package io.flowmesh.enterprise.adapters.db;

import io.flowmesh.enterprise.adapters.db.model.*;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.mockito.Mockito;

import javax.sql.DataSource;
import java.sql.Connection;
import java.sql.DatabaseMetaData;
import java.sql.ResultSet;
import java.sql.Statement;
import java.util.List;

import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.ArgumentMatchers.anyString;
import static org.mockito.Mockito.when;

@DisplayName("Database Adapters Verification (PostgreSQL, Oracle, SQL Server)")
class DatabaseAdaptersTest {

    private DataSource mockDataSource;
    private PostgreSqlDatabaseAdapter postgresAdapter;
    private OracleDatabaseAdapter oracleAdapter;
    private SqlServerDatabaseAdapter sqlServerAdapter;
    private DatabaseAdapterRegistry registry;

    @BeforeEach
    void setUp() throws Exception {
        mockDataSource = Mockito.mock(DataSource.class);
        Connection mockConn = Mockito.mock(Connection.class);
        Statement mockStmt = Mockito.mock(Statement.class);
        ResultSet mockRs = Mockito.mock(ResultSet.class);
        DatabaseMetaData mockMeta = Mockito.mock(DatabaseMetaData.class);

        when(mockDataSource.getConnection()).thenReturn(mockConn);
        when(mockConn.createStatement()).thenReturn(mockStmt);
        when(mockConn.getMetaData()).thenReturn(mockMeta);
        when(mockMeta.getDatabaseProductName()).thenReturn("PostgreSQL");
        when(mockStmt.executeQuery(anyString())).thenReturn(mockRs);
        when(mockRs.next()).thenReturn(true);
        when(mockRs.getString("db_version")).thenReturn("PostgreSQL 16.4 on x86_64");

        postgresAdapter = new PostgreSqlDatabaseAdapter(mockDataSource);
        oracleAdapter = new OracleDatabaseAdapter();
        sqlServerAdapter = new SqlServerDatabaseAdapter();

        registry = new DatabaseAdapterRegistry(List.of(postgresAdapter, oracleAdapter, sqlServerAdapter));
    }

    @Test
    @DisplayName("Registry should contain all 3 enterprise database adapters")
    void testRegistryPopulation() {
        assertEquals(3, registry.getAllAdapters().size());
        assertTrue(registry.hasAdapter(DatabaseType.POSTGRESQL));
        assertTrue(registry.hasAdapter(DatabaseType.ORACLE));
        assertTrue(registry.hasAdapter(DatabaseType.SQL_SERVER));
    }

    @Test
    @DisplayName("PostgreSQL adapter should test connection successfully")
    void testPostgreSqlConnectionTest() {
        ConnectionTestResult result = postgresAdapter.testConnection();
        assertNotNull(result);
        assertTrue(result.successful());
        assertEquals("POSTGRESQL", result.databaseType());
    }

    @Test
    @DisplayName("Oracle adapter should test connection and introspect ERP tables")
    void testOracleAdapter() {
        ConnectionTestResult result = oracleAdapter.testConnection();
        assertNotNull(result);
        assertTrue(result.successful());
        assertEquals("ORACLE", result.databaseType());

        List<TableMetadata> tables = oracleAdapter.introspectTables("FLOWMESH_ORCL");
        assertFalse(tables.isEmpty());
        assertTrue(tables.stream().anyMatch(t -> t.tableName().contains("ERP_TRANSACTIONS")));

        DatabaseQueryResponse queryRes = oracleAdapter.executeQuery(
                new DatabaseQueryRequest("SELECT 1 FROM DUAL", List.of(), 5, 10));
        assertNotNull(queryRes);
        assertEquals("SUCCESS", queryRes.status());
    }

    @Test
    @DisplayName("SQL Server adapter should test connection and introspect audit tables")
    void testSqlServerAdapter() {
        ConnectionTestResult result = sqlServerAdapter.testConnection();
        assertNotNull(result);
        assertTrue(result.successful());
        assertEquals("SQL_SERVER", result.databaseType());

        List<TableMetadata> tables = sqlServerAdapter.introspectTables("dbo");
        assertFalse(tables.isEmpty());
        assertTrue(tables.stream().anyMatch(t -> t.tableName().contains("EnterpriseAuditLogs")));

        DatabaseQueryResponse queryRes = sqlServerAdapter.executeQuery(
                new DatabaseQueryRequest("SELECT 1 AS Ping", List.of(), 5, 10));
        assertNotNull(queryRes);
        assertEquals("SUCCESS", queryRes.status());
    }
}
