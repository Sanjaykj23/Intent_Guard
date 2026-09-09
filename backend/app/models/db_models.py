from datetime import datetime
from sqlalchemy import Column, String, Integer, DateTime, Text, ForeignKey, BigInteger
from sqlalchemy.orm import relationship
from backend.app.core.database import Base

class UserModel(Base):
    __tablename__ = "users"

    id = Column(String(64), primary_key=True, index=True)
    name = Column(String(128), nullable=False)
    email = Column(String(128), unique=True, index=True, nullable=False)
    password_hash = Column(String(256), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    policies = relationship("PaymentPolicyModel", back_populates="user", cascade="all, delete-orphan")
    tokens = relationship("PaymentTokenMetadataModel", back_populates="user", cascade="all, delete-orphan")

class PaymentPolicyModel(Base):
    __tablename__ = "payment_policies"

    policy_id = Column(String(64), primary_key=True, index=True)
    user_id = Column(String(64), ForeignKey("users.id"), nullable=False)
    daily_limit_paise = Column(BigInteger, default=500000) # Default ₹5,000
    transaction_limit_paise = Column(BigInteger, default=100000) # Default ₹1,000
    auto_approval_threshold_paise = Column(BigInteger, default=20000) # Default ₹200
    allowed_categories_json = Column(Text, default='["apparel", "electronics", "food", "recharge"]')
    policy_version = Column(Integer, default=1)
    updated_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("UserModel", back_populates="policies")

class PaymentTokenMetadataModel(Base):
    __tablename__ = "payment_tokens_metadata"

    id = Column(String(64), primary_key=True, index=True)
    user_id = Column(String(64), ForeignKey("users.id"), nullable=False)
    razorpay_customer_id = Column(String(128), nullable=False)
    razorpay_mandate_token_ref = Column(String(128), nullable=False)
    token_hash_sha256 = Column(String(128), nullable=False) # Cryptographic hash of token
    status = Column(String(32), default="ACTIVE")
    created_at = Column(DateTime, default=datetime.utcnow)

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
    created_at = Column(DateTime, default=datetime.utcnow)

class AuditLogModel(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    event_id = Column(String(64), index=True)
    event_type = Column(String(64), nullable=False)
    payload_json = Column(Text, nullable=False)
    previous_hash = Column(String(128), nullable=False)
    current_hash = Column(String(128), nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)
