import uuid
import datetime
from typing import List, Dict, Any, Optional
from backend.app.schemas.intent_schemas import UCPActionCandidate, ExtractedIntent
from backend.app.router.adapters.commerce_adapter import commerce_adapter
from backend.app.router.adapters.food_adapter import food_adapter
from backend.app.router.adapters.telecom_adapter import telecom_adapter
from backend.app.router.adapters.billpay_adapter import billpay_adapter
from backend.app.normalizer.url_classifier import url_classifier

class ProviderRouter:
    def __init__(self):
        self.commerce = commerce_adapter
        self.food = food_adapter
        self.telecom = telecom_adapter
        self.billpay = billpay_adapter

    def get_adapter(self, action_type: str, category: Optional[str] = None):
        act = (action_type or "").upper()
        cat = (category or "").lower()

        if act == "MOBILE_RECHARGE" or cat in ["recharge", "telecom"]:
            return self.telecom
        elif act == "PAY_BILL" or cat == "utility":
            return self.billpay
        else:
            return self.commerce

    async def route_and_discover(self, intent: ExtractedIntent) -> List[UCPActionCandidate]:
        intent_type = (intent.intent or "").lower()
        cat = (intent.category or "").lower()
        
        if intent_type == "mobile_recharge" or cat in ["recharge", "telecom"]:
            action_type = "MOBILE_RECHARGE"
        elif intent_type == "bill_payment" or cat == "utility":
            action_type = "PAY_BILL"
        else:
            action_type = "PURCHASE_PRODUCT"

        intent_slots = {
            "product": intent.product,
            "max_price_paise": intent.max_price_paise,
            "category": cat,
            "delivery_location": intent.delivery_location,
            "priorities": intent.priorities
        }

        adapter = self.get_adapter(action_type, cat)
        candidates = await adapter.acm_discover(intent_slots)

        # Apply source verification gating via URLClassifier
        for candidate in candidates:
            if candidate.action_type == "MOBILE_RECHARGE":
                # Telecom links are live scraped and do not follow e-commerce patterns
                candidate.verified = True
                continue
            
            target_url = candidate.exact_action_url or candidate.source_url or ""
            classification = url_classifier.classify(target_url)
            candidate.verified = classification["verified"]
            if not candidate.exact_action_url:
                candidate.exact_action_url = classification["exact_action_url"]

        return candidates

    async def lock_quote(self, candidate: UCPActionCandidate) -> UCPActionCandidate:
        cat = (candidate.category or "").lower()
        adapter = self.get_adapter(candidate.action_type, cat)
        return await adapter.acm_quote_lock(candidate)

    async def execute_pay(self, candidate: UCPActionCandidate, token_hash: str) -> Dict[str, Any]:
        cat = (candidate.category or "").lower()
        adapter = self.get_adapter(candidate.action_type, cat)
        return await adapter.acm_execute_pay(candidate, token_hash)

provider_router = ProviderRouter()
