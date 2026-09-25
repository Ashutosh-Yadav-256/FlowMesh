package io.flowmesh.enterprise.model;

import com.fasterxml.jackson.annotation.JsonIgnore;
import jakarta.persistence.*;
import java.time.Instant;

@Entity
@Table(name = "transaction_audit_entries", indexes = {
    @Index(name = "idx_audit_txn_id", columnList = "transaction_id"),
    @Index(name = "idx_audit_performed_at", columnList = "performed_at")
})
public class TransactionAuditEntry {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @ManyToOne(fetch = FetchType.LAZY, optional = false)
    @JoinColumn(name = "transaction_id", nullable = false)
    @JsonIgnore
    private EnterpriseTransaction transaction;

    @Column(name = "action", nullable = false, length = 64)
    private String action;

    @Column(name = "actor", nullable = false, length = 64)
    private String actor;

    @Column(name = "details", length = 512)
    private String details;

    @Column(name = "performed_at", nullable = false, updatable = false)
    private Instant performedAt = Instant.now();

    public TransactionAuditEntry() {}

    public TransactionAuditEntry(EnterpriseTransaction transaction, String action, String actor, String details) {
        this.transaction = transaction;
        this.action = action;
        this.actor = actor;
        this.details = details;
        this.performedAt = Instant.now();
    }

    public Long getId() { return id; }
    public void setId(Long id) { this.id = id; }

    public EnterpriseTransaction getTransaction() { return transaction; }
    public void setTransaction(EnterpriseTransaction transaction) { this.transaction = transaction; }

    public String getAction() { return action; }
    public void setAction(String action) { this.action = action; }

    public String getActor() { return actor; }
    public void setActor(String actor) { this.actor = actor; }

    public String getDetails() { return details; }
    public void setDetails(String details) { this.details = details; }

    public Instant getPerformedAt() { return performedAt; }
    public void setPerformedAt(Instant performedAt) { this.performedAt = performedAt; }
}
