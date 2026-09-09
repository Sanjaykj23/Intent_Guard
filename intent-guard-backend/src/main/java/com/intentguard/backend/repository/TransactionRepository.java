package com.intentguard.backend.repository;

import com.intentguard.backend.model.Transaction;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.jdbc.core.RowMapper;
import org.springframework.stereotype.Repository;

import java.util.List;
import java.util.Optional;

/**
 * TransactionRepository using Spring JdbcTemplate.
 */
@Repository
public class TransactionRepository {

    private final JdbcTemplate jdbcTemplate;

    public TransactionRepository(JdbcTemplate jdbcTemplate) {
        this.jdbcTemplate = jdbcTemplate;
    }

    private final RowMapper<Transaction> transactionRowMapper = (rs, rowNum) -> new Transaction(
            rs.getString("id"),
            rs.getString("user_id"),
            rs.getObject("conversation_id") != null ? rs.getLong("conversation_id") : null,
            rs.getString("product_id"),
            rs.getString("merchant"),
            rs.getDouble("amount"),
            rs.getString("status"),
            rs.getString("authorization_reference"),
            rs.getTimestamp("created_at") != null ? rs.getTimestamp("created_at").toLocalDateTime() : null
    );

    public int save(Transaction tx) {
        String sql = "INSERT INTO transactions (id, user_id, conversation_id, product_id, merchant, amount, status, authorization_reference, created_at) " +
                     "VALUES (?, ?, ?, ?, ?, ?, ?, ?, NOW())";
        return jdbcTemplate.update(sql,
                tx.getId(),
                tx.getUserId(),
                tx.getConversationId(),
                tx.getProductId(),
                tx.getMerchant(),
                tx.getAmount(),
                tx.getStatus(),
                tx.getAuthorizationReference()
        );
    }

    public Optional<Transaction> findByAuthorizationReference(String ref) {
        String sql = "SELECT * FROM transactions WHERE authorization_reference = ?";
        return jdbcTemplate.query(sql, transactionRowMapper, ref).stream().findFirst();
    }

    public Optional<Transaction> findById(String id) {
        String sql = "SELECT * FROM transactions WHERE id = ?";
        return jdbcTemplate.query(sql, transactionRowMapper, id).stream().findFirst();
    }

    public int updateStatus(String id, String status) {
        String sql = "UPDATE transactions SET status = ? WHERE id = ?";
        return jdbcTemplate.update(sql, status, id);
    }

    public List<Transaction> findByUserId(String userId) {
        String sql = "SELECT * FROM transactions WHERE user_id = ? ORDER BY created_at DESC";
        return jdbcTemplate.query(sql, transactionRowMapper, userId);
    }
}
