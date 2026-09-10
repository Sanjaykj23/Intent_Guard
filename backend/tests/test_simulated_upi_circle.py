"""
Automated Test Suite for Hackathon Simulated UPI Circle & Payment Decision Engine
Tests all 12 required test cases for delegated payments, limit caps, category rules,
mock bank debits, risk approvals, and transaction splitting protection.
"""

import pytest
import asyncio
import uuid
from datetime import datetime, timedelta, timezone

from backend.app.payment.mock_bank import mock_bank
from backend.app.payment.merchant_registry import merchant_registry
from backend.app.payment.upi_circle_provider import mock_upi_circle_provider
from backend.app.payment.upi_circle_pde import pde_engine, PaymentIntentRequest, store


@pytest.fixture(autouse=True)
def reset_demo_environment():
    """Reset mock bank, delegation provider, and PDE store before each test case."""
    mock_bank.reset_account("USER_TEST_SUITE", balance_paise=2500000) # ₹25,000
    mock_upi_circle_provider.reset_provider()
    store.locks.clear()
    store.velocity_logs.clear()
    store.txn_history.clear()
    # Create test delegation
    asyncio.run(mock_upi_circle_provider.create_delegation(
        primary_user_id="USER_TEST_SUITE",
        monthly_limit_paise=1500000, # ₹15,000
        transaction_limit_paise=500000 # ₹5,000
    ))


@pytest.mark.asyncio
async def test_01_grocery_350_approved_and_success():
    """TEST 1: ₹350 grocery -> APPROVED + SUCCESS"""
    req = PaymentIntentRequest(
        user_id="USER_TEST_SUITE",
        session_id=str(uuid.uuid4()),
        mandate_id="DEL_001",
        item_id="PROD_GROCERY_01",
        item_title="Fresh Veggies",
        claimed_price_paise=35000, # ₹350
        merchant_vpa="grocery@demo",
        merchant="Demo Grocery Store",
        category="GROCERY"
    )

    ctx = await pde_engine.evaluate_intent(req)
    assert ctx.decision.value in ["APPROVED", "COMPLETED"]
    assert ctx.checks["transaction_limit"] is True
    assert ctx.checks["monthly_limit"] is True

    # Execute payment
    res = await pde_engine.execute_approved_payment(ctx, transaction_id="TXN_TEST_01")
    assert res["status"] == "SUCCESS"
    assert res["amount"] == 350.0

    # Verify balance & monthly spend updated
    assert mock_bank.get_balance_paise("USER_TEST_SUITE") == 2465000 # ₹24,650
    del_info = await mock_upi_circle_provider.get_delegation("USER_TEST_SUITE")
    assert del_info["spent_this_month"] == 350.0


@pytest.mark.asyncio
async def test_02_transaction_limit_exact_5000_approved():
    """TEST 2: ₹5,000 transaction -> APPROVED"""
    req = PaymentIntentRequest(
        user_id="USER_TEST_SUITE",
        session_id=str(uuid.uuid4()),
        mandate_id="DEL_001",
        item_id="PROD_TEST_5K",
        item_title="Store Purchase",
        claimed_price_paise=500000, # ₹5,000
        merchant_vpa="food@demo",
        merchant="Demo Food Store",
        category="FOOD"
    )

    ctx = await pde_engine.evaluate_intent(req)
    assert ctx.decision.value in ["APPROVED", "COMPLETED"]
    assert ctx.checks["transaction_limit"] is True


@pytest.mark.asyncio
async def test_03_transaction_limit_exceeded_5001_denied():
    """TEST 3: ₹5,001 transaction -> DENIED"""
    req = PaymentIntentRequest(
        user_id="USER_TEST_SUITE",
        session_id=str(uuid.uuid4()),
        mandate_id="DEL_001",
        item_id="PROD_TEST_5K1",
        item_title="Overlimit Purchase",
        claimed_price_paise=500100, # ₹5,001
        merchant_vpa="demostore@demo",
        merchant="Demo Store",
        category="SHOPPING"
    )

    ctx = await pde_engine.evaluate_intent(req)
    assert ctx.decision.value == "DENIED"
    assert ctx.reason_code == "TRANSACTION_LIMIT_EXCEEDED"
    assert "exceeds delegated transaction limit" in ctx.rejection_reason


@pytest.mark.asyncio
async def test_04_monthly_limit_exceeded_denied():
    """TEST 4: Monthly spent ₹14,800 + ₹500 -> DENIED"""
    delegation = await mock_upi_circle_provider.get_delegation("USER_TEST_SUITE")
    delegation["spent_this_month_paise"] = 1480000 # ₹14,800 spent

    req = PaymentIntentRequest(
        user_id="USER_TEST_SUITE",
        session_id=str(uuid.uuid4()),
        mandate_id="DEL_001",
        item_id="PROD_TEST_500",
        item_title="Shirt",
        claimed_price_paise=50000, # ₹500
        merchant_vpa="demostore@demo",
        merchant="Demo Store",
        category="SHOPPING"
    )

    ctx = await pde_engine.evaluate_intent(req)
    assert ctx.decision.value == "DENIED"
    assert ctx.reason_code == "MONTHLY_LIMIT_EXCEEDED"
    assert "exceeds remaining monthly limit" in ctx.rejection_reason


@pytest.mark.asyncio
async def test_05_blocked_category_denied():
    """TEST 5: Blocked category (CRYPTO) -> DENIED"""
    req = PaymentIntentRequest(
        user_id="USER_TEST_SUITE",
        session_id=str(uuid.uuid4()),
        mandate_id="DEL_001",
        item_id="PROD_CRYPTO",
        item_title="Crypto Tokens",
        claimed_price_paise=100000, # ₹1,000
        merchant_vpa="crypto@demo",
        merchant="Demo Crypto",
        category="CRYPTO"
    )

    ctx = await pde_engine.evaluate_intent(req)
    assert ctx.decision.value == "DENIED"
    assert ctx.reason_code == "CATEGORY_BLOCKED"
    assert "blocked under security policy" in ctx.rejection_reason


@pytest.mark.asyncio
async def test_06_inactive_delegation_denied():
    """TEST 6: Inactive delegation -> DENIED"""
    await mock_upi_circle_provider.revoke_delegation("USER_TEST_SUITE")

    req = PaymentIntentRequest(
        user_id="USER_TEST_SUITE",
        session_id=str(uuid.uuid4()),
        mandate_id="DEL_001",
        item_id="PROD_TEA",
        item_title="Tea",
        claimed_price_paise=3500, # ₹35
        merchant_vpa="food@demo",
        merchant="Demo Food Store",
        category="FOOD"
    )

    ctx = await pde_engine.evaluate_intent(req)
    assert ctx.decision.value == "DENIED"
    assert ctx.reason_code in ["DELEGATION_DISCONNECTED", "DELEGATION_INACTIVE"]


@pytest.mark.asyncio
async def test_07_expired_delegation_denied():
    """TEST 7: Expired delegation -> DENIED"""
    delegation = await mock_upi_circle_provider.get_delegation("USER_TEST_SUITE")
    delegation["expires_at"] = (datetime.now(timezone.utc) - timedelta(days=1)).isoformat()

    req = PaymentIntentRequest(
        user_id="USER_TEST_SUITE",
        session_id=str(uuid.uuid4()),
        mandate_id="DEL_001",
        item_id="PROD_TEA",
        item_title="Tea",
        claimed_price_paise=3500,
        merchant_vpa="food@demo",
        merchant="Demo Food Store",
        category="FOOD"
    )

    ctx = await pde_engine.evaluate_intent(req)
    assert ctx.decision.value == "DENIED"
    assert ctx.reason_code == "DELEGATION_EXPIRED"


@pytest.mark.asyncio
async def test_08_insufficient_mock_bank_balance_failed():
    """TEST 8: Insufficient mock bank balance -> FAILED / DENIED"""
    mock_bank.reset_account("USER_TEST_SUITE", balance_paise=10000) # Only ₹100 in bank

    req = PaymentIntentRequest(
        user_id="USER_TEST_SUITE",
        session_id=str(uuid.uuid4()),
        mandate_id="DEL_001",
        item_id="PROD_SHOES",
        item_title="Shoes",
        claimed_price_paise=49900, # ₹499
        merchant_vpa="demostore@demo",
        merchant="Demo Store",
        category="SHOPPING"
    )

    ctx = await pde_engine.evaluate_intent(req)
    assert ctx.decision.value in ["FAILED", "DENIED"]
    assert ctx.reason_code == "INSUFFICIENT_FUNDS"


@pytest.mark.asyncio
async def test_09_high_risk_requires_user_approval():
    """TEST 9: High-risk transaction -> REQUIRES_USER_APPROVAL"""
    req = PaymentIntentRequest(
        user_id="USER_TEST_SUITE",
        session_id=str(uuid.uuid4()),
        mandate_id="DEL_001",
        item_id="PROD_LAPTOP_01",
        item_title="Demo Electronics",
        claimed_price_paise=450000, # ₹4,500
        merchant_vpa="electronics@demo",
        merchant="Demo Electronics",
        category="SHOPPING"
    )

    ctx = await pde_engine.evaluate_intent(req)
    assert ctx.decision.value in ["REQUIRES_USER_APPROVAL", "ESCALATED_TO_PIN"]
    assert ctx.risk_score >= 0.40


@pytest.mark.asyncio
async def test_10_user_rejects_approval_cancelled():
    """TEST 10: User rejects approval -> CANCELLED"""
    from backend.app.api.v1.simulated_upi_api import initiate_payment, InitiatePaymentSchema
    res = await initiate_payment(InitiatePaymentSchema(transaction_id="TXN_USER_REJECT", action="REJECT"))
    assert res["status"] == "CANCELLED"


@pytest.mark.asyncio
async def test_11_user_approves_approval_success():
    """TEST 11: User approves approval -> SUCCESS"""
    req = PaymentIntentRequest(
        user_id="USER_TEST_SUITE",
        session_id=str(uuid.uuid4()),
        mandate_id="DEL_001",
        item_id="PROD_LAPTOP_01",
        item_title="Demo Electronics",
        claimed_price_paise=450000, # ₹4,500
        merchant_vpa="electronics@demo",
        merchant="Demo Electronics",
        category="SHOPPING"
    )

    ctx = await pde_engine.evaluate_intent(req)

    res = await pde_engine.execute_approved_payment(ctx, transaction_id="TXN_APPROVED_EXEC")
    assert res["status"] == "SUCCESS"
    assert res["amount"] == 4500.0


@pytest.mark.asyncio
async def test_12_transaction_splitting_protection_denied():
    """TEST 12: Attempt to split ₹8,000 purchase into two ₹4,000 payments -> DENIED"""
    req1 = PaymentIntentRequest(
        user_id="USER_TEST_SUITE",
        session_id=str(uuid.uuid4()),
        mandate_id="DEL_001",
        item_id="PROD_PHONE_PART1",
        item_title="Smartphone Part 1",
        claimed_price_paise=400000, # ₹4,000
        merchant_vpa="electronics@demo",
        merchant="Demo Electronics",
        category="SHOPPING"
    )

    # First ₹4,000 intent
    ctx1 = await pde_engine.evaluate_intent(req1)
    await store.record_transaction_intent("USER_TEST_SUITE", req1)

    # Second ₹4,000 intent within 10 minutes (Total ₹8,000 for same merchant/category)
    req2 = PaymentIntentRequest(
        user_id="USER_TEST_SUITE",
        session_id=str(uuid.uuid4()),
        mandate_id="DEL_001",
        item_id="PROD_PHONE_PART2",
        item_title="Smartphone Part 2",
        claimed_price_paise=400000, # ₹4,000
        merchant_vpa="electronics@demo",
        merchant="Demo Electronics",
        category="SHOPPING"
    )

    ctx2 = await pde_engine.evaluate_intent(req2)
    assert ctx2.decision.value == "DENIED"
    assert ctx2.reason_code == "POSSIBLE_TRANSACTION_SPLITTING"
    assert "Possible transaction splitting detected" in ctx2.rejection_reason
