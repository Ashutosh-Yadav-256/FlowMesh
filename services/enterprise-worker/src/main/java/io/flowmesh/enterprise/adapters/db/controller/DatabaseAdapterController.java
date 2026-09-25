package io.flowmesh.enterprise.adapters.db.controller;

import io.flowmesh.enterprise.adapters.db.DatabaseAdapter;
import io.flowmesh.enterprise.adapters.db.DatabaseAdapterRegistry;
import io.flowmesh.enterprise.adapters.db.DatabaseType;
import io.flowmesh.enterprise.adapters.db.model.*;
import io.flowmesh.enterprise.logging.LogExecutionTime;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.*;

@RestController
@RequestMapping("/api/v1/enterprise/database")
@CrossOrigin(origins = {"http://localhost:3000", "http://127.0.0.1:3000", "http://localhost:8000"})
public class DatabaseAdapterController {

    private final DatabaseAdapterRegistry registry;

    public DatabaseAdapterController(DatabaseAdapterRegistry registry) {
        this.registry = registry;
    }

    @GetMapping("/adapters")
    public ResponseEntity<List<Map<String, Object>>> listAdapters() {
        List<Map<String, Object>> list = new ArrayList<>();
        for (DatabaseAdapter adapter : registry.getAllAdapters()) {
            Map<String, Object> item = new LinkedHashMap<>();
            item.put("type", adapter.getType().name());
            item.put("displayName", adapter.getDisplayName());
            item.put("poolStats", adapter.getPoolStatistics());
            list.add(item);
        }
        return ResponseEntity.ok(list);
    }

    @PostMapping("/adapters/{type}/test")
    @LogExecutionTime(thresholdMs = 500, operation = "database.testConnection")
    public ResponseEntity<ConnectionTestResult> testConnection(@PathVariable String type) {
        DatabaseType dbType = DatabaseType.fromString(type);
        DatabaseAdapter adapter = registry.getAdapter(dbType);
        return ResponseEntity.ok(adapter.testConnection());
    }

    @PostMapping("/test-all")
    @LogExecutionTime(thresholdMs = 1000, operation = "database.testAll")
    public ResponseEntity<Map<String, ConnectionTestResult>> testAll() {
        Map<DatabaseType, ConnectionTestResult> map = registry.testAll();
        Map<String, ConnectionTestResult> result = new LinkedHashMap<>();
        map.forEach((k, v) -> result.put(k.name(), v));
        return ResponseEntity.ok(result);
    }

    @PostMapping("/adapters/{type}/query")
    @LogExecutionTime(thresholdMs = 1500, operation = "database.executeQuery")
    public ResponseEntity<DatabaseQueryResponse> executeQuery(
            @PathVariable String type,
            @RequestBody DatabaseQueryRequest request) {
        DatabaseType dbType = DatabaseType.fromString(type);
        DatabaseAdapter adapter = registry.getAdapter(dbType);
        return ResponseEntity.ok(adapter.executeQuery(request));
    }

    @GetMapping("/adapters/{type}/tables")
    public ResponseEntity<List<TableMetadata>> introspectTables(
            @PathVariable String type,
            @RequestParam(required = false) String schema) {
        DatabaseType dbType = DatabaseType.fromString(type);
        DatabaseAdapter adapter = registry.getAdapter(dbType);
        return ResponseEntity.ok(adapter.introspectTables(schema));
    }

    @GetMapping("/adapters/{type}/pool")
    public ResponseEntity<PoolStats> getPoolStats(@PathVariable String type) {
        DatabaseType dbType = DatabaseType.fromString(type);
        DatabaseAdapter adapter = registry.getAdapter(dbType);
        return ResponseEntity.ok(adapter.getPoolStatistics());
    }
}
