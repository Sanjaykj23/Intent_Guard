package com.intentguard.backend.dto;

import com.intentguard.backend.model.Intent;

public class ChatResponse {
    private Long conversationId;
    private String userMessage;
    private String agentMessage;
    private Intent intent;

    public ChatResponse() {}

    public ChatResponse(Long conversationId, String userMessage, String agentMessage, Intent intent) {
        this.conversationId = conversationId;
        this.userMessage = userMessage;
        this.agentMessage = agentMessage;
        this.intent = intent;
    }

    public Long getConversationId() { return conversationId; }
    public void setConversationId(Long conversationId) { this.conversationId = conversationId; }

    public String getUserMessage() { return userMessage; }
    public void setUserMessage(String userMessage) { this.userMessage = userMessage; }

    public String getAgentMessage() { return agentMessage; }
    public void setAgentMessage(String agentMessage) { this.agentMessage = agentMessage; }

    public Intent getIntent() { return intent; }
    public void setIntent(Intent intent) { this.intent = intent; }
}
