package io.flowmesh.enterprise.dataplatform;

import io.flowmesh.enterprise.dataplatform.schema.DataPlatformSchemaEngine;
import io.flowmesh.enterprise.dataplatform.schema.DataPlatformSchemaEngine.ContractValidationResult;
import io.flowmesh.enterprise.dataplatform.schema.DataPlatformSchemaEngine.DriftSeverity;
import io.flowmesh.enterprise.dataplatform.schema.DataPlatformSchemaEngine.SchemaDriftReport;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;

import java.util.List;
import java.util.Map;

import static org.junit.jupiter.api.Assertions.*;

@DisplayName("Data Platform Engineering: Schema Contract & Drift Engine TDD Suite")
class DataPlatformSchemaEngineTest {

    private DataPlatformSchemaEngine schemaEngine;

    @BeforeEach
    void setUp() {
        schemaEngine = new DataPlatformSchemaEngine();
    }

    @Test
    @DisplayName("TDD: Validate Contract - should accept payload matching contract schema exactly")
    void testValidateContract_ValidPayload() {
        Map<String, String> contract = Map.of(
                "transactionId", "STRING",
                "amount", "NUMBER",
                "isActive", "BOOLEAN",
                "metadata", "OBJECT",
                "tags", "ARRAY"
        );

        Map<String, Object> payload = Map.of(
                "transactionId", "TX-1001",
                "amount", 1250.75,
                "isActive", true,
                "metadata", Map.of("source", "web"),
                "tags", List.of("enterprise", "priority")
        );

        ContractValidationResult result = schemaEngine.validateContract(contract, payload);

        assertTrue(result.valid());
        assertTrue(result.missingFields().isEmpty());
        assertTrue(result.typeViolations().isEmpty());
        assertNotNull(result.validatedAt());
    }

    @Test
    @DisplayName("TDD: Validate Contract - should detect missing required fields and type violations")
    void testValidateContract_MissingAndTypeViolations() {
        Map<String, String> contract = Map.of(
                "transactionId", "STRING",
                "amount", "NUMBER",
                "tenantId", "STRING"
        );

        Map<String, Object> payload = Map.of(
                "transactionId", 12345, // Type violation: expected STRING, got Integer
                "amount", 99.99
                // missing tenantId
        );

        ContractValidationResult result = schemaEngine.validateContract(contract, payload);

        assertFalse(result.valid());
        assertEquals(1, result.missingFields().size());
        assertTrue(result.missingFields().contains("tenantId"));

        assertEquals(1, result.typeViolations().size());
        assertTrue(result.typeViolations().get(0).contains("transactionId"));
    }

    @Test
    @DisplayName("TDD: Validate Contract - should return valid when contract is empty or null")
    void testValidateContract_NullOrEmptyContract() {
        ContractValidationResult resultNull = schemaEngine.validateContract(null, Map.of("id", "123"));
        assertTrue(resultNull.valid());

        ContractValidationResult resultEmpty = schemaEngine.validateContract(Map.of(), Map.of("id", "123"));
        assertTrue(resultEmpty.valid());
    }

    @Test
    @DisplayName("TDD: Detect Drift - identical schemas should result in COMPATIBLE severity")
    void testDetectDrift_Compatible() {
        Map<String, String> baseline = Map.of(
                "id", "STRING",
                "amount", "NUMBER",
                "createdAt", "STRING"
        );
        Map<String, String> incoming = Map.of(
                "id", "STRING",
                "amount", "NUMBER",
                "createdAt", "STRING"
        );

        SchemaDriftReport report = schemaEngine.detectDrift(baseline, incoming);

        assertEquals(DriftSeverity.COMPATIBLE, report.severity());
        assertTrue(report.addedFields().isEmpty());
        assertTrue(report.removedFields().isEmpty());
        assertTrue(report.alteredTypes().isEmpty());
        assertTrue(report.recommendation().toLowerCase().contains("100%"));
    }

    @Test
    @DisplayName("TDD: Detect Drift - additive fields without drops or type changes should be NON_BREAKING_ADDITIVE")
    void testDetectDrift_NonBreakingAdditive() {
        Map<String, String> baseline = Map.of(
                "id", "STRING",
                "amount", "NUMBER"
        );
        Map<String, String> incoming = Map.of(
                "id", "STRING",
                "amount", "NUMBER",
                "currency", "STRING",
                "taxCode", "STRING"
        );

        SchemaDriftReport report = schemaEngine.detectDrift(baseline, incoming);

        assertEquals(DriftSeverity.NON_BREAKING_ADDITIVE, report.severity());
        assertEquals(2, report.addedFields().size());
        assertTrue(report.addedFields().contains("currency"));
        assertTrue(report.addedFields().contains("taxCode"));
        assertTrue(report.removedFields().isEmpty());
        assertTrue(report.alteredTypes().isEmpty());
        assertTrue(report.recommendation().toLowerCase().contains("safe to proceed"));
    }

    @Test
    @DisplayName("TDD: Detect Drift - dropped columns or altered types must trigger CRITICAL_BREAKING severity")
    void testDetectDrift_CriticalBreaking() {
        Map<String, String> baseline = Map.of(
                "id", "STRING",
                "amount", "NUMBER",
                "tenantId", "STRING",
                "status", "STRING"
        );
        Map<String, String> incoming = Map.of(
                "id", "STRING",
                "amount", "STRING", // Altered type: NUMBER -> STRING
                "status", "STRING"
                // tenantId is removed
        );

        SchemaDriftReport report = schemaEngine.detectDrift(baseline, incoming);

        assertEquals(DriftSeverity.CRITICAL_BREAKING, report.severity());
        assertEquals(1, report.removedFields().size());
        assertTrue(report.removedFields().contains("tenantId"));

        assertEquals(1, report.alteredTypes().size());
        assertEquals("NUMBER -> STRING", report.alteredTypes().get("amount"));
        assertTrue(report.recommendation().toLowerCase().contains("reject pipeline ingestion"));
    }
}
