package io.flowmesh.enterprise.repository.spec;

import io.flowmesh.enterprise.model.EnterpriseTransaction;
import jakarta.persistence.criteria.Predicate;
import org.springframework.data.jpa.domain.Specification;

import java.math.BigDecimal;
import java.util.ArrayList;
import java.util.List;

public class TransactionSpecification {

    public static Specification<EnterpriseTransaction> withFilters(
            String tenantId,
            String status,
            String currency,
            BigDecimal minAmount,
            BigDecimal maxAmount) {

        return (root, query, cb) -> {
            List<Predicate> predicates = new ArrayList<>();

            if (tenantId != null && !tenantId.isBlank()) {
                predicates.add(cb.equal(root.get("tenantId"), tenantId));
            }

            if (status != null && !status.isBlank()) {
                predicates.add(cb.equal(root.get("status"), status));
            }

            if (currency != null && !currency.isBlank()) {
                predicates.add(cb.equal(root.get("monetaryAmount").get("currency"), currency.trim().toUpperCase()));
            }

            if (minAmount != null) {
                predicates.add(cb.greaterThanOrEqualTo(root.get("monetaryAmount").get("amount"), minAmount));
            }

            if (maxAmount != null) {
                predicates.add(cb.lessThanOrEqualTo(root.get("monetaryAmount").get("amount"), maxAmount));
            }

            return cb.and(predicates.toArray(new Predicate[0]));
        };
    }
}
