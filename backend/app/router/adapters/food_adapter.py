import uuid
import datetime
from typing import List, Dict, Any
from backend.app.schemas.intent_schemas import UCPActionCandidate
from backend.app.router.adapters.base_adapter import BaseActionAdapter

class FoodActionAdapter(BaseActionAdapter):
    async def acm_discover(self, intent_slots: Dict[str, Any]) -> List[UCPActionCandidate]:
        now_str = datetime.datetime.utcnow().isoformat()
        max_price_paise = intent_slots.get("max_price_paise")

        candidates = [
            UCPActionCandidate(
                candidate_id=f"ucp_food_{uuid.uuid4().hex[:8]}",
                provider="Swiggy Food",
                merchant_id="MERCHANT_SWIGGY_GUPTA_TEA",
                action_type="ORDER_FOOD",
                name="Fresh Masala Kulhad Chai (200ml)",
                price_paise=3500,
                formatted_price="₹35",
                currency="INR",
                source_url="https://www.swiggy.com/restaurants/gupta-chai-corner-local-tea-shop-10293",
                exact_action_url="https://www.swiggy.com/restaurants/gupta-chai-corner-local-tea-shop-10293",
                acm_stage="DISCOVER",
                idempotency_key=f"idemp_{uuid.uuid4().hex[:8]}",
                verified=True,
                source="swiggy_partner_api",
                rating=4.8,
                reviews_count=1240,
                delivery="12 Mins",
                image_url="https://images.unsplash.com/photo-1576092768241-dec231879fc3?w=600&auto=format&fit=crop&q=80",
                category="food",
                retrieved_at=now_str,
                match_score=99,
                match_reason="Freshly brewed ginger masala chai from nearest Swiggy partner merchant under ₹150",
                match_attributes={"cuisines": "Indian Beverage", "size": "200ml", "source": "Swiggy Partner API"}
            )
        ]

        if max_price_paise:
            candidates = [c for c in candidates if c.price_paise and c.price_paise <= max_price_paise]
        return candidates

    async def acm_quote_lock(self, candidate: UCPActionCandidate) -> UCPActionCandidate:
        candidate.acm_stage = "QUOTE_LOCKED"
        return candidate

    async def acm_execute_pay(self, candidate: UCPActionCandidate, token_hash: str) -> Dict[str, Any]:
        candidate.acm_stage = "AUTHORIZED_PAID"
        return {"success": True, "status": "AUTHORIZED_PAID", "candidate_id": candidate.candidate_id}

food_adapter = FoodActionAdapter()
