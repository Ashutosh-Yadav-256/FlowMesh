package io.flowmesh.enterprise.repository;

import io.flowmesh.enterprise.model.EnterpriseTransaction;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;
import org.springframework.stereotype.Repository;

import java.util.List;
import java.util.Optional;

@Repository
public interface EnterpriseTransactionRepository extends JpaRepository<EnterpriseTransaction, Long> {

    List<EnterpriseTransaction> findByTenantId(String tenantId);

    Optional<EnterpriseTransaction> findByTenantIdAndExternalReference(String tenantId, String externalReference);

    @Query("SELECT t FROM EnterpriseTransaction t WHERE t.tenantId = :tenantId AND t.status = :status ORDER BY t.createdAt DESC")
    List<EnterpriseTransaction> findActiveTransactionsByTenant(
        @Param("tenantId") String tenantId,
        @Param("status") String status
    );
}
