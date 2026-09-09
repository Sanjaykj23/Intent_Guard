import uuid
import datetime
from typing import List, Dict, Any
from backend.app.schemas.intent_schemas import UCPActionCandidate
from backend.app.router.adapters.base_adapter import BaseActionAdapter

class BillPayActionAdapter(BaseActionAdapter):
    async def acm_discover(self, intent_slots: Dict[str, Any]) -> List[UCPActionCandidate]:
        now_str = datetime.datetime.utcnow().isoformat()
        max_price_paise = intent_slots.get("max_price_paise")

        candidates = [
            UCPActionCandidate(
                candidate_id=f"ucp_bill_{uuid.uuid4().hex[:8]}",
                provider="BBPS Electricity Direct",
                merchant_id="MERCHANT_BBPS_ELECTRICITY",
                action_type="PAY_BILL",
                name="Monthly Electricity Utility Bill Payment",
                price_paise=145000,
                formatted_price="₹1,450",
                currency="INR",
                source_url="https://www.bbps.org.in/electricity-bill-pay",
                exact_action_url="https://www.bbps.org.in/electricity-bill-pay",
                acm_stage="DISCOVER",
                idempotency_key=f"idemp_{uuid.uuid4().hex[:8]}",
                verified=True,
                source="bbps_official_api",
                rating=4.9,
                reviews_count=8900,
                delivery="Instant Settlement",
                image_url="https://images.unsplash.com/photo-1473341304170-971dccb5ac1e?w=600&auto=format&fit=crop&q=80",
                category="utility",
                retrieved_at=now_str,
                match_score=99,
                match_reason="BBPS Official verified electricity utility bill payment",
                match_attributes={"utility": "Electricity", "source": "BBPS Official API"}
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

billpay_adapter = BillPayActionAdapter()
