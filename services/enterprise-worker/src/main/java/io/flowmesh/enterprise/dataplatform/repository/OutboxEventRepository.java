package io.flowmesh.enterprise.dataplatform.repository;

import io.flowmesh.enterprise.dataplatform.model.OutboxEvent;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;
import org.springframework.stereotype.Repository;

import java.util.List;

@Repository
public interface OutboxEventRepository extends JpaRepository<OutboxEvent, Long> {

    @Query("SELECT e FROM OutboxEvent e WHERE e.processed = false ORDER BY e.createdAt ASC")
    List<OutboxEvent> findPendingEvents(Pageable pageable);

    @Query("SELECT e FROM OutboxEvent e WHERE e.tenantId = :tenantId AND e.processed = false ORDER BY e.createdAt ASC")
    List<OutboxEvent> findPendingEventsByTenant(@Param("tenantId") String tenantId, Pageable pageable);

    long countByProcessedFalse();
}
