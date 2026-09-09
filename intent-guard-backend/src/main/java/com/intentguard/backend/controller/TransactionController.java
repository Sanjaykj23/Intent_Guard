package com.intentguard.backend.controller;

import com.intentguard.backend.dto.PurchaseRequest;
import com.intentguard.backend.dto.PurchaseResponse;
import com.intentguard.backend.service.TransactionService;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

/**
 * TransactionController
 * Handles secure payment authorization reference generation and mock payment execution.
 * CORE SECURITY RULE: "The AI gets permission, not credentials."
 */
@RestController
@RequestMapping("/api/transactions")
public class TransactionController {

    private final TransactionService transactionService;

    public TransactionController(TransactionService transactionService) {
        this.transactionService = transactionService;
    }

    @PostMapping("/authorize")
    public ResponseEntity<PurchaseResponse> authorizeTransaction(@RequestBody PurchaseRequest request) {
        PurchaseResponse response = transactionService.authorize(request);
        return ResponseEntity.ok(response);
    }

    @PostMapping("/execute")
    public ResponseEntity<PurchaseResponse> executeTransaction(@RequestBody PurchaseRequest request) {
        String authRef = request.getAuthorizationReference();
        PurchaseResponse response = transactionService.execute(authRef);
        return ResponseEntity.ok(response);
    }
}
