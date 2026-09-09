package com.intentguard.backend.repository;

import com.intentguard.backend.model.User;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.jdbc.core.RowMapper;
import org.springframework.stereotype.Repository;

import java.sql.ResultSet;
import java.sql.SQLException;
import java.util.Optional;

/**
 * UserRepository using Spring JdbcTemplate (NO JPA / NO HIBERNATE).
 */
@Repository
public class UserRepository {

    private final JdbcTemplate jdbcTemplate;

    public UserRepository(JdbcTemplate jdbcTemplate) {
        this.jdbcTemplate = jdbcTemplate;
    }

    private final RowMapper<User> userRowMapper = (rs, rowNum) -> new User(
            rs.getString("id"),
            rs.getString("name"),
            rs.getString("email"),
            rs.getString("password"),
            rs.getTimestamp("created_at") != null ? rs.getTimestamp("created_at").toLocalDateTime() : null
    );

    public Optional<User> findById(String id) {
        String sql = "SELECT * FROM users WHERE id = ?";
        return jdbcTemplate.query(sql, userRowMapper, id).stream().findFirst();
    }

    public Optional<User> findByEmail(String email) {
        String sql = "SELECT * FROM users WHERE email = ?";
        return jdbcTemplate.query(sql, userRowMapper, email).stream().findFirst();
    }

    public int save(User user) {
        String sql = "INSERT INTO users (id, name, email, password, created_at) VALUES (?, ?, ?, ?, NOW())";
        return jdbcTemplate.update(sql, user.getId(), user.getName(), user.getEmail(), user.getPassword());
    }
}
