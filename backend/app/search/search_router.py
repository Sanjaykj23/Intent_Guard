from typing import List
from backend.app.schemas.intent_schemas import ProductResult, ExtractedIntent
from backend.app.search.providers.merchant_adapters import DemoEcommerceAdapter, DemoFoodAdapter, DemoRechargeAdapter
from backend.app.search.providers.live_web_search import live_web_search_agent
from backend.app.normalizer.product_normalizer import ProductNormalizer

class SearchRouter:
    def __init__(self):
        self.ecom_adapter = DemoEcommerceAdapter()
        self.food_adapter = DemoFoodAdapter()
        self.recharge_adapter = DemoRechargeAdapter()

    async def route_and_search(self, intent: ExtractedIntent) -> List[ProductResult]:
        cat = (intent.category or "apparel").lower()
        intent_type = (intent.intent or "").lower()
        query = intent.product or ""

        # 1. Execute Live Internet Web Search
        live_results = await live_web_search_agent.search_live_internet(query, cat, intent.max_price_paise)
        if live_results:
            return ProductNormalizer.normalize_and_rank(live_results, intent.priorities)

        # 2. Fallback to category adapters if live web search yields no items
        if intent_type in ["tea_order", "food_order"] or cat == "food":
            raw_results = await self.food_adapter.search(query, cat, intent.max_price_paise)
        elif intent_type == "mobile_recharge" or cat == "recharge":
            raw_results = await self.recharge_adapter.search(query, cat, intent.max_price_paise)
        else:
            raw_results = await self.ecom_adapter.search(query, cat, intent.max_price_paise)

        return ProductNormalizer.normalize_and_rank(raw_results, intent.priorities)

search_router = SearchRouter()
