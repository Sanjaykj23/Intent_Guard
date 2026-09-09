package com.intentguard.backend.dto;

import jakarta.validation.constraints.NotBlank;

public class ChatRequest {
    @NotBlank(message = "userId is required")
    private String userId;

    private Long conversationId;

    @NotBlank(message = "message is required")
    private String message;

    public ChatRequest() {}

    public ChatRequest(String userId, Long conversationId, String message) {
        this.userId = userId;
        this.conversationId = conversationId;
        this.message = message;
    }

    public String getUserId() { return userId; }
    public void setUserId(String userId) { this.userId = userId; }

    public Long getConversationId() { return conversationId; }
    public void setConversationId(Long conversationId) { this.conversationId = conversationId; }

    public String getMessage() { return message; }
    public void setMessage(String message) { this.message = message; }
}
