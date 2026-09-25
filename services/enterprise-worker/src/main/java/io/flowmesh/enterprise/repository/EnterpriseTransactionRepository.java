package io.flowmesh.enterprise.repository;

import io.flowmesh.enterprise.model.EnterpriseTransaction;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.EntityGraph;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.JpaSpecificationExecutor;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;
import org.springframework.stereotype.Repository;

import java.util.List;
import java.util.Optional;

@Repository
public interface EnterpriseTransactionRepository extends
        JpaRepository<EnterpriseTransaction, Long>,
        JpaSpecificationExecutor<EnterpriseTransaction> {

    List<EnterpriseTransaction> findByTenantId(String tenantId);

    Optional<EnterpriseTransaction> findByTenantIdAndExternalReference(String tenantId, String externalReference);

    @Query("SELECT t FROM EnterpriseTransaction t WHERE t.tenantId = :tenantId AND t.status = :status ORDER BY t.createdAt DESC")
    List<EnterpriseTransaction> findActiveTransactionsByTenant(
            @Param("tenantId") String tenantId,
            @Param("status") String status
    );

    /**
     * Eagerly loads transaction along with its audit entries in a single SQL JOIN query,
     * eliminating the classic Hibernate N+1 select problem.
     */
    @EntityGraph(value = "EnterpriseTransaction.withAuditEntries", type = EntityGraph.EntityGraphType.LOAD)
    @Query("SELECT t FROM EnterpriseTransaction t WHERE t.id = :id")
    Optional<EnterpriseTransaction> findByIdWithAuditEntries(@Param("id") Long id);

    @EntityGraph(value = "EnterpriseTransaction.withAuditEntries", type = EntityGraph.EntityGraphType.LOAD)
    @Query("SELECT t FROM EnterpriseTransaction t WHERE t.tenantId = :tenantId")
    Page<EnterpriseTransaction> findByTenantIdWithAuditEntries(@Param("tenantId") String tenantId, Pageable pageable);
}
