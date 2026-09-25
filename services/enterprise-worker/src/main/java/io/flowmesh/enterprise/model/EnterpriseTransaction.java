package io.flowmesh.enterprise.model;

import io.flowmesh.enterprise.model.converter.TransactionMetadataConverter;
import jakarta.persistence.*;
import org.hibernate.annotations.SQLDelete;
import org.hibernate.annotations.SQLRestriction;

import java.math.BigDecimal;
import java.time.Instant;
import java.util.*;

@Entity
@Table(name = "enterprise_transactions", indexes = {
    @Index(name = "idx_txn_tenant_status", columnList = "tenant_id, status"),
    @Index(name = "idx_txn_reference", columnList = "external_reference"),
    @Index(name = "idx_txn_created_at", columnList = "created_at")
})
@NamedEntityGraph(
    name = "EnterpriseTransaction.withAuditEntries",
    attributeNodes = @NamedAttributeNode("auditEntries")
)
@SQLDelete(sql = "UPDATE enterprise_transactions SET deleted = true WHERE id = ? AND version = ?")
@SQLRestriction("deleted = false")
public class EnterpriseTransaction {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Version
    @Column(name = "version", nullable = false)
    private Long version = 0L;

    @Column(name = "tenant_id", nullable = false, length = 64)
    private String tenantId;

    @Column(name = "external_reference", nullable = false, length = 128)
    private String externalReference;

    @Embedded
    private MonetaryAmount monetaryAmount = new MonetaryAmount(BigDecimal.ZERO, "USD");

    @Column(name = "source_system", nullable = false, length = 64)
    private String sourceSystem;

    @Column(name = "target_system", nullable = false, length = 64)
    private String targetSystem;

    @Column(name = "status", nullable = false, length = 32)
    private String status;

    @Convert(converter = TransactionMetadataConverter.class)
    @Column(name = "metadata", columnDefinition = "TEXT")
    private Map<String, Object> metadata = new HashMap<>();

    @OneToMany(mappedBy = "transaction", cascade = CascadeType.ALL, orphanRemoval = true, fetch = FetchType.LAZY)
    private List<TransactionAuditEntry> auditEntries = new ArrayList<>();

    @Column(name = "deleted", nullable = false)
    private boolean deleted = false;

    @Column(name = "created_at", nullable = false, updatable = false)
    private Instant createdAt = Instant.now();

    @Column(name = "updated_at", nullable = false)
    private Instant updatedAt = Instant.now();

    public EnterpriseTransaction() {}

    public EnterpriseTransaction(String tenantId, String externalReference, BigDecimal amount, String currency, String sourceSystem, String targetSystem, String status) {
        this.tenantId = tenantId;
        this.externalReference = externalReference;
        this.monetaryAmount = new MonetaryAmount(amount != null ? amount : BigDecimal.ZERO, currency != null ? currency : "USD");
        this.sourceSystem = sourceSystem;
        this.targetSystem = targetSystem;
        this.status = status;
        this.createdAt = Instant.now();
        this.updatedAt = Instant.now();
        this.deleted = false;
        this.metadata = new HashMap<>();
    }

    @PrePersist
    protected void onPrePersist() {
        if (this.createdAt == null) this.createdAt = Instant.now();
        this.updatedAt = Instant.now();
        if (this.monetaryAmount == null) this.monetaryAmount = new MonetaryAmount(BigDecimal.ZERO, "USD");
    }

    @PreUpdate
    protected void onPreUpdate() {
        this.updatedAt = Instant.now();
    }

    public void addAuditEntry(String action, String actor, String details) {
        TransactionAuditEntry entry = new TransactionAuditEntry(this, action, actor, details);
        this.auditEntries.add(entry);
    }

    // Getters & Setters
    public Long getId() { return id; }
    public void setId(Long id) { this.id = id; }

    public Long getVersion() { return version; }
    public void setVersion(Long version) { this.version = version; }

    public String getTenantId() { return tenantId; }
    public void setTenantId(String tenantId) { this.tenantId = tenantId; }

    public String getExternalReference() { return externalReference; }
    public void setExternalReference(String externalReference) { this.externalReference = externalReference; }

    public MonetaryAmount getMonetaryAmount() { return monetaryAmount; }
    public void setMonetaryAmount(MonetaryAmount monetaryAmount) {
        this.monetaryAmount = monetaryAmount != null ? monetaryAmount : new MonetaryAmount(BigDecimal.ZERO, "USD");
    }

    // Compatibility delegates for existing code
    public BigDecimal getAmount() {
        return monetaryAmount != null ? monetaryAmount.getAmount() : BigDecimal.ZERO;
    }
    public void setAmount(BigDecimal amount) {
        if (this.monetaryAmount == null) this.monetaryAmount = new MonetaryAmount(amount, "USD");
        else this.monetaryAmount.setAmount(amount);
    }

    public String getCurrency() {
        return monetaryAmount != null ? monetaryAmount.getCurrency() : "USD";
    }
    public void setCurrency(String currency) {
        if (this.monetaryAmount == null) this.monetaryAmount = new MonetaryAmount(BigDecimal.ZERO, currency);
        else this.monetaryAmount.setCurrency(currency);
    }

    public String getSourceSystem() { return sourceSystem; }
    public void setSourceSystem(String sourceSystem) { this.sourceSystem = sourceSystem; }

    public String getTargetSystem() { return targetSystem; }
    public void setTargetSystem(String targetSystem) { this.targetSystem = targetSystem; }

    public String getStatus() { return status; }
    public void setStatus(String status) { this.status = status; }

    public Map<String, Object> getMetadata() { return metadata; }
    public void setMetadata(Map<String, Object> metadata) { this.metadata = metadata != null ? metadata : new HashMap<>(); }

    public List<TransactionAuditEntry> getAuditEntries() { return auditEntries; }
    public void setAuditEntries(List<TransactionAuditEntry> auditEntries) { this.auditEntries = auditEntries != null ? auditEntries : new ArrayList<>(); }

    public boolean isDeleted() { return deleted; }
    public void setDeleted(boolean deleted) { this.deleted = deleted; }

    public Instant getCreatedAt() { return createdAt; }
    public void setCreatedAt(Instant createdAt) { this.createdAt = createdAt; }

    public Instant getUpdatedAt() { return updatedAt; }
    public void setUpdatedAt(Instant updatedAt) { this.updatedAt = updatedAt; }
}
