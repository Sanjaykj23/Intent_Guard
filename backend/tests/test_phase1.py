import pytest
import asyncio
from backend.app.ai.llama_service import llama_service
from backend.app.schemas.intent_schemas import ExtractedIntent, UserPolicySchema
from backend.app.search.search_router import search_router
from backend.app.guard.policy_engine import policy_engine
from backend.app.payment.razorpay_vault import razorpay_vault
from backend.app.audit.hash_chain import hash_chain, GENESIS_HASH

@pytest.mark.asyncio
async def test_llama_intent_extraction():
    prompt = "Recharge my jio number 9876543210 under ₹50"
    intent = await llama_service.extract_intent(prompt)
    assert intent.intent == "mobile_recharge"
    assert intent.category == "recharge"
    assert intent.max_price_paise == 5000

@pytest.mark.asyncio
async def test_live_search_and_direct_url():
    intent = ExtractedIntent(
        intent="product_search",
        category="electronics",
        product="laptop for coding",
        max_price_paise=7000000,
        currency="INR"
    )
    products = await search_router.route_and_search(intent)
    assert len(products) > 0
    top = products[0]
    assert top.product_url.startswith("https://")
    assert top.price_paise <= 7000000

def test_intentguard_policy_engine():
    policy = UserPolicySchema(
        user_id="USER_TEST",
        daily_limit_paise=500000,
        transaction_limit_paise=100000,
        auto_approval_threshold_paise=20000,
        allowed_categories=["apparel", "electronics", "food", "recharge"]
    )

    # Test Tea under threshold -> AUTO ALLOWED
    res_tea = policy_engine.evaluate_transaction(policy, 3500, "food")
    assert res_tea.allowed is True
    assert res_tea.auto_approved is True

    # Test Laptop over limit -> BLOCKED
    res_laptop = policy_engine.evaluate_transaction(policy, 5299000, "electronics")
    assert res_laptop.allowed is False
    assert res_laptop.status_code == "BLOCKED_TRANSACTION_LIMIT_EXCEEDED"

def test_razorpay_mandate_token_hashing():
    raw_token = "rzp_mandate_token_test_123"
    token_hash = razorpay_vault.hash_mandate_token(raw_token)
    assert len(token_hash) == 64 # SHA-256 length

def test_append_only_hash_chain():
    payload1 = {"intent": "ORDER_TEA", "amount_paise": 3500}
    hash1 = hash_chain.compute_hash(GENESIS_HASH, payload1)
    
    payload2 = {"transaction_id": "TXN_1001", "status": "EXECUTED"}
    hash2 = hash_chain.compute_hash(hash1, payload2)
    
    assert hash1 != GENESIS_HASH
    assert hash2 != hash1
