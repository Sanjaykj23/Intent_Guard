package com.intentguard.backend.model;

import java.time.LocalDateTime;

/**
 * Transaction Model
 * Tracks authorized execution references and transaction status.
 * DOES NOT store bank balance, card numbers, CVV, or UPI PINs.
 */
public class Transaction {
    private String id;
    private String userId;
    private Long conversationId;
    private String productId;
    private String merchant;
    private Double amount;
    private String status; // "PENDING", "AUTHORIZED", "SUCCESS", "FAILED"
    private String authorizationReference;
    private LocalDateTime createdAt;

    public Transaction() {}

    public Transaction(String id, String userId, Long conversationId, String productId,
                       String merchant, Double amount, String status,
                       String authorizationReference, LocalDateTime createdAt) {
        this.id = id;
        this.userId = userId;
        this.conversationId = conversationId;
        this.productId = productId;
        this.merchant = merchant;
        this.amount = amount;
        this.status = status;
        this.authorizationReference = authorizationReference;
        this.createdAt = createdAt;
    }

    public String getId() { return id; }
    public void setId(String id) { this.id = id; }

    public String getUserId() { return userId; }
    public void setUserId(String userId) { this.userId = userId; }

    public Long getConversationId() { return conversationId; }
    public void setConversationId(Long conversationId) { this.conversationId = conversationId; }

    public String getProductId() { return productId; }
    public void setProductId(String productId) { this.productId = productId; }

    public String getMerchant() { return merchant; }
    public void setMerchant(String merchant) { this.merchant = merchant; }

    public Double getAmount() { return amount; }
    public void setAmount(Double amount) { this.amount = amount; }

    public String getStatus() { return status; }
    public void setStatus(String status) { this.status = status; }

    public String getAuthorizationReference() { return authorizationReference; }
    public void setAuthorizationReference(String authorizationReference) { this.authorizationReference = authorizationReference; }

    public LocalDateTime getCreatedAt() { return createdAt; }
    public void setCreatedAt(LocalDateTime createdAt) { this.createdAt = createdAt; }
}
