from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, DateTime, Text, ForeignKey, BigInteger, Boolean, LargeBinary
from sqlalchemy.orm import relationship
from backend.app.core.database import Base

def utc_now():
    return datetime.now(timezone.utc)

# =====================================================================
# 1. USER IDENTITY & AUTHENTICATION
# =====================================================================

class UserModel(Base):
    __tablename__ = "users"

    id = Column(String(64), primary_key=True, index=True)
    name = Column(String(128), nullable=False)
    email = Column(String(128), unique=True, index=True, nullable=False)
    phone = Column(String(32), nullable=True)                                 # E.164 mobile number e.g. +919876543210
    address = Column(Text, nullable=True)                                     # Delivery address
    phone_hash = Column(String(128), unique=True, index=True, nullable=True) # HMAC-SHA256 hashed phone
    email_hash = Column(String(128), unique=True, index=True, nullable=True) # HMAC-SHA256 hashed email
    password_hash = Column(String(256), nullable=False)
    account_status = Column(String(32), default="ACTIVE", index=True) # ACTIVE, SUSPENDED, BLOCKED
    kyc_tier = Column(String(32), default="MINIMUM")                  # MINIMUM, FULL_KYC
    created_at = Column(DateTime, default=utc_now)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now)
    deleted_at = Column(DateTime, nullable=True)

    policies = relationship("PaymentPolicyModel", back_populates="user", cascade="all, delete-orphan")
    tokens = relationship("PaymentTokenMetadataModel", back_populates="user", cascade="all, delete-orphan")
    devices = relationship("UserDeviceModel", back_populates="user", cascade="all, delete-orphan")
    upi_profiles = relationship("UserUPIProfileModel", back_populates="user", cascade="all, delete-orphan")
    mandates = relationship("UPICircleMandateModel", back_populates="primary_user", cascade="all, delete-orphan")


# =====================================================================
# 2. TRUSTED DEVICE BINDINGS (PCI-DSS & SECURITY LAYER)
# =====================================================================

class UserDeviceModel(Base):
    __tablename__ = "user_devices"

    device_id = Column(String(64), primary_key=True, index=True)
    user_id = Column(String(64), ForeignKey("users.id"), nullable=False, index=True)
    device_fingerprint_hash = Column(String(128), nullable=False) # HMAC of hardware serial + IMEI
    push_token_enc = Column(LargeBinary, nullable=True)           # Encrypted push token
    is_trusted = Column(Boolean, default=True)
    last_active_at = Column(DateTime, default=utc_now)
    created_at = Column(DateTime, default=utc_now)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now)

    user = relationship("UserModel", back_populates="devices")


# =====================================================================
# 3. TOKENIZED UPI BANK PROFILES
# =====================================================================

class UserUPIProfileModel(Base):
    __tablename__ = "user_upi_profiles"

    profile_id = Column(String(64), primary_key=True, index=True)
    user_id = Column(String(64), ForeignKey("users.id"), nullable=False, index=True)
    primary_vpa = Column(String(128), unique=True, index=True, nullable=False) # e.g. "sanjay@okicici"
    ifsc_code = Column(String(11), nullable=False)                            # Bank IFSC
    account_number_masked = Column(String(16), nullable=False)                # e.g. "XXXX1234"
    tokenized_handle_ref = Column(String(128), nullable=False)                # Bank PSP Vault token
    is_primary = Column(Boolean, default=True)
    created_at = Column(DateTime, default=utc_now)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now)

    user = relationship("UserModel", back_populates="upi_profiles")


# =====================================================================
# 4. NPCI UPI CIRCLE MANDATES (DELEGATION LIFECYCLE)
# =====================================================================

class UPICircleMandateModel(Base):
    __tablename__ = "upi_circle_mandates"

    mandate_id = Column(String(64), primary_key=True, index=True)
    primary_user_id = Column(String(64), ForeignKey("users.id"), nullable=False, index=True)
    primary_vpa = Column(String(128), nullable=False, index=True)
    secondary_agent_vpa = Column(String(128), nullable=False, index=True) # e.g. "agent.antigravity@psp"
    mandate_ref_no = Column(String(64), unique=True, nullable=False)       # NPCI UMN
    delegation_type = Column(String(32), default="FULL_DELEGATION")       # FULL_DELEGATION | PARTIAL_DELEGATION
    per_txn_limit_paise = Column(BigInteger, default=500000)               # Max ₹5,000 (500,000 paise)
    monthly_limit_paise = Column(BigInteger, default=1500000)             # Max ₹15,000 (1,500,000 paise)
    current_month_spend_paise = Column(BigInteger, default=0)
    last_spend_reset_at = Column(DateTime, default=utc_now)
    cooling_off_until = Column(DateTime, nullable=False)                   # NPCI 24h cooling off
    mandate_status = Column(String(32), default="PENDING_AUTH", index=True)# PENDING_AUTH, ACTIVE, PAUSED, REVOKED, EXPIRED
    enc_delegation_token = Column(LargeBinary, nullable=False)            # Encrypted PSP delegation token
    valid_from = Column(DateTime, default=utc_now)
    valid_until = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=utc_now)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now)

    primary_user = relationship("UserModel", back_populates="mandates")
    ledger_entries = relationship("MandateSpendLedgerModel", back_populates="mandate", cascade="all, delete-orphan")

    @property
    def current_monthly_spend_paise(self) -> int:
        return self.current_month_spend_paise or 0

    @current_monthly_spend_paise.setter
    def current_monthly_spend_paise(self, value: int):
        self.current_month_spend_paise = value

    @property
    def mandate_state(self) -> str:
        return self.mandate_status or "PENDING_AUTH"


# =====================================================================
# 5. IMMUTABLE MANDATE SPEND LEDGER (DISPUTE RESOLUTION)
# =====================================================================

class MandateSpendLedgerModel(Base):
    __tablename__ = "mandate_spend_ledger"

    ledger_id = Column(String(64), primary_key=True, index=True)
    mandate_id = Column(String(64), ForeignKey("upi_circle_mandates.mandate_id"), nullable=False, index=True)
    transaction_id = Column(String(64), unique=True, nullable=False)
    amount_paise = Column(BigInteger, nullable=False)
    entry_type = Column(String(32), default="DEBIT")                      # DEBIT, REFUND, ADJUSTMENT
    merchant_vpa = Column(String(128), nullable=False)
    merchant_mcc = Column(String(8), nullable=False)
    previous_month_spend_paise = Column(BigInteger, default=0)
    new_month_spend_paise = Column(BigInteger, default=0)
    created_at = Column(DateTime, default=utc_now, index=True)

    mandate = relationship("UPICircleMandateModel", back_populates="ledger_entries")


# =====================================================================
# 5b. PAYMENT DECISION ENGINE RECORD (AUDIT & VERDICT PERSISTENCE)
# =====================================================================

class PaymentDecisionModel(Base):
    __tablename__ = "payment_decisions"

    decision_id = Column(String(64), primary_key=True, index=True)
    user_id = Column(String(64), ForeignKey("users.id"), nullable=True, index=True)
    mandate_id = Column(String(64), ForeignKey("upi_circle_mandates.mandate_id"), nullable=True, index=True)
    session_id = Column(String(64), nullable=True)
    idempotency_key = Column(String(128), index=True, nullable=False)
    item_id = Column(String(64), nullable=False)
    item_title = Column(String(256), nullable=False)
    claimed_price_paise = Column(BigInteger, nullable=False)
    merchant_vpa = Column(String(128), nullable=False)
    merchant_mcc = Column(String(8), nullable=False)
    decision = Column(String(32), nullable=False, index=True)
    rejection_reason = Column(Text, nullable=True)
    step_up_reason = Column(Text, nullable=True)
    execution_trace_json = Column(Text, nullable=True)
    created_at = Column(DateTime, default=utc_now, index=True)



# =====================================================================
# 6. LEGACY COMPATIBILITY MODELS (POLICIES, TOKENS, QUOTES, AUDIT)
# =====================================================================

class PaymentPolicyModel(Base):
    __tablename__ = "payment_policies"

    policy_id = Column(String(64), primary_key=True, index=True)
    user_id = Column(String(64), ForeignKey("users.id"), nullable=False)
    daily_limit_paise = Column(BigInteger, default=500000) # Default ₹5,000
    transaction_limit_paise = Column(BigInteger, default=100000) # Default ₹1,000
    auto_approval_threshold_paise = Column(BigInteger, default=20000) # Default ₹200
    allowed_categories_json = Column(Text, default='["apparel", "electronics", "food", "recharge"]')
    policy_version = Column(Integer, default=1)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now)

    user = relationship("UserModel", back_populates="policies")


class PaymentTokenMetadataModel(Base):
    __tablename__ = "payment_tokens_metadata"

    id = Column(String(64), primary_key=True, index=True)
    user_id = Column(String(64), ForeignKey("users.id"), nullable=False)
    razorpay_customer_id = Column(String(128), nullable=False)
    razorpay_mandate_token_ref = Column(String(128), nullable=False)
    token_hash_sha256 = Column(String(128), nullable=False)
    status = Column(String(32), default="ACTIVE")
    created_at = Column(DateTime, default=utc_now)

    user = relationship("UserModel", back_populates="tokens")


class QuoteModel(Base):
    __tablename__ = "quotes"

    quote_id = Column(String(64), primary_key=True, index=True)
    user_id = Column(String(64), nullable=False)
    merchant_name = Column(String(128), nullable=False)
    product_name = Column(String(256), nullable=False)
    price_paise = Column(BigInteger, nullable=False)
    product_url = Column(Text, nullable=False)
    expires_at = Column(DateTime, nullable=False)
    quote_hash = Column(String(128), nullable=False)
    created_at = Column(DateTime, default=utc_now)


class AuditLogModel(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    event_id = Column(String(64), index=True)
    event_type = Column(String(64), nullable=False)
    payload_json = Column(Text, nullable=False)
    previous_hash = Column(String(128), nullable=False)
    current_hash = Column(String(128), nullable=False)
    timestamp = Column(DateTime, default=utc_now)
