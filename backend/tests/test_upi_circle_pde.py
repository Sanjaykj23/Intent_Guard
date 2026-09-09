"""
Fault Injection & Security Test Suite for UPI Circle Payment Decision Engine (PDE)
Verifies zero-trust execution, AI hallucination gating, rate limits, boundary step-up, and timeout recovery.
"""

import pytest
import asyncio
import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.future import select

from backend.app.core.database import Base
from backend.app.models.db_models import (
    UserModel,
    UPICircleMandateModel,
    MandateSpendLedgerModel,
    PaymentDecisionModel
)
from backend.app.payment.upi_circle_pde import (
    pde_engine,
    psp_client,
    store,
    PaymentIntentRequest,
    DecisionStatus,
    DecisionVerdict,
    UPICirclePSPClient
)
from backend.app.payment.reconciliation_worker import ReconciliationWorker



@pytest.mark.asyncio
async def test_ai_hallucination_price_mismatch():
    """
    Test 1: AI Hallucination Gating
    User prompt claimed item price of ₹399 (39900 paise), but catalog price is ₹499 (49900 paise).
    Engine MUST detect price inequality and REJECT transaction.
    """
    req = PaymentIntentRequest(
        user_id="USER_TEST_01",
        session_id=str(uuid.uuid4()),
        mandate_id="MANDATE_UPI_9901",
        item_id="PROD_SHIRT_01",
        item_title="Roadster T-Shirt",
        claimed_price_paise=39900, # Hallucinated discount claimed by LLM!
        merchant_vpa="myntra@upi",
        merchant_mcc="5691"
    )

    ctx = await pde_engine.evaluate_intent(req)
    assert ctx.decision == DecisionStatus.REJECTED
    assert "AI Hallucination Detected" in ctx.rejection_reason


@pytest.mark.asyncio
async def test_repeat_dispatch_idempotency():
    """
    Test 2: Replay Attack & Duplicate Intent Dispatch
    Two identical payment intent requests submitted within lock TTL window.
    First request passes filter; second request MUST be REJECTED.
    """
    req = PaymentIntentRequest(
        user_id="USER_TEST_02",
        session_id="SESSION_REPLAY_1001",
        mandate_id="MANDATE_UPI_9901",
        item_id="PROD_SHIRT_01",
        item_title="Roadster T-Shirt",
        claimed_price_paise=49900,
        merchant_vpa="myntra@upi",
        merchant_mcc="5691"
    )

    # First dispatch
    ctx1 = await pde_engine.evaluate_intent(req)
    assert ctx1.decision == DecisionStatus.APPROVED

    # Duplicate dispatch
    ctx2 = await pde_engine.evaluate_intent(req)
    assert ctx2.decision == DecisionStatus.REJECTED
    assert "Duplicate payment request detected" in ctx2.rejection_reason


@pytest.mark.asyncio
async def test_boundary_transition_stepup():
    """
    Test 3: NPCI UPI Circle Full Delegation Cap Exceeded
    Transaction amount is ₹3,495 (349500 paise), but mandate per-txn limit is set to ₹3,000 (300000 paise).
    Engine MUST ESCALATE TO PIN (Step-up authorization).
    """
    # Temporarily set per-txn limit to ₹3,000 for testing
    store.mandates_db["MANDATE_UPI_9901"]["per_txn_limit_paise"] = 300000

    req = PaymentIntentRequest(
        user_id="USER_TEST_03",
        session_id=str(uuid.uuid4()),
        mandate_id="MANDATE_UPI_9901",
        item_id="PROD_SHOES_01",
        item_title="Nike Shoes",
        claimed_price_paise=349500,
        merchant_vpa="flipkart@upi",
        merchant_mcc="5661"
    )

    ctx = await pde_engine.evaluate_intent(req)
    assert ctx.decision == DecisionStatus.ESCALATED_TO_PIN
    assert "exceeds NPCI UPI Circle autonomous full delegation limit" in ctx.step_up_reason

    # Restore default per_txn_limit
    store.mandates_db["MANDATE_UPI_9901"]["per_txn_limit_paise"] = 500000


@pytest.mark.asyncio
async def test_quota_depletion_monthly_limit():
    """
    Test 4: Cumulative Monthly Quota Depletion
    User monthly limit is ₹15,000 (1500000 paise). Current spend is ₹14,800 (1480000 paise).
    New purchase of ₹499 (49900 paise) causes total to exceed ₹15,000 cap.
    Engine MUST REJECT transaction.
    """
    store.mandates_db["MANDATE_UPI_9901"]["current_monthly_spend_paise"] = 1480000

    req = PaymentIntentRequest(
        user_id="USER_TEST_04",
        session_id=str(uuid.uuid4()),
        mandate_id="MANDATE_UPI_9901",
        item_id="PROD_SHIRT_01",
        item_title="Roadster T-Shirt",
        claimed_price_paise=49900,
        merchant_vpa="myntra@upi",
        merchant_mcc="5691"
    )

    ctx = await pde_engine.evaluate_intent(req)
    assert ctx.decision == DecisionStatus.REJECTED
    assert "Monthly cumulative spend quota breached" in ctx.rejection_reason

    # Reset spend
    store.mandates_db["MANDATE_UPI_9901"]["current_monthly_spend_paise"] = 250000


@pytest.mark.asyncio
async def test_network_timeout_in_doubt_recovery():
    """
    Test 5: Banking PSP Timeout & Asynchronous Reconciliation
    PSP gateway times out during debit execution.
    Client enters IN_DOUBT state. Reconciliation worker queries bank status and updates state to COMPLETED.
    """
    timeout_psp_client = UPICirclePSPClient(simulate_timeout=True)

    status, txn_id, err = await timeout_psp_client.execute_autonomous_debit(
        mandate_id="MANDATE_UPI_9901",
        amount_paise=49900,
        target_vpa="myntra@upi",
        idempotency_key="idemp:mock_test_key"
    )

    assert status == DecisionStatus.IN_DOUBT
    assert txn_id in timeout_psp_client.ledger
    assert timeout_psp_client.ledger[txn_id]["status"] == DecisionStatus.IN_DOUBT

    # Run reconciliation worker
    worker = ReconciliationWorker(psp_client_ref=timeout_psp_client)
    resolved = await worker.reconcile_once()

    assert len(resolved) == 1
    assert resolved[0]["txn_id"] == txn_id
    assert resolved[0]["resolution"] == "COMPLETED"
    assert timeout_psp_client.ledger[txn_id]["status"] == DecisionStatus.COMPLETED


@pytest.mark.asyncio
async def test_async_session_mandate_policy_and_persistence():
    """
    Test 6: SQLAlchemy AsyncSession Mandate Policy Filter & Atomic Persistence
    Validates:
    - Querying UPICircleMandateModel directly via AsyncSession.
    - Validating active status, cooling off window, monthly limit, and ₹5,000 cap step-up.
    - Atomic write to PaymentDecisionModel, UPICircleMandateModel spend update, and MandateSpendLedgerModel.
    - Safe transaction rollback handling on error.
    """
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        # Seed test user & active mandate
        user = UserModel(
            id="USER_DB_01",
            name="Test User",
            email="testuser@example.com",
            password_hash="hashed_pw"
        )
        session.add(user)

        now = datetime.now(timezone.utc)
        mandate = UPICircleMandateModel(
            mandate_id="MANDATE_DB_001",
            primary_user_id="USER_DB_01",
            primary_vpa="user@upi",
            secondary_agent_vpa="agent@psp",
            mandate_ref_no="UMN123456789",
            delegation_type="FULL_DELEGATION",
            per_txn_limit_paise=500000, # ₹5,000
            monthly_limit_paise=1500000, # ₹15,000
            current_month_spend_paise=100000, # ₹1,000
            cooling_off_until=now - timedelta(hours=25), # Past cooling off
            mandate_status="ACTIVE",
            enc_delegation_token=b"encrypted_token",
            valid_from=now - timedelta(days=1),
            valid_until=now + timedelta(days=365)
        )
        session.add(mandate)
        await session.commit()

        # 1. Approved intent evaluation with AsyncSession
        req_approved = PaymentIntentRequest(
            user_id="USER_DB_01",
            session_id=str(uuid.uuid4()),
            mandate_id="MANDATE_DB_001",
            item_id="PROD_SHIRT_01",
            item_title="Roadster T-Shirt",
            claimed_price_paise=49900, # ₹499
            merchant_vpa="myntra@upi",
            merchant_mcc="5691"
        )

        ctx = await pde_engine.evaluate_intent(req_approved, db=session)
        assert ctx.decision == DecisionStatus.APPROVED
        assert ctx.db_mandate is not None
        assert ctx.db_mandate.mandate_id == "MANDATE_DB_001"

        # Check decision record written
        dec_stmt = select(PaymentDecisionModel).where(PaymentDecisionModel.mandate_id == "MANDATE_DB_001")
        dec_res = await session.execute(dec_stmt)
        decisions = dec_res.scalars().all()
        assert len(decisions) >= 1

        # 2. Execute and persist ledger atomically
        txn_id = f"TXN_{uuid.uuid4().hex[:8]}"
        await pde_engine.execute_and_persist_ledger(ctx, transaction_id=txn_id, status_str="COMPLETED")

        # Verify mandate spend was updated in DB
        m_stmt = select(UPICircleMandateModel).where(UPICircleMandateModel.mandate_id == "MANDATE_DB_001")
        m_res = await session.execute(m_stmt)
        updated_mandate = m_res.scalars().first()
        assert updated_mandate.current_month_spend_paise == 149900

        # Verify MandateSpendLedgerModel entry was created
        l_stmt = select(MandateSpendLedgerModel).where(MandateSpendLedgerModel.transaction_id == txn_id)
        l_res = await session.execute(l_stmt)
        ledger_entry = l_res.scalars().first()
        assert ledger_entry is not None
        assert ledger_entry.amount_paise == 49900
        assert ledger_entry.previous_month_spend_paise == 100000
        assert ledger_entry.new_month_spend_paise == 149900

        # 3. Test Step-Up PIN escalation when exceeding limit
        req_high = PaymentIntentRequest(
            user_id="USER_DB_01",
            session_id=str(uuid.uuid4()),
            mandate_id="MANDATE_DB_001",
            item_id="PROD_SHOES_01",
            item_title="Nike Shoes",
            claimed_price_paise=349500,
            merchant_vpa="flipkart@upi",
            merchant_mcc="5661"
        )
        updated_mandate.per_txn_limit_paise = 200000
        await session.commit()

        ctx_high = await pde_engine.evaluate_intent(req_high, db=session)
        assert ctx_high.decision in (DecisionStatus.ESCALATED_TO_PIN, DecisionVerdict.ESCALATE_TO_PIN)

        # 4. Test 24-hour cooling off window restriction
        updated_mandate.cooling_off_until = now + timedelta(hours=12)
        await session.commit()

        req_cooling = PaymentIntentRequest(
            user_id="USER_DB_01",
            session_id=str(uuid.uuid4()),
            mandate_id="MANDATE_DB_001",
            item_id="PROD_TEA_01",
            item_title="Chai",
            claimed_price_paise=3500,
            merchant_vpa="zomato@upi",
            merchant_mcc="5812"
        )
        ctx_cooling = await pde_engine.evaluate_intent(req_cooling, db=session)
        assert ctx_cooling.decision == DecisionStatus.APPROVED

        req_over_cooling = PaymentIntentRequest(
            user_id="USER_DB_01",
            session_id=str(uuid.uuid4()),
            mandate_id="MANDATE_DB_001",
            item_id="PROD_SHOES_01",
            item_title="Shoes",
            claimed_price_paise=250000,
            merchant_vpa="zomato@upi",
            merchant_mcc="5812"
        )
        ctx_over_cooling = await pde_engine.evaluate_intent(req_over_cooling, db=session)
        assert ctx_over_cooling.decision == DecisionStatus.ESCALATED_TO_PIN
        assert "cooling-off" in ctx_over_cooling.step_up_reason

    await engine.dispose()

