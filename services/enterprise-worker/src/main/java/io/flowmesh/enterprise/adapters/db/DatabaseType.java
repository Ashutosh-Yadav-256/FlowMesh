package io.flowmesh.enterprise.adapters.db;

public enum DatabaseType {
    POSTGRESQL,
    ORACLE,
    SQL_SERVER;

    public static DatabaseType fromString(String value) {
        if (value == null) return POSTGRESQL;
        String normalized = value.trim().toUpperCase().replace("-", "_").replace(" ", "_");
        for (DatabaseType type : values()) {
            if (type.name().equals(normalized)) return type;
        }
        if (normalized.contains("POSTGRES")) return POSTGRESQL;
        if (normalized.contains("ORACLE")) return ORACLE;
        if (normalized.contains("SQL") && normalized.contains("SERVER") || normalized.contains("MSSQL")) return SQL_SERVER;
        throw new IllegalArgumentException("Unsupported DatabaseType: " + value);
    }
}
