package io.flowmesh.enterprise.dataplatform.schema;

import org.springframework.stereotype.Service;

import java.time.Instant;
import java.util.*;

@Service
public class DataPlatformSchemaEngine {

    public record ContractValidationResult(
            boolean valid,
            List<String> missingFields,
            List<String> typeViolations,
            Instant validatedAt
    ) {}

    public enum DriftSeverity {
        COMPATIBLE,
        NON_BREAKING_ADDITIVE,
        CRITICAL_BREAKING
    }

    public record SchemaDriftReport(
            DriftSeverity severity,
            List<String> addedFields,
            List<String> removedFields,
            Map<String, String> alteredTypes,
            Instant analyzedAt,
            String recommendation
    ) {}

    public ContractValidationResult validateContract(Map<String, String> contract, Map<String, Object> payload) {
        List<String> missing = new ArrayList<>();
        List<String> violations = new ArrayList<>();

        if (contract == null || contract.isEmpty()) {
            return new ContractValidationResult(true, List.of(), List.of(), Instant.now());
        }

        for (Map.Entry<String, String> entry : contract.entrySet()) {
            String field = entry.getKey();
            String expectedType = entry.getValue().toUpperCase();

            if (!payload.containsKey(field) || payload.get(field) == null) {
                missing.add(field);
                continue;
            }

            Object val = payload.get(field);
            boolean typeMatches = switch (expectedType) {
                case "STRING", "VARCHAR", "TEXT" -> val instanceof CharSequence;
                case "NUMBER", "INTEGER", "BIGINT", "LONG" -> val instanceof Number;
                case "BOOLEAN" -> val instanceof Boolean;
                case "OBJECT", "JSON" -> val instanceof Map;
                case "ARRAY", "LIST" -> val instanceof Collection;
                default -> true;
            };

            if (!typeMatches) {
                violations.add("Field '" + field + "' expected " + expectedType + " but found " + val.getClass().getSimpleName());
            }
        }

        boolean isValid = missing.isEmpty() && violations.isEmpty();
        return new ContractValidationResult(isValid, missing, violations, Instant.now());
    }

    public SchemaDriftReport detectDrift(Map<String, String> baseline, Map<String, String> incoming) {
        List<String> added = new ArrayList<>();
        List<String> removed = new ArrayList<>();
        Map<String, String> altered = new HashMap<>();

        if (baseline == null) baseline = Map.of();
        if (incoming == null) incoming = Map.of();

        for (String field : incoming.keySet()) {
            if (!baseline.containsKey(field)) {
                added.add(field);
            } else {
                String baseType = baseline.get(field).toUpperCase();
                String inType = incoming.get(field).toUpperCase();
                if (!baseType.equals(inType)) {
                    altered.put(field, baseType + " -> " + inType);
                }
            }
        }

        for (String field : baseline.keySet()) {
            if (!incoming.containsKey(field)) {
                removed.add(field);
            }
        }

        DriftSeverity severity;
        String recommendation;

        if (!removed.isEmpty() || !altered.isEmpty()) {
            severity = DriftSeverity.CRITICAL_BREAKING;
            recommendation = "Reject pipeline ingestion: Downstream consumer queries will fail due to dropped columns or type changes.";
        } else if (!added.isEmpty()) {
            severity = DriftSeverity.NON_BREAKING_ADDITIVE;
            recommendation = "Safe to proceed: Schema expanded with new additive columns. Update metadata catalog.";
        } else {
            severity = DriftSeverity.COMPATIBLE;
            recommendation = "Schema contracts match 100%. No evolution actions required.";
        }

        return new SchemaDriftReport(severity, added, removed, altered, Instant.now(), recommendation);
    }
}
