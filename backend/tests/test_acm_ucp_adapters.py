import pytest
import uuid
import datetime
from backend.app.schemas.intent_schemas import UCPActionCandidate, ExtractedIntent
from backend.app.router.provider_router import provider_router
from backend.app.payment.razorpay_vault import razorpay_vault
from backend.app.audit.hash_chain import hash_chain, GENESIS_HASH

@pytest.mark.asyncio
async def test_provider_router_discovery_and_ucp_schema():
    # 1. Commerce Discovery
    comm_intent = ExtractedIntent(
        intent="product_search",
        category="electronics",
        product="20W fast charger",
        max_price_paise=50000
    )
    comm_candidates = await provider_router.route_and_discover(comm_intent)
    assert len(comm_candidates) > 0
    c1 = comm_candidates[0]
    assert isinstance(c1, UCPActionCandidate)
    assert c1.action_type == "PURCHASE_PRODUCT"
    assert c1.acm_stage == "DISCOVER"
    assert c1.verified is True
    assert c1.price_paise <= 50000

    # 2. Telecom Recharge Discovery
    recharge_intent = ExtractedIntent(
        intent="mobile_recharge",
        category="recharge",
        product="2GB 5G plan",
        max_price_paise=30000
    )
    recharge_candidates = await provider_router.route_and_discover(recharge_intent)
    assert len(recharge_candidates) > 0
    r1 = recharge_candidates[0]
    assert r1.action_type == "MOBILE_RECHARGE"
    assert r1.price_paise <= 30000

    # 4. Bill Pay Discovery
    bill_intent = ExtractedIntent(
        intent="bill_payment",
        category="utility",
        product="Electricity Bill",
        max_price_paise=200000
    )
    bill_candidates = await provider_router.route_and_discover(bill_intent)
    assert len(bill_candidates) > 0
    b1 = bill_candidates[0]
    assert b1.action_type == "PAY_BILL"

@pytest.mark.asyncio
async def test_acm_lifecycle_stages_quote_lock_and_pay():
    comm_intent = ExtractedIntent(
        intent="product_search",
        category="electronics",
        product="Ambrane charger",
        max_price_paise=50000
    )
    candidates = await provider_router.route_and_discover(comm_intent)
    c = candidates[0]
    assert c.acm_stage == "DISCOVER"

    # Stage 2: QUOTE LOCK
    locked_cand = await provider_router.lock_quote(c)
    assert locked_cand.acm_stage == "QUOTE_LOCKED"

    # Stage 3: EXECUTE PAY via Mandate Token Vault
    mandate_token = "mandate_token_demo_9921"
    token_hash = razorpay_vault.hash_token(mandate_token)
    assert razorpay_vault.verify_token(mandate_token, token_hash) is True

    pay_res = await provider_router.execute_pay(locked_cand, token_hash)
    assert pay_res["success"] is True
    assert pay_res["status"] == "AUTHORIZED_PAID"

@pytest.mark.asyncio
async def test_razorpay_vault_and_audit_hash_chain():
    # 1. Razorpay Mandate Vault
    token = "test_mandate_token_778"
    t_hash = razorpay_vault.hash_token(token)
    assert len(t_hash) == 64 # SHA-256 length
    assert razorpay_vault.verify_token(token, t_hash) is True
    assert razorpay_vault.verify_token("invalid_token", t_hash) is False

    # 2. Cryptographic Hash Chain Audit Trail
    payload_1 = {"action": "QUOTE_LOCKED", "amount_paise": 44900}
    hash_1 = hash_chain.compute_hash(GENESIS_HASH, payload_1)

    payload_2 = {"action": "AUTHORIZED_PAID", "amount_paise": 44900, "token_hash": t_hash}
    hash_2 = hash_chain.compute_hash(hash_1, payload_2)

    # Verify integrity of block 2 against block 1
    assert hash_chain.verify_link(hash_1, payload_2, hash_2) is True
    # Verify tampered payload fails
    tampered_payload_2 = {"action": "AUTHORIZED_PAID", "amount_paise": 99900, "token_hash": t_hash}
    assert hash_chain.verify_link(hash_1, tampered_payload_2, hash_2) is False
