-- Initial Seed Data for Intent Guard
-- Inserts default demo user USER_1 for hackathon prototype testing.

INSERT IGNORE INTO users (id, name, email, password, created_at)
VALUES ('USER_1', 'Alex Morgan', 'alex@intentguard.ai', 'intent123', NOW());
