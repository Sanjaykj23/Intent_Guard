import pytest
from backend.app.schemas.intent_schemas import ExtractedIntent, CanonicalIntent, UCPActionCandidate
from backend.app.search.deterministic_parser import deterministic_parser
from backend.app.search.slot_resolver import slot_resolver
from backend.app.guard.verification_engine import verification_engine

def test_deterministic_parser_extraction():
    prompt = "Order a black shirt under ₹500 and deliver it within 4 days."
    parsed = deterministic_parser.parse_user_input(prompt)
    
    assert parsed["max_price_paise"] == 50000  # ₹500 in paise
    assert parsed["delivery_days_max"] == 4     # 4 days
    assert parsed["color"] == "Black"           # Color Black
    assert parsed["quantity"] == 1

def test_slot_resolver_and_conflict_detection():
    prompt = "Order a black shirt under ₹500 and deliver it within 4 days."
    
    # Simulate an untrusted/hallucinated LLM output with inflated price limit ₹5,000 (500000 paise)
    untrusted_llm = ExtractedIntent(
        intent="product_search",
        category="apparel",
        product="black shirt",
        max_price_paise=500000, # Untrusted LLM hallucinated 5,000 INR
        delivery_days_max=10
    )

    canonical = slot_resolver.resolve_canonical_intent(prompt, untrusted_llm)

    # 1. Deterministic REGEX MUST OVERRIDE untrusted LLM value for critical money slot!
    assert canonical.max_price_paise == 50000 # Enforced ₹500 (50000 paise)
    assert canonical.slot_sources["max_price_paise"] == "DETERMINISTIC_REGEX"
    assert "rejected" in canonical.slot_sources["price_conflict_note"].lower()

    # 2. Deterministic REGEX MUST OVERRIDE untrusted LLM value for delivery days!
    assert canonical.delivery_days_max == 4
    assert canonical.slot_sources["delivery_days_max"] == "DETERMINISTIC_REGEX"

    # 3. Canonical Intent Status must be VALIDATED
    assert canonical.status == "VALIDATED"

def test_verification_engine_constraint_filtering():
    prompt = "Order a black shirt under ₹500 and deliver it within 4 days."
    untrusted_llm = ExtractedIntent(intent="product_search", category="apparel", product="black shirt")
    canonical = slot_resolver.resolve_canonical_intent(prompt, untrusted_llm)

    # Schema Validation Check
    val_res = verification_engine.validate_canonical_intent(canonical)
    assert val_res["valid"] is True

    # Candidate filtering check
    candidates = [
        UCPActionCandidate(
            candidate_id="c1",
            provider="Myntra Direct",
            merchant_id="M1",
            action_type="PURCHASE_PRODUCT",
            name="Roadster Black Oversized Cotton T-Shirt",
            price_paise=49900, # ₹499 (Valid <= ₹500)
            formatted_price="₹499",
            delivery="Tomorrow", # 1 Day (Valid <= 4 Days)
            source_url="https://www.myntra.com/tshirts/roadster/roadster-men-black-pure-cotton-oversized-t-shirt/1700944/buy",
            exact_action_url="https://www.myntra.com/tshirts/roadster/roadster-men-black-pure-cotton-oversized-t-shirt/1700944/buy"
        ),
        UCPActionCandidate(
            candidate_id="c2",
            provider="Flipkart Store",
            merchant_id="M2",
            action_type="PURCHASE_PRODUCT",
            name="Premium Black Shirt",
            price_paise=79900, # ₹799 (INVALID > ₹500 Budget)
            formatted_price="₹799",
            delivery="Tomorrow",
            source_url="https://www.flipkart.com/p/itm123456789",
            exact_action_url="https://www.flipkart.com/p/itm123456789"
        ),
        UCPActionCandidate(
            candidate_id="c3",
            provider="Amazon India",
            merchant_id="M3",
            action_type="PURCHASE_PRODUCT",
            name="Casual Black Shirt",
            price_paise=45000, # ₹450 (Valid <= ₹500)
            formatted_price="₹450",
            delivery="10 Days", # INVALID > 4 Days Delivery
            source_url="https://www.amazon.in/dp/B08X123456",
            exact_action_url="https://www.amazon.in/dp/B08X123456"
        )
    ]

    filtered = verification_engine.verify_and_filter_candidates(candidates, canonical)

    # c2 (over budget ₹799) and c3 (over delivery 10 days) MUST be rejected by hard constraint engine!
    assert len(filtered) == 1
    assert filtered[0].candidate_id == "c1"
    assert filtered[0].price_paise <= 50000
