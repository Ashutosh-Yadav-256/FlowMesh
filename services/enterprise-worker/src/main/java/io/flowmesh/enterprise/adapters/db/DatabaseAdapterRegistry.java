package io.flowmesh.enterprise.adapters.db;

import io.flowmesh.enterprise.adapters.db.model.ConnectionTestResult;
import org.springframework.stereotype.Service;

import java.util.*;

@Service
public class DatabaseAdapterRegistry {

    private final Map<DatabaseType, DatabaseAdapter> adapters = new EnumMap<>(DatabaseType.class);

    public DatabaseAdapterRegistry(List<DatabaseAdapter> adapterList) {
        for (DatabaseAdapter adapter : adapterList) {
            adapters.put(adapter.getType(), adapter);
        }
    }

    public DatabaseAdapter getAdapter(DatabaseType type) {
        DatabaseAdapter adapter = adapters.get(type);
        if (adapter == null) {
            throw new IllegalArgumentException("No database adapter registered for type: " + type);
        }
        return adapter;
    }

    public Collection<DatabaseAdapter> getAllAdapters() {
        return Collections.unmodifiableCollection(adapters.values());
    }

    public boolean hasAdapter(DatabaseType type) {
        return adapters.containsKey(type);
    }

    public Map<DatabaseType, ConnectionTestResult> testAll() {
        Map<DatabaseType, ConnectionTestResult> results = new EnumMap<>(DatabaseType.class);
        for (Map.Entry<DatabaseType, DatabaseAdapter> entry : adapters.entrySet()) {
            results.put(entry.getKey(), entry.getValue().testConnection());
        }
        return results;
    }
}
