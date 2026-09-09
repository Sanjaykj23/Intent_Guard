package com.intentguard.backend.model;

import java.time.LocalDateTime;

/**
 * Message Model
 * Represents a single message bubble (USER or AGENT) within a conversation.
 */
public class Message {
    private Long id;
    private Long conversationId;
    private String sender; // "USER" or "AGENT"
    private String content;
    private LocalDateTime createdAt;

    public Message() {}

    public Message(Long id, Long conversationId, String sender, String content, LocalDateTime createdAt) {
        this.id = id;
        this.conversationId = conversationId;
        this.sender = sender;
        this.content = content;
        this.createdAt = createdAt;
    }

    public Long getId() { return id; }
    public void setId(Long id) { this.id = id; }

    public Long getConversationId() { return conversationId; }
    public void setConversationId(Long conversationId) { this.conversationId = conversationId; }

    public String getSender() { return sender; }
    public void setSender(String sender) { this.sender = sender; }

    public String getContent() { return content; }
    public void setContent(String content) { this.content = content; }

    public LocalDateTime getCreatedAt() { return createdAt; }
    public void setCreatedAt(LocalDateTime createdAt) { this.createdAt = createdAt; }
}
