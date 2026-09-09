package com.intentguard.backend.model;

import java.time.LocalDateTime;

/**
 * Conversation Model
 * Represents a session conversation thread started by a user.
 */
public class Conversation {
    private Long id;
    private String userId;
    private String title;
    private LocalDateTime createdAt;
    private LocalDateTime updatedAt;

    public Conversation() {}

    public Conversation(Long id, String userId, String title, LocalDateTime createdAt, LocalDateTime updatedAt) {
        this.id = id;
        this.userId = userId;
        this.title = title;
        this.createdAt = createdAt;
        this.updatedAt = updatedAt;
    }

    public Long getId() { return id; }
    public void setId(Long id) { this.id = id; }

    public String getUserId() { return userId; }
    public void setUserId(String userId) { this.userId = userId; }

    public String getTitle() { return title; }
    public void setTitle(String title) { this.title = title; }

    public LocalDateTime getCreatedAt() { return createdAt; }
    public void setCreatedAt(LocalDateTime createdAt) { this.createdAt = createdAt; }

    public LocalDateTime getUpdatedAt() { return updatedAt; }
    public void setUpdatedAt(LocalDateTime updatedAt) { this.updatedAt = updatedAt; }
}
