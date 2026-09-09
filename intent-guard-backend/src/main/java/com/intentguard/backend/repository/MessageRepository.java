package com.intentguard.backend.repository;

import com.intentguard.backend.model.Message;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.jdbc.core.RowMapper;
import org.springframework.jdbc.support.GeneratedKeyHolder;
import org.springframework.jdbc.support.KeyHolder;
import org.springframework.stereotype.Repository;

import java.sql.PreparedStatement;
import java.sql.Statement;
import java.util.List;
import java.util.Map;

/**
 * MessageRepository using Spring JdbcTemplate.
 */
@Repository
public class MessageRepository {

    private final JdbcTemplate jdbcTemplate;

    public MessageRepository(JdbcTemplate jdbcTemplate) {
        this.jdbcTemplate = jdbcTemplate;
    }

    private final RowMapper<Message> messageRowMapper = (rs, rowNum) -> new Message(
            rs.getLong("id"),
            rs.getLong("conversation_id"),
            rs.getString("sender"),
            rs.getString("content"),
            rs.getTimestamp("created_at") != null ? rs.getTimestamp("created_at").toLocalDateTime() : null
    );

    public Long save(Message message) {
        String sql = "INSERT INTO messages (conversation_id, sender, content, created_at) VALUES (?, ?, ?, NOW())";
        KeyHolder keyHolder = new GeneratedKeyHolder();

        jdbcTemplate.update(connection -> {
            PreparedStatement ps = connection.prepareStatement(sql, Statement.RETURN_GENERATED_KEYS);
            ps.setLong(1, message.getConversationId());
            ps.setString(2, message.getSender());
            ps.setString(3, message.getContent());
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

    public List<Message> findByConversationId(Long conversationId) {
        String sql = "SELECT * FROM messages WHERE conversation_id = ? ORDER BY created_at ASC";
        return jdbcTemplate.query(sql, messageRowMapper, conversationId);
    }
}
