import uuid
from typing import Dict, Any, Tuple
from backend.app.schemas.intent_schemas import ExtractedIntent, CanonicalIntent
from backend.app.search.deterministic_parser import deterministic_parser

class SlotResolver:
    """
    PHASE 4 — HYBRID SLOT RESOLUTION & CONFLICT DETECTOR (ZERO TRUST LLM)
    Combines Deterministic REGEX Extractions and LLM Extractions.
    Enforces Trust Priority Rule:
    1️⃣ User Input / Deterministic REGEX (Source of Truth for Money & Critical Constraints)
    2️⃣ Schema & Pydantic Rules
    3️⃣ LLM Inference (Untrusted — ONLY used for action/intent categorization & keywords)
    """

    @classmethod
    def resolve_canonical_intent(cls, user_message: str, llm_intent: ExtractedIntent) -> CanonicalIntent:
        regex_slots = deterministic_parser.parse_user_input(user_message)
        slot_sources: Dict[str, str] = {}

        # 1. Action & Category Resolution
        intent_type = (llm_intent.intent or "product_search").lower()
        if intent_type in ["food_order", "tea_order"]:
            action = "ORDER_FOOD"
            category = "food"
        elif intent_type == "mobile_recharge":
            action = "MOBILE_RECHARGE"
            category = "recharge"
        elif intent_type == "bill_payment":
            action = "PAY_BILL"
            category = "utility"
        elif intent_type == "greeting":
            action = "GREETING"
            category = "general"
        elif intent_type == "policy_question":
            action = "POLICY_QUESTION"
            category = "general"
        else:
            action = "SEARCH_PRODUCT"
            category = llm_intent.category or "apparel"

        slot_sources["action"] = "LLM_INFERENCE"
        slot_sources["category"] = "LLM_INFERENCE"

        # 2. Critical Price Slot Resolution (Money is a critical field — REGEX OVERRIDES LLM)
        regex_price = regex_slots.get("max_price_paise")
        llm_price = llm_intent.max_price_paise

        if regex_price is not None:
            max_price_paise = regex_price
            slot_sources["max_price_paise"] = "DETERMINISTIC_REGEX"
            if llm_price is not None and llm_price != regex_price:
                slot_sources["price_conflict_note"] = f"LLM proposed {llm_price} paise rejected in favor of Deterministic REGEX {regex_price} paise"
        else:
            max_price_paise = llm_price
            slot_sources["max_price_paise"] = "LLM_INFERENCE" if llm_price is not None else "UNCONSTRAINED"

        # 3. Delivery Days Constraint Resolution (REGEX OVERRIDES LLM)
        regex_delivery = regex_slots.get("delivery_days_max")
        llm_delivery = llm_intent.delivery_days_max

        if regex_delivery is not None:
            delivery_days_max = regex_delivery
            slot_sources["delivery_days_max"] = "DETERMINISTIC_REGEX"
        else:
            delivery_days_max = llm_delivery
            slot_sources["delivery_days_max"] = "LLM_INFERENCE" if llm_delivery is not None else "UNCONSTRAINED"

        # 4. Color & Brand Resolution
        color = regex_slots.get("color") or llm_intent.color
        slot_sources["color"] = "DETERMINISTIC_REGEX" if regex_slots.get("color") else "LLM_INFERENCE"

        brand = regex_slots.get("brand") or llm_intent.brand
        slot_sources["brand"] = "DETERMINISTIC_REGEX" if regex_slots.get("brand") else "LLM_INFERENCE"

        # 5. Quantity Resolution
        quantity = regex_slots.get("quantity") or llm_intent.quantity or 1
        slot_sources["quantity"] = "DETERMINISTIC_REGEX"

        # 6. Product Query Keywords
        product_query = llm_intent.product or user_message

        canonical = CanonicalIntent(
            intent_id=f"intent_{uuid.uuid4().hex[:8]}",
            action=action,
            category=category,
            product_query=product_query,
            max_price_paise=max_price_paise,
            currency="INR",
            delivery_days_max=delivery_days_max,
            color=color,
            brand=brand,
            quantity=quantity,
            status="VALIDATED",
            slot_sources=slot_sources
        )

        return canonical

slot_resolver = SlotResolver()
