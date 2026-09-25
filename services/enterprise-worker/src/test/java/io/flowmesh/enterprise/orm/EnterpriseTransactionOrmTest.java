package io.flowmesh.enterprise.orm;

import io.flowmesh.enterprise.model.*;
import io.flowmesh.enterprise.repository.EnterpriseTransactionRepository;
import io.flowmesh.enterprise.repository.spec.TransactionSpecification;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.orm.jpa.DataJpaTest;
import org.springframework.boot.test.autoconfigure.orm.jpa.TestEntityManager;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.PageRequest;
import org.springframework.orm.ObjectOptimisticLockingFailureException;
import org.springframework.test.context.ActiveProfiles;

import java.math.BigDecimal;
import java.util.List;
import java.util.Map;
import java.util.Optional;

import static org.junit.jupiter.api.Assertions.*;

@DataJpaTest
@ActiveProfiles("test")
@DisplayName("ORM / JPA 2.2 / Hibernate 6 TDD Specification Suite")
class EnterpriseTransactionOrmTest {

    @Autowired
    private TestEntityManager entityManager;

    @Autowired
    private EnterpriseTransactionRepository repository;

    @Test
    @DisplayName("TDD: Should persist entity with MonetaryAmount embeddable and JSON metadata converter")
    void testEntityPersistenceAndValueObject() {
        EnterpriseTransaction txn = new EnterpriseTransaction(
                "tenant_acme",
                "REF-ORM-001",
                new BigDecimal("1500.50"),
                "USD",
                "STRIPE_GATEWAY",
                "ORACLE_GL",
                "COMMITTED"
        );
        txn.setMetadata(Map.of("risk_score", 0.02, "channel", "WEB_CHECKOUT"));
        txn.addAuditEntry("INITIAL_POST", "Operator_1", "Created via automated test");

        EnterpriseTransaction saved = repository.save(txn);
        entityManager.flush();
        entityManager.clear();

        Optional<EnterpriseTransaction> loaded = repository.findById(saved.getId());
        assertTrue(loaded.isPresent());
        EnterpriseTransaction entity = loaded.get();

        assertEquals(new BigDecimal("1500.50"), entity.getAmount());
        assertEquals("USD", entity.getCurrency());
        assertEquals(0L, entity.getVersion());
        assertEquals(0.02, ((Number) entity.getMetadata().get("risk_score")).doubleValue());
        assertFalse(entity.isDeleted());
    }

    @Test
    @DisplayName("TDD: Optimistic Locking - Should throw ObjectOptimisticLockingFailureException on concurrent stale update")
    void testOptimisticLockingCollision() {
        EnterpriseTransaction txn = new EnterpriseTransaction(
                "tenant_acme",
                "REF-LOCK-COLLISION",
                new BigDecimal("500.00"),
                "USD",
                "REST_INGRESS",
                "INTERNAL_LEDGER",
                "PENDING"
        );
        EnterpriseTransaction saved = repository.save(txn);
        entityManager.flush();

        Long id = saved.getId();

        // Simulate Thread 1 holding a detached entity snapshot at version 0
        EnterpriseTransaction staleThread1 = new EnterpriseTransaction(
                "tenant_acme",
                "REF-LOCK-COLLISION",
                new BigDecimal("500.00"),
                "USD",
                "REST_INGRESS",
                "INTERNAL_LEDGER",
                "PENDING"
        );
        staleThread1.setId(id);
        staleThread1.setVersion(0L);

        // Meanwhile, Thread 2 modifies and commits the transaction, bumping version to 1 in the database
        EnterpriseTransaction txnThread2 = repository.findById(id).orElseThrow();
        txnThread2.setStatus("COMMITTED");
        repository.save(txnThread2);
        entityManager.flush();
        entityManager.clear();

        // Now Thread 1 attempts to save its stale entity with version 0
        staleThread1.setStatus("REJECTED");
        assertThrows(ObjectOptimisticLockingFailureException.class, () -> {
            repository.save(staleThread1);
            entityManager.flush();
        }, "Hibernate must detect stale version update and throw ObjectOptimisticLockingFailureException");
    }

    @Test
    @DisplayName("TDD: N+1 Query Elimination - EntityGraph should eagerly load child audit entries in single query")
    void testEntityGraphEagerLoading() {
        EnterpriseTransaction txn = new EnterpriseTransaction(
                "tenant_fintech",
                "REF-GRAPH-001",
                new BigDecimal("999.00"),
                "EUR",
                "SEPA_TRANSFER",
                "ORACLE_ERP",
                "COMMITTED"
        );
        txn.addAuditEntry("VALIDATE", "System", "Passed KYC check");
        txn.addAuditEntry("RECONCILE", "BatchEngine", "Matched against bank statement");
        txn.addAuditEntry("POST", "LedgerService", "Ledger journal updated");

        EnterpriseTransaction saved = repository.save(txn);
        entityManager.flush();
        entityManager.clear();

        // Fetch using custom @EntityGraph method
        Optional<EnterpriseTransaction> loaded = repository.findByIdWithAuditEntries(saved.getId());
        assertTrue(loaded.isPresent());

        // Audit entries must be loaded and populated without lazy initialization exception
        List<TransactionAuditEntry> entries = loaded.get().getAuditEntries();
        assertEquals(3, entries.size());
        assertEquals("VALIDATE", entries.get(0).getAction());
        assertEquals("POST", entries.get(2).getAction());
    }

    @Test
    @DisplayName("TDD: Specifications - Should build dynamic Criteria predicates for multi-filter search")
    void testDynamicCriteriaSpecifications() {
        repository.save(new EnterpriseTransaction("tenant_acme", "REF-A1", new BigDecimal("100.00"), "USD", "S1", "T1", "COMMITTED"));
        repository.save(new EnterpriseTransaction("tenant_acme", "REF-A2", new BigDecimal("500.00"), "USD", "S1", "T1", "COMMITTED"));
        repository.save(new EnterpriseTransaction("tenant_acme", "REF-A3", new BigDecimal("1200.00"), "USD", "S1", "T1", "PENDING"));
        repository.save(new EnterpriseTransaction("tenant_prod", "REF-B1", new BigDecimal("300.00"), "EUR", "S1", "T1", "COMMITTED"));
        entityManager.flush();

        // Filter: tenant_acme + COMMITTED + USD + minAmount 200
        var spec = TransactionSpecification.withFilters(
                "tenant_acme",
                "COMMITTED",
                "USD",
                new BigDecimal("200.00"),
                null
        );

        List<EnterpriseTransaction> results = repository.findAll(spec);
        assertEquals(1, results.size());
        assertEquals("REF-A2", results.get(0).getExternalReference());
    }

    @Test
    @DisplayName("TDD: Soft Delete - SQLDelete & SQLRestriction should prevent deleted records from query results")
    void testSoftDeletePattern() {
        EnterpriseTransaction txn = new EnterpriseTransaction(
                "tenant_acme",
                "REF-SOFT-DELETE",
                new BigDecimal("75.00"),
                "USD",
                "POS_TERMINAL",
                "LEDGER",
                "COMMITTED"
        );
        EnterpriseTransaction saved = repository.save(txn);
        entityManager.flush();

        Long id = saved.getId();
        repository.delete(saved);
        entityManager.flush();
        entityManager.clear();

        // Normal query should filter out soft-deleted records via @SQLRestriction("deleted = false")
        Optional<EnterpriseTransaction> found = repository.findById(id);
        assertTrue(found.isEmpty(), "Soft deleted entity must not be returned by standard finder");
    }
}
