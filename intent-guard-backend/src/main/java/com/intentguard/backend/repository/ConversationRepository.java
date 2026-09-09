package com.intentguard.backend.repository;

import com.intentguard.backend.model.Conversation;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.jdbc.core.RowMapper;
import org.springframework.jdbc.support.GeneratedKeyHolder;
import org.springframework.jdbc.support.KeyHolder;
import org.springframework.stereotype.Repository;

import java.sql.PreparedStatement;
import java.sql.Statement;
import java.util.List;
import java.util.Map;
import java.util.Optional;

/**
 * ConversationRepository using Spring JdbcTemplate.
 */
@Repository
public class ConversationRepository {

    private final JdbcTemplate jdbcTemplate;

    public ConversationRepository(JdbcTemplate jdbcTemplate) {
        this.jdbcTemplate = jdbcTemplate;
    }

    private final RowMapper<Conversation> conversationRowMapper = (rs, rowNum) -> new Conversation(
            rs.getLong("id"),
            rs.getString("user_id"),
            rs.getString("title"),
            rs.getTimestamp("created_at") != null ? rs.getTimestamp("created_at").toLocalDateTime() : null,
            rs.getTimestamp("updated_at") != null ? rs.getTimestamp("updated_at").toLocalDateTime() : null
    );

    public Long save(Conversation conversation) {
        String sql = "INSERT INTO conversations (user_id, title, created_at, updated_at) VALUES (?, ?, NOW(), NOW())";
        KeyHolder keyHolder = new GeneratedKeyHolder();

        jdbcTemplate.update(connection -> {
            PreparedStatement ps = connection.prepareStatement(sql, Statement.RETURN_GENERATED_KEYS);
            ps.setString(1, conversation.getUserId());
            ps.setString(2, conversation.getTitle());
            return ps;
        }, keyHolder);

        Map<String, Object> keys = keyHolder.getKeys();
        if (keys != null) {
            for (Map.Entry<String, Object> entry : keys.entrySet()) {
                if ("id".equalsIgnoreCase(entry.getKey()) && entry.getValue() instanceof Number num) {
                    return num.longValue();
                }
            }
            if (!keys.isEmpty() && keys.values().iterator().next() instanceof Number num) {
                return num.longValue();
            }
        }
        return keyHolder.getKey() != null ? keyHolder.getKey().longValue() : null;
    }

    public Optional<Conversation> findById(Long id) {
        String sql = "SELECT * FROM conversations WHERE id = ?";
        return jdbcTemplate.query(sql, conversationRowMapper, id).stream().findFirst();
    }

    public List<Conversation> findByUserId(String userId) {
        String sql = "SELECT * FROM conversations WHERE user_id = ? ORDER BY updated_at DESC";
        return jdbcTemplate.query(sql, conversationRowMapper, userId);
    }

    public int updateTitle(Long id, String title) {
        String sql = "UPDATE conversations SET title = ?, updated_at = NOW() WHERE id = ?";
        return jdbcTemplate.update(sql, title, id);
    }

    public int deleteByIdAndUserId(Long id, String userId) {
        String sql = "DELETE FROM conversations WHERE id = ? AND user_id = ?";
        return jdbcTemplate.update(sql, id, userId);
    }
}
