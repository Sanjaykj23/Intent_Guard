package com.intentguard.backend.dto;

public class LoginResponse {
    private boolean success;
    private String agentUserId;
    private String message;

    public LoginResponse() {}

    public LoginResponse(boolean success, String agentUserId, String message) {
        this.success = success;
        this.agentUserId = agentUserId;
        this.message = message;
    }

    public boolean isSuccess() { return success; }
    public void setSuccess(boolean success) { this.success = success; }

    public String getAgentUserId() { return agentUserId; }
    public void setAgentUserId(String agentUserId) { this.agentUserId = agentUserId; }

    public String getMessage() { return message; }
    public void setMessage(String message) { this.message = message; }
}
