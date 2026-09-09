package com.intentguard.backend.dto;

import jakarta.validation.constraints.NotBlank;

public class LoginRequest {
    @NotBlank(message = "Password is required")
    private String password;

    public LoginRequest() {}
    public LoginRequest(String password) { this.password = password; }

    public String getPassword() { return password; }
    public void setPassword(String password) { this.password = password; }
}
