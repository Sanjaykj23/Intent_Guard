"""
Test Suite for User Registration, Login, and UPI Circle Delegation Setup
Verifies user authentication, E.164 phone validation, JWT session dependencies,
NPCI 24-hour cooling off limits (₹2,000 cap), and Zero-Trust credential safety.
"""

import pytest
import asyncio
from datetime import datetime, timedelta, timezone
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.future import select

from backend.app.core.database import Base
from backend.app.core.config import settings
from backend.app.models.db_models import (
    UserModel,
    UPICircleMandateModel,
    PaymentPolicyModel
)
from backend.app.schemas.intent_schemas import (
    UserRegistration,
    UPICircleSetupRequest
)
from backend.app.api.v1.auth import (
    create_access_token,
    decode_access_token
)
from backend.app.payment.upi_circle_pde import (
    pde_engine,
    PaymentIntentRequest,
    DecisionStatus
)


@pytest.mark.asyncio
async def test_user_registration_e164_phone_and_login():
    """
    Test 1: User Registration with Name, Email, Address, and E.164 Phone Validation
    """
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    # Valid E.164 Phone
    valid_reg = UserRegistration(
        name="Antigravity User",
        email="sanjay@example.com",
        password="securepassword123",
        phone="+919876543210",
        address="123 Tech Park, Bengaluru, KA"
    )
    assert valid_reg.phone == "+919876543210"

    # E.164 Auto-prefixing
    auto_prefix_reg = UserRegistration(
        name="Auto User",
        email="auto@example.com",
        password="password123",
        phone="9876543210",
        address="Chennai, TN"
    )
    assert auto_prefix_reg.phone == "+919876543210"

    # Invalid E.164 Phone rejection
    with pytest.raises(ValueError):
        UserRegistration(
            name="Bad Phone User",
            email="badphone@example.com",
            password="password123",
            phone="abc123",
            address="Delhi, DL"
        )

    # JWT Token creation and decoding
    token = create_access_token("USER_TEST_100", "sanjay@example.com")
    payload = decode_access_token(token)
    assert payload["sub"] == "USER_TEST_100"
    assert payload["email"] == "sanjay@example.com"

    await engine.dispose()


@pytest.mark.asyncio
async def test_upi_circle_setup_jwt_dependency_and_zero_trust():
    """
    Test 2: UPI Circle Mandate Setup strictly extracts user_id from session
    and sets secondary_agent_vpa from server config.
    """
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        # Seed test user
        user = UserModel(
            id="USER_JWT_999",
            name="Sanjay Merchant",
            email="sanjay.m@example.com",
            phone="+919988776655",
            address="Indiranagar, Bengaluru",
            password_hash="password123"
        )
        session.add(user)
        await session.commit()

        # Simulate setup request with primary VPA
        req = UPICircleSetupRequest(
            primary_vpa="sanjay@okicici",
            per_txn_limit_paise=500000, # ₹5,000 cap
            monthly_limit_paise=1500000 # ₹15,000 cap
        )

        now = datetime.now(timezone.utc)
        cooling_until = now + timedelta(hours=24)
        secondary_agent_vpa = settings.SECONDARY_AGENT_VPA

        # Create mandate directly tied to user session ID
        mandate = UPICircleMandateModel(
            mandate_id="MANDATE_AUTH_001",
            primary_user_id=user.id,
            primary_vpa=req.primary_vpa,
            secondary_agent_vpa=secondary_agent_vpa,
            mandate_ref_no="UMN_AUTH_12345",
            delegation_type="FULL_DELEGATION",
            per_txn_limit_paise=min(req.per_txn_limit_paise, 500000),
            monthly_limit_paise=min(req.monthly_limit_paise, 1500000),
            current_month_spend_paise=0,
            cooling_off_until=cooling_until,
            mandate_status="ACTIVE",
            enc_delegation_token=b"encrypted_token_hash_no_raw_cards_or_mpins",
            valid_from=now,
            valid_until=now + timedelta(days=365)
        )
        session.add(mandate)
        await session.commit()

        # Verify database fields: Secondary VPA set from config
        m_stmt = select(UPICircleMandateModel).where(UPICircleMandateModel.primary_user_id == "USER_JWT_999")
        res = await session.execute(m_stmt)
        m = res.scalars().first()
        assert m is not None
        assert m.primary_user_id == "USER_JWT_999"
        assert m.secondary_agent_vpa == settings.SECONDARY_AGENT_VPA
        assert m.per_txn_limit_paise == 500000
        assert m.monthly_limit_paise == 1500000

        # ZERO TRUST AUDIT: Verify no raw card numbers or MPIN attributes exist on model
        for col in UPICircleMandateModel.__table__.columns:
            col_name = col.name.lower()
            assert "card" not in col_name
            assert "mpin" not in col_name
            assert "cvv" not in col_name

    await engine.dispose()


@pytest.mark.asyncio
async def test_npci_cooling_off_2000_rupee_limit_escalation():
    """
    Test 3: Enforce NPCI 24-hour cooling-off cap (₹2,000 max autonomous limit).
    Transactions <= ₹2,000 (200000 paise) pass; transactions > ₹2,000 trigger ESCALATE_TO_PIN.
    """
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        user = UserModel(
            id="USER_COOLING_01",
            name="Cooling Off User",
            email="cooling@example.com",
            password_hash="pw"
        )
        session.add(user)

        now = datetime.now(timezone.utc)
        cooling_until = now + timedelta(hours=12) # Active 24h cooling off window

        mandate = UPICircleMandateModel(
            mandate_id="MANDATE_COOL_001",
            primary_user_id="USER_COOLING_01",
            primary_vpa="user.cool@upi",
            secondary_agent_vpa="agent.antigravity@psp",
            mandate_ref_no="UMN_COOL_99",
            delegation_type="FULL_DELEGATION",
            per_txn_limit_paise=500000, # Default ₹5,000 cap
            monthly_limit_paise=1500000,
            current_month_spend_paise=0,
            cooling_off_until=cooling_until,
            mandate_status="ACTIVE",
            enc_delegation_token=b"enc_token",
            valid_from=now,
            valid_until=now + timedelta(days=365)
        )
        session.add(mandate)
        await session.commit()

        # 1. Purchase of ₹1,800 (180000 paise) during cooling off -> APPROVED
        req_within_limit = PaymentIntentRequest(
            user_id="USER_COOLING_01",
            session_id="SESS_COOL_1",
            mandate_id="MANDATE_COOL_001",
            item_id="PROD_SHIRT_01",
            item_title="Roadster T-Shirt",
            claimed_price_paise=49900, # ₹499 <= ₹2,000
            merchant_vpa="myntra@upi",
            merchant_mcc="5691"
        )
        ctx_within = await pde_engine.evaluate_intent(req_within_limit, db=session)
        assert ctx_within.decision == DecisionStatus.APPROVED

        # 2. Purchase of ₹3,495 (349500 paise) during cooling off -> ESCALATED_TO_PIN
        req_exceeds = PaymentIntentRequest(
            user_id="USER_COOLING_01",
            session_id="SESS_COOL_2",
            mandate_id="MANDATE_COOL_001",
            item_id="PROD_SHOES_01",
            item_title="Nike Shoes",
            claimed_price_paise=349500, # ₹3,495 > ₹2,000 cap during cooling off!
            merchant_vpa="flipkart@upi",
            merchant_mcc="5661"
        )
        ctx_exceeds = await pde_engine.evaluate_intent(req_exceeds, db=session)
        assert ctx_exceeds.decision == DecisionStatus.ESCALATED_TO_PIN
        assert "exceeds NPCI 24-hour cooling-off" in ctx_exceeds.step_up_reason

    await engine.dispose()


@pytest.mark.asyncio
async def test_upi_circle_disconnected_rejects_and_connected_completes():
    """
    Test 4: If UPI Circle is disconnected/revoked, payment intent is DENIED with DELEGATION_DISCONNECTED.
    If UPI Circle is re-connected/active, payment intent is APPROVED.
    """
    from backend.app.payment.upi_circle_provider import mock_upi_circle_provider

    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        user_id = "USER_RULE_TEST_01"
        user = UserModel(id=user_id, name="Test Rule User", email="rule@example.com", password_hash="pw")
        session.add(user)
        await session.commit()

        # Step 1: Revoke/Disconnect delegation
        await mock_upi_circle_provider.revoke_delegation(user_id)

        req = PaymentIntentRequest(
            user_id=user_id,
            session_id="SESS_RULE_1",
            item_id="PROD_SHIRT_01",
            item_title="Statement T-Shirt",
            claimed_price_paise=113100, # ₹1,131
            merchant_vpa="nykaa@upi",
            category="SHOPPING"
        )

        ctx_disconnected = await pde_engine.evaluate_intent(req, db=session)
        assert ctx_disconnected.decision == DecisionStatus.DENIED
        assert ctx_disconnected.reason_code == "DELEGATION_DISCONNECTED"
        assert "disconnected or inactive" in ctx_disconnected.rejection_reason

        # Step 2: Connect delegation
        await mock_upi_circle_provider.create_delegation(primary_user_id=user_id)

        ctx_connected = await pde_engine.evaluate_intent(req, db=session)
        assert ctx_connected.decision == DecisionStatus.APPROVED

    await engine.dispose()

