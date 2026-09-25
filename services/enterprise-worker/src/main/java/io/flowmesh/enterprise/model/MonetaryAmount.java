package io.flowmesh.enterprise.model;

import jakarta.persistence.Column;
import jakarta.persistence.Embeddable;
import java.io.Serializable;
import java.math.BigDecimal;
import java.util.Objects;

@Embeddable
public class MonetaryAmount implements Serializable {

    @Column(name = "amount", nullable = false, precision = 18, scale = 2)
    private BigDecimal amount;

    @Column(name = "currency", nullable = false, length = 3)
    private String currency;

    public MonetaryAmount() {
        this.amount = BigDecimal.ZERO;
        this.currency = "USD";
    }

    public MonetaryAmount(BigDecimal amount, String currency) {
        if (amount == null) {
            throw new IllegalArgumentException("Monetary amount cannot be null");
        }
        if (currency == null || currency.trim().length() != 3) {
            throw new IllegalArgumentException("Currency must be a 3-letter ISO code");
        }
        this.amount = amount;
        this.currency = currency.trim().toUpperCase();
    }

    public BigDecimal getAmount() {
        return amount;
    }

    public void setAmount(BigDecimal amount) {
        this.amount = amount;
    }

    public String getCurrency() {
        return currency;
    }

    public void setCurrency(String currency) {
        this.currency = currency != null ? currency.toUpperCase() : "USD";
    }

    @Override
    public boolean equals(Object o) {
        if (this == o) return true;
        if (!(o instanceof MonetaryAmount that)) return false;
        return Objects.equals(amount, that.amount) && Objects.equals(currency, that.currency);
    }

    @Override
    public int hashCode() {
        return Objects.hash(amount, currency);
    }

    @Override
    public String toString() {
        return amount + " " + currency;
    }
}
