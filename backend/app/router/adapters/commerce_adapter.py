import uuid
import datetime
from typing import List, Dict, Any
from backend.app.schemas.intent_schemas import UCPActionCandidate
from backend.app.router.adapters.base_adapter import BaseActionAdapter
from backend.app.search.providers.live_web_search import live_web_search_agent

class CommerceActionAdapter(BaseActionAdapter):
    async def acm_discover(self, intent_slots: Dict[str, Any]) -> List[UCPActionCandidate]:
        now_str = datetime.datetime.utcnow().isoformat()
        query = (intent_slots.get("product") or "").lower()
        max_price_paise = intent_slots.get("max_price_paise")
        category = intent_slots.get("category", "commerce")

        # 1. Fetch real products using Google Shopping Serper
        live_products = await live_web_search_agent.search_live_internet(query, category=category, max_price_paise=max_price_paise)
        
        candidates = []
        for p in live_products:
            candidates.append(
                UCPActionCandidate(
                    candidate_id=f"ucp_comm_{uuid.uuid4().hex[:8]}",
                    provider=p.merchant,
                    merchant_id=f"MERCHANT_{p.merchant.upper().replace(' ', '_')}",
                    action_type="PURCHASE_PRODUCT",
                    name=p.title,
                    price_paise=p.price_paise,
                    formatted_price=p.formatted_price,
                    currency="INR",
                    source_url=p.product_url,
                    exact_action_url=p.exact_action_url,
                    acm_stage="DISCOVER",
                    idempotency_key=f"idemp_{uuid.uuid4().hex[:8]}",
                    verified=p.verified,
                    source="live_google_shopping",
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
        return {
            "success": True,
            "status": "AUTHORIZED_PAID",
            "candidate_id": candidate.candidate_id,
            "provider": candidate.provider,
            "token_hash": token_hash
        }

commerce_adapter = CommerceActionAdapter()
