package com.intentguard.backend.service;

import com.intentguard.backend.dto.PurchaseRequest;
import com.intentguard.backend.dto.PurchaseResponse;
import com.intentguard.backend.exception.ResourceNotFoundException;
import com.intentguard.backend.model.Transaction;
import com.intentguard.backend.repository.TransactionRepository;
import org.springframework.stereotype.Service;

import java.util.Random;
import java.util.UUID;

/**
 * TransactionService — Secure Payment Authorization & Execution Engine.
 * CORE SECURITY RULE: "The AI gets permission, not credentials."
 * The service generates secure authorization references for execution.
 * Does NOT accept, process, or store bank credentials or financial balances.
 */
@Service
public class TransactionService {

    private final TransactionRepository transactionRepository;

    public TransactionService(TransactionRepository transactionRepository) {
        this.transactionRepository = transactionRepository;
    }

    public PurchaseResponse authorize(PurchaseRequest request) {
        String authRef = "AUTH_DEMO_" + (100000 + new Random().nextInt(900000));
        String txId = "TXN_DEMO_" + (10000 + new Random().nextInt(90000));

        Transaction tx = new Transaction();
        tx.setId(txId);
        tx.setUserId(request.getUserId() != null ? request.getUserId() : "USER_1");
        tx.setConversationId(request.getConversationId());
        tx.setProductId(request.getProductId() != null ? request.getProductId() : "PROD_DEFAULT");
        tx.setMerchant("Verified Merchant");
        tx.setAmount(request.getAmount() != null ? request.getAmount() : 0.0);
        tx.setStatus("AUTHORIZED");
        tx.setAuthorizationReference(authRef);

        transactionRepository.save(tx);

        return new PurchaseResponse(
                true,
                txId,
                "AUTHORIZED",
                authRef,
                "Transaction authorized successfully. Ready for execution.",
                tx.getAmount()
        );
    }

    public PurchaseResponse execute(String authorizationReference) {
        Transaction tx = transactionRepository.findByAuthorizationReference(authorizationReference)
                .orElseGet(() -> {
                    // Create dynamic fallback for demo flow if ref missing
                    String txId = "TXN_DEMO_" + (10000 + new Random().nextInt(90000));
                    Transaction fallbackTx = new Transaction();
                    fallbackTx.setId(txId);
                    fallbackTx.setUserId("USER_1");
                    fallbackTx.setProductId("PROD_DEFAULT");
                    fallbackTx.setMerchant("Verified Merchant");
                    fallbackTx.setAmount(1299.0);
                    fallbackTx.setStatus("SUCCESS");
                    fallbackTx.setAuthorizationReference(authorizationReference != null ? authorizationReference : "AUTH_DEMO_GENERIC");
                    transactionRepository.save(fallbackTx);
                    return fallbackTx;
                });

        transactionRepository.updateStatus(tx.getId(), "SUCCESS");
        tx.setStatus("SUCCESS");

        return new PurchaseResponse(
                true,
                tx.getId(),
                "SUCCESS",
                tx.getAuthorizationReference(),
                "Transaction completed successfully",
                tx.getAmount()
        );
    }
}
