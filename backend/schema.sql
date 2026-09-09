-- =====================================================================
-- IntentGuard Relational Database Schema (SQL Reference File)
-- System: NPCI UPI Circle & Autonomous AI Agent Safety Framework
-- Target Engine: PostgreSQL / SQLite (ANSI SQL Compliant)
-- =====================================================================

-- ---------------------------------------------------------------------
-- 1. USERS TABLE
-- Core identity tracking account status, KYC tier, and authentication credentials.
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS users (
    id VARCHAR(64) PRIMARY KEY,
    name VARCHAR(128) NOT NULL,
    email VARCHAR(128) UNIQUE NOT NULL,
    phone VARCHAR(32),
    address TEXT,
    phone_hash VARCHAR(128) UNIQUE,
    email_hash VARCHAR(128) UNIQUE,
    password_hash VARCHAR(256) NOT NULL,
    account_status VARCHAR(32) DEFAULT 'ACTIVE',
    kyc_tier VARCHAR(32) DEFAULT 'MINIMUM',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMP NULL
);

CREATE INDEX IF NOT EXISTS ix_users_id ON users (id);
CREATE INDEX IF NOT EXISTS ix_users_email ON users (email);
CREATE INDEX IF NOT EXISTS ix_users_phone_hash ON users (phone_hash);
CREATE INDEX IF NOT EXISTS ix_users_email_hash ON users (email_hash);
CREATE INDEX IF NOT EXISTS ix_users_account_status ON users (account_status);

-- ---------------------------------------------------------------------
-- 2. USER DEVICES TABLE
-- Hardware bindings for zero-trust client device verification.
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS user_devices (
    device_id VARCHAR(64) PRIMARY KEY,
    user_id VARCHAR(64) NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    device_fingerprint_hash VARCHAR(128) NOT NULL,
    push_token_enc BYTEA NULL,
    is_trusted BOOLEAN DEFAULT TRUE,
    last_active_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS ix_user_devices_device_id ON user_devices (device_id);
CREATE INDEX IF NOT EXISTS ix_user_devices_user_id ON user_devices (user_id);

-- ---------------------------------------------------------------------
-- 3. USER UPI PROFILES TABLE
-- Tokenized bank account handles and masked account numbers.
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS user_upi_profiles (
    profile_id VARCHAR(64) PRIMARY KEY,
    user_id VARCHAR(64) NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    primary_vpa VARCHAR(128) UNIQUE NOT NULL,
    ifsc_code VARCHAR(11) NOT NULL,
    account_number_masked VARCHAR(16) NOT NULL,
    tokenized_handle_ref VARCHAR(128) NOT NULL,
    is_primary BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS ix_user_upi_profiles_profile_id ON user_upi_profiles (profile_id);
CREATE INDEX IF NOT EXISTS ix_user_upi_profiles_user_id ON user_upi_profiles (user_id);
CREATE INDEX IF NOT EXISTS ix_user_upi_profiles_primary_vpa ON user_upi_profiles (primary_vpa);

-- ---------------------------------------------------------------------
-- 4. UPI CIRCLE MANDATES TABLE
-- NPCI UPI Circle delegation lifecycle, limits, and 24h cooling-off window.
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS upi_circle_mandates (
    mandate_id VARCHAR(64) PRIMARY KEY,
    primary_user_id VARCHAR(64) NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    primary_vpa VARCHAR(128) NOT NULL,
    secondary_agent_vpa VARCHAR(128) NOT NULL,
    mandate_ref_no VARCHAR(64) UNIQUE NOT NULL,
    delegation_type VARCHAR(32) DEFAULT 'FULL_DELEGATION',
    per_txn_limit_paise BIGINT DEFAULT 500000,   -- NPCI Cap: Rs 5,000 (500,000 paise)
    monthly_limit_paise BIGINT DEFAULT 1500000, -- NPCI Cap: Rs 15,000 (1,500,000 paise)
    current_month_spend_paise BIGINT DEFAULT 0,
    last_spend_reset_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    cooling_off_until TIMESTAMP NOT NULL,
    mandate_status VARCHAR(32) DEFAULT 'PENDING_AUTH',
    enc_delegation_token BYTEA NOT NULL,
    valid_from TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    valid_until TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS ix_upi_circle_mandates_mandate_id ON upi_circle_mandates (mandate_id);
CREATE INDEX IF NOT EXISTS ix_upi_circle_mandates_primary_user_id ON upi_circle_mandates (primary_user_id);
CREATE INDEX IF NOT EXISTS ix_upi_circle_mandates_primary_vpa ON upi_circle_mandates (primary_vpa);
CREATE INDEX IF NOT EXISTS ix_upi_circle_mandates_secondary_agent_vpa ON upi_circle_mandates (secondary_agent_vpa);
CREATE INDEX IF NOT EXISTS ix_upi_circle_mandates_mandate_status ON upi_circle_mandates (mandate_status);

-- ---------------------------------------------------------------------
-- 5. MANDATE SPEND LEDGER TABLE
-- Immutable debit/refund audit entries for mandate dispute resolution.
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS mandate_spend_ledger (
    ledger_id VARCHAR(64) PRIMARY KEY,
    mandate_id VARCHAR(64) NOT NULL REFERENCES upi_circle_mandates(mandate_id) ON DELETE CASCADE,
    transaction_id VARCHAR(64) UNIQUE NOT NULL,
    amount_paise BIGINT NOT NULL,
    entry_type VARCHAR(32) DEFAULT 'DEBIT',
    merchant_vpa VARCHAR(128) NOT NULL,
    merchant_mcc VARCHAR(8) NOT NULL,
    previous_month_spend_paise BIGINT DEFAULT 0,
    new_month_spend_paise BIGINT DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS ix_mandate_spend_ledger_ledger_id ON mandate_spend_ledger (ledger_id);
CREATE INDEX IF NOT EXISTS ix_mandate_spend_ledger_mandate_id ON mandate_spend_ledger (mandate_id);
CREATE INDEX IF NOT EXISTS ix_mandate_spend_ledger_created_at ON mandate_spend_ledger (created_at);

-- ---------------------------------------------------------------------
-- 6. PAYMENT DECISIONS TABLE
-- Real-time Payment Decision Engine (PDE) verdicts and execution traces.
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS payment_decisions (
    decision_id VARCHAR(64) PRIMARY KEY,
    user_id VARCHAR(64) REFERENCES users(id) ON DELETE SET NULL,
    mandate_id VARCHAR(64) REFERENCES upi_circle_mandates(mandate_id) ON DELETE SET NULL,
    session_id VARCHAR(64) NULL,
    idempotency_key VARCHAR(128) NOT NULL,
    item_id VARCHAR(64) NOT NULL,
    item_title VARCHAR(256) NOT NULL,
    claimed_price_paise BIGINT NOT NULL,
    merchant_vpa VARCHAR(128) NOT NULL,
    merchant_mcc VARCHAR(8) NOT NULL,
    decision VARCHAR(32) NOT NULL,
    rejection_reason TEXT NULL,
    step_up_reason TEXT NULL,
    execution_trace_json TEXT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS ix_payment_decisions_decision_id ON payment_decisions (decision_id);
CREATE INDEX IF NOT EXISTS ix_payment_decisions_user_id ON payment_decisions (user_id);
CREATE INDEX IF NOT EXISTS ix_payment_decisions_mandate_id ON payment_decisions (mandate_id);
CREATE INDEX IF NOT EXISTS ix_payment_decisions_idempotency_key ON payment_decisions (idempotency_key);
CREATE INDEX IF NOT EXISTS ix_payment_decisions_decision ON payment_decisions (decision);
CREATE INDEX IF NOT EXISTS ix_payment_decisions_created_at ON payment_decisions (created_at);

-- ---------------------------------------------------------------------
-- 7. PAYMENT POLICIES TABLE
-- Per-user spend policy configurations and threshold limits.
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS payment_policies (
    policy_id VARCHAR(64) PRIMARY KEY,
    user_id VARCHAR(64) NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    daily_limit_paise BIGINT DEFAULT 500000,
    transaction_limit_paise BIGINT DEFAULT 100000,
    auto_approval_threshold_paise BIGINT DEFAULT 20000,
    allowed_categories_json TEXT DEFAULT '["apparel", "electronics", "food", "recharge"]',
    policy_version INTEGER DEFAULT 1,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS ix_payment_policies_policy_id ON payment_policies (policy_id);

-- ---------------------------------------------------------------------
-- 8. PAYMENT TOKENS METADATA TABLE
-- Metadata references for Razorpay tokenized recurring mandates.
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS payment_tokens_metadata (
    id VARCHAR(64) PRIMARY KEY,
    user_id VARCHAR(64) NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    razorpay_customer_id VARCHAR(128) NOT NULL,
    razorpay_mandate_token_ref VARCHAR(128) NOT NULL,
    token_hash_sha256 VARCHAR(128) NOT NULL,
    status VARCHAR(32) DEFAULT 'ACTIVE',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS ix_payment_tokens_metadata_id ON payment_tokens_metadata (id);

-- ---------------------------------------------------------------------
-- 9. QUOTES TABLE
-- Locked merchant quotes for zero-tolerance price matching validation.
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS quotes (
    quote_id VARCHAR(64) PRIMARY KEY,
    user_id VARCHAR(64) NOT NULL,
    merchant_name VARCHAR(128) NOT NULL,
    product_name VARCHAR(256) NOT NULL,
    price_paise BIGINT NOT NULL,
    product_url TEXT NOT NULL,
    expires_at TIMESTAMP NOT NULL,
    quote_hash VARCHAR(128) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS ix_quotes_quote_id ON quotes (quote_id);

-- ---------------------------------------------------------------------
-- 10. AUDIT LOGS TABLE
-- Cryptographic SHA-256 tamper-evident audit hash chain.
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS audit_logs (
    id SERIAL PRIMARY KEY,
    event_id VARCHAR(64),
    event_type VARCHAR(64) NOT NULL,
    payload_json TEXT NOT NULL,
    previous_hash VARCHAR(128) NOT NULL,
    current_hash VARCHAR(128) NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS ix_audit_logs_event_id ON audit_logs (event_id);
