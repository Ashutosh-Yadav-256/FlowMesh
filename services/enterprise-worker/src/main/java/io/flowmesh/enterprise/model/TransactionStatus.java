package io.flowmesh.enterprise.model;

public enum TransactionStatus {
    PENDING,
    VALIDATED,
    RECONCILING,
    COMMITTED,
    REJECTED,
    SETTLED
}
