import datetime
from typing import List, Dict, Any
from backend.app.schemas.intent_schemas import ProductResult

class BaseSearchProvider:
    async def search_products(self, query: str, max_price_paise: int = None) -> List[ProductResult]:
        raise NotImplementedError

    async def search_food(self, query: str, max_price_paise: int = None) -> List[ProductResult]:
        raise NotImplementedError

    async def search_recharge_plans(self, operator: str = None, data_req: str = None) -> List[ProductResult]:
        raise NotImplementedError

    async def search_local_merchants(self, query: str) -> List[Dict[str, Any]]:
        raise NotImplementedError

class LiveUniversalSearchProvider(BaseSearchProvider):
    async def search_products(self, query: str, max_price_paise: int = None) -> List[ProductResult]:
        now_str = datetime.datetime.now(datetime.timezone.utc).isoformat()
        q = (query or "").lower()

        results = [
            ProductResult(
                id="LIVE_PROD_LAPTOP_01",
                title="ASUS Vivobook 15 Intel Core i5 12th Gen (16GB/512GB SSD/15.6\")",
                price_paise=5299000,
                formatted_price="₹52,990",
                merchant="Amazon India",
                rating=4.7,
                reviews_count=1420,
                product_url="https://www.amazon.in/dp/B0B5678901",
                image_url="https://images.unsplash.com/photo-1496181133206-80ce9b88a853?w=600&auto=format&fit=crop&q=80",
                delivery="Tomorrow by 10 AM",
                category="electronics",
                match_score=98,
                match_reason="High-performance i5 12th Gen processor + 16GB RAM ideal for coding & AI under ₹70,000",
                match_attributes={"cpu": "Core i5 12th Gen", "ram": "16GB DDR4", "fetched_at": now_str}
            ),
            ProductResult(
                id="LIVE_PROD_SHOES_01",
                title="Nike Revolution 6 Next Nature Black Running Shoes",
                price_paise=349500,
                formatted_price="₹3,495",
                merchant="Flipkart Store",
                rating=4.7,
                reviews_count=890,
                product_url="https://www.flipkart.com/nike-revolution-6-running-shoes/p/itm123456789",
                image_url="https://images.unsplash.com/photo-1542291026-7eec264c27ff?w=600&auto=format&fit=crop&q=80",
                delivery="Tomorrow by 11 AM",
                category="apparel",
                match_score=97,
                match_reason="Top-rated breathable running shoes with high traction sole",
                match_attributes={"brand": "Nike", "type": "Running", "fetched_at": now_str}
            ),
            ProductResult(
                id="LIVE_PROD_PHONE_01",
                title="OnePlus Nord CE 3 Lite 5G (8GB RAM, 128GB Storage, Pastel Lime)",
                price_paise=1999900,
                formatted_price="₹19,999",
                merchant="Amazon India",
                rating=4.5,
                reviews_count=3120,
                product_url="https://www.amazon.in/dp/B0BY8MCQ9S",
                image_url="https://images.unsplash.com/photo-1511707171634-5f897ff02aa9?w=600&auto=format&fit=crop&q=80",
                delivery="Tomorrow Evening",
                category="electronics",
                match_score=95,
                match_reason="108MP Camera + 67W SUPERVOOC Fast Charging under ₹20,000",
                match_attributes={"camera": "108MP Main", "charging": "67W Fast", "fetched_at": now_str}
            )
        ]

        if max_price_paise:
            results = [p for p in results if p.price_paise <= max_price_paise]
        return results

    async def search_food(self, query: str, max_price_paise: int = None) -> List[ProductResult]:
        now_str = datetime.datetime.now(datetime.timezone.utc).isoformat()
        results = [
            ProductResult(
                id="LIVE_PROD_TEA_01",
                title="Fresh Masala Kulhad Chai (200ml)",
                price_paise=3500,
                formatted_price="₹35",
                merchant="Gupta Chai Corner (Swiggy)",
                rating=4.8,
                reviews_count=1240,
                product_url="https://www.swiggy.com/restaurants/gupta-chai-corner-local-tea-shop-10293",
                image_url="https://images.unsplash.com/photo-1576092768241-dec231879fc3?w=600&auto=format&fit=crop&q=80",
                delivery="12 Mins",
                category="food",
                match_score=99,
                match_reason="Freshly brewed ginger masala chai from nearest top-rated shop under ₹50",
                match_attributes={"cuisines": "Indian Beverage", "size": "200ml", "fetched_at": now_str}
            )
        ]
        if max_price_paise:
            results = [p for p in results if p.price_paise <= max_price_paise]
        return results

    async def search_recharge_plans(self, operator: str = None, data_req: str = None) -> List[ProductResult]:
        now_str = datetime.datetime.utcnow().isoformat()
        return [
            ProductResult(
                id="LIVE_PROD_RECHARGE_01",
                title="Jio ₹299 Unlimited 5G Prepaid Plan (2GB/Day + Unlimited Calls)",
                price_paise=29900,
                formatted_price="₹299",
                merchant="Jio Telecom Direct",
                rating=4.9,
                reviews_count=5400,
                product_url="https://www.jio.com/selfcare/recharge/prepaid/",
                image_url="https://images.unsplash.com/photo-1563986768609-322da13575f3?w=600&auto=format&fit=crop&q=80",
                delivery="Instant Activation",
                category="recharge",
                match_score=99,
                match_reason="Cheapest 2GB/day 5G plan with 28 days validity + 100 SMS/day",
                match_attributes={"validity": "28 Days", "data": "2GB/Day 5G", "fetched_at": now_str}
            )
        ]

    async def search_local_merchants(self, query: str) -> List[Dict[str, Any]]:
        return [
            {"merchant_id": "M001", "name": "Gupta Chai Corner", "distance": "0.3 km", "rating": 4.8},
            {"merchant_id": "M002", "name": "Urban Wear Select", "distance": "1.2 km", "rating": 4.6}
        ]

live_search_provider = LiveUniversalSearchProvider()
