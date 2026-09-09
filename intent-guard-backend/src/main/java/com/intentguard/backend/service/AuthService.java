package com.intentguard.backend.service;

import com.intentguard.backend.dto.LoginResponse;
import org.springframework.stereotype.Service;

/**
 * AuthService
 * Handles demo authentication.
 * Demo password: intent123
 */
@Service
public class AuthService {

    public LoginResponse login(String password) {
        if ("intent123".equals(password)) {
            return new LoginResponse(true, "USER_1", "Authentication successful");
        }
        return new LoginResponse(false, null, "Invalid authorization password");
    }
}
