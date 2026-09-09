package com.intentguard.backend.dto;

public class PurchaseRequest {
    private String userId;
    private Long conversationId;
    private String productId;
    private Double amount;
    private String authorizationReference;

    public PurchaseRequest() {}

    public String getUserId() { return userId; }
    public void setUserId(String userId) { this.userId = userId; }

    public Long getConversationId() { return conversationId; }
    public void setConversationId(Long conversationId) { this.conversationId = conversationId; }

    public String getProductId() { return productId; }
    public void setProductId(String productId) { this.productId = productId; }

    public Double getAmount() { return amount; }
    public void setAmount(Double amount) { this.amount = amount; }

    public String getAuthorizationReference() { return authorizationReference; }
    public void setAuthorizationReference(String authorizationReference) { this.authorizationReference = authorizationReference; }
}
