from typing import List, Dict, Any

class QueryBuilder:
    """
    Deterministic Query Builder.
    Constructs precise search queries from extracted intent slots.
    """
    @staticmethod
    def build_search_queries(intent_slots: Dict[str, Any]) -> List[str]:
        product = intent_slots.get("product") or intent_slots.get("product_type") or "item"
        budget = intent_slots.get("max_price_paise")
        budget_inr = budget // 100 if budget else None
        features = intent_slots.get("features", [])
        brand = intent_slots.get("brand")

        feature_str = " ".join(features) if features else ""
        brand_str = f"{brand} " if brand else ""
        budget_str = f"under {budget_inr} INR" if budget_inr else ""

        queries = [
            f"{brand_str}{product} {feature_str} {budget_str} site:amazon.in OR site:flipkart.com OR site:myntra.com".strip(),
            f"{product} price {budget_str} India".strip(),
            f"{brand_str}{product} online buy India".strip()
        ]
        return queries

query_builder = QueryBuilder()
