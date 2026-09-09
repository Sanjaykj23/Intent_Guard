import uuid
import datetime
import httpx
from typing import List, Dict, Any
from backend.app.schemas.intent_schemas import UCPActionCandidate
from backend.app.router.adapters.base_adapter import BaseActionAdapter
from backend.app.search.providers.live_web_search import live_web_search_agent

class OperatorLookupAPI:
    """Mock API simulating a telecom HLR/Operator Lookup service"""
    @staticmethod
    async def lookup(phone_number: str) -> str:
        # Simulate API latency
        # In a real app, this would hit an API like datayuge or a Telecom HLR lookup
        first_two = phone_number[:2]
        if first_two in ["98", "99", "97"]:
            return "Airtel"
        elif first_two in ["70", "79", "63", "88"]:
            return "Jio"
        elif first_two in ["94", "89", "80"]:
            return "BSNL"
        else:
            return "Vi"

operator_lookup_api = OperatorLookupAPI()

class TelecomActionAdapter(BaseActionAdapter):
    async def acm_discover(self, intent_slots: Dict[str, Any]) -> List[UCPActionCandidate]:
        now_str = datetime.datetime.utcnow().isoformat()
        max_price_paise = intent_slots.get("max_price_paise")
        query = intent_slots.get("product") or "mobile recharge plan"

        live_plans = await live_web_search_agent._search_via_open_web(query, category="recharge", max_price_paise=max_price_paise)
        
        candidates = []
        for p in live_plans:
            candidates.append(
                UCPActionCandidate(
                    candidate_id=f"ucp_tel_{uuid.uuid4().hex[:8]}",
                    provider=p.merchant,
                    merchant_id=f"MERCHANT_{p.merchant.upper().replace(' ', '_')}",
                    action_type="MOBILE_RECHARGE",
                    name=p.title,
                    price_paise=p.price_paise,
                    formatted_price=p.formatted_price,
                    currency="INR",
                    source_url=p.product_url,
                    exact_action_url=p.exact_action_url,
                    acm_stage="DISCOVER",
                    idempotency_key=f"idemp_{uuid.uuid4().hex[:8]}",
                    verified=p.verified,
                    source="live_telecom_search",
                    rating=p.rating,
                    reviews_count=p.reviews_count,
                    delivery=p.delivery,
                    image_url=p.image_url,
                    category=p.category,
                    retrieved_at=now_str,
                    match_score=p.match_score,
                    match_reason=p.match_reason,
                    match_attributes=p.match_attributes
                )
            )

        if max_price_paise:
            candidates = [c for c in candidates if c.price_paise and c.price_paise <= max_price_paise]
        return candidates

    async def acm_quote_lock(self, candidate: UCPActionCandidate) -> UCPActionCandidate:
        candidate.acm_stage = "QUOTE_LOCKED"
        return candidate

    async def acm_execute_pay(self, candidate: UCPActionCandidate, token_hash: str) -> Dict[str, Any]:
        candidate.acm_stage = "AUTHORIZED_PAID"
        return {"success": True, "status": "AUTHORIZED_PAID", "candidate_id": candidate.candidate_id}

telecom_adapter = TelecomActionAdapter()
