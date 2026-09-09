package com.intentguard.backend.dto;

public class PurchaseResponse {
    private boolean success;
    private String transactionId;
    private String status;
    private String authorizationReference;
    private String message;
    private Double amountPaid;

    public PurchaseResponse() {}

    public PurchaseResponse(boolean success, String transactionId, String status,
                            String authorizationReference, String message, Double amountPaid) {
        this.success = success;
        this.transactionId = transactionId;
        this.status = status;
        this.authorizationReference = authorizationReference;
        this.message = message;
        this.amountPaid = amountPaid;
    }

    public boolean isSuccess() { return success; }
    public void setSuccess(boolean success) { this.success = success; }

    public String getTransactionId() { return transactionId; }
    public void setTransactionId(String transactionId) { this.transactionId = transactionId; }

    public String getStatus() { return status; }
    public void setStatus(String status) { this.status = status; }

    public String getAuthorizationReference() { return authorizationReference; }
    public void setAuthorizationReference(String authorizationReference) { this.authorizationReference = authorizationReference; }

    public String getMessage() { return message; }
    public void setMessage(String message) { this.message = message; }

    public Double getAmountPaid() { return amountPaid; }
    public void setAmountPaid(Double amountPaid) { this.amountPaid = amountPaid; }
}
