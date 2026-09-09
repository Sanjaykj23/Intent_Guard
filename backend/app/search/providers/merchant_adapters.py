from typing import List
from backend.app.schemas.intent_schemas import ProductResult

class MerchantAdapter:
    async def search(self, query: str, category: str, max_price_paise: int = None) -> List[ProductResult]:
        raise NotImplementedError

class DemoEcommerceAdapter(MerchantAdapter):
    async def search(self, query: str, category: str, max_price_paise: int = None) -> List[ProductResult]:
        q = (query or "").lower()
        
        # Apparel Dataset with Direct URLs
        apparel_items = [
            ProductResult(
                id="PROD_SHIRT_01",
                title="Urban Oversized Heavyweight Cotton Shirt - Jet Black",
                price_paise=129900,
                formatted_price="₹1,299",
                merchant="Amazon India",
                rating=4.6,
                reviews_count=342,
                product_url="https://www.amazon.in/dp/B08X123456",
                image_url="https://images.unsplash.com/photo-1521572267360-ee0c2909d518?w=600&auto=format&fit=crop&q=80",
                delivery="Tomorrow by 2 PM",
                category="apparel",
                match_score=96,
                match_reason="Best overall match for black oversized cotton shirt within budget",
                match_attributes={"color": "Jet Black", "style": "Oversized Fit", "budget": "₹1,299 (Under budget)"}
            ),
            ProductResult(
                id="PROD_SHOES_01",
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
                match_attributes={"brand": "Nike", "type": "Running", "budget": "₹3,495 (Under ₹5,000)"}
            ),
            ProductResult(
                id="PROD_SHIRT_02",
                title="Streetwear Dark Cotton Drop-Shoulder Tee",
                price_paise=99900,
                formatted_price="₹999",
                merchant="Myntra Direct",
                rating=4.4,
                reviews_count=189,
                product_url="https://www.myntra.com/tshirts/roadster/dark-cotton-tee/998811",
                image_url="https://images.unsplash.com/photo-1583743814966-8936f5b7be1a?w=600&auto=format&fit=crop&q=80",
                delivery="2 Days (Friday)",
                category="apparel",
                match_score=91,
                match_reason="Affordable streetwear tee crafted from bio-washed cotton",
                match_attributes={"color": "Charcoal Black", "budget": "₹999 (Well under limit)"}
            )
        ]

        # Electronics Dataset with Direct URLs
        electronics_items = [
            ProductResult(
                id="PROD_LAPTOP_01",
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
                match_reason="Excellent laptop for coding and software development with 16GB RAM under ₹70,000",
                match_attributes={"cpu": "Core i5 12th Gen", "ram": "16GB DDR4", "budget": "₹52,990 (Under ₹70,000)"}
            ),
            ProductResult(
                id="PROD_EARBUDS_01",
                title="SonicPro Active Noise Cancelling Wireless Earbuds",
                price_paise=189900,
                formatted_price="₹1,899",
                merchant="Amazon India",
                rating=4.7,
                reviews_count=890,
                product_url="https://www.amazon.in/dp/B09ANC9988",
                image_url="https://images.unsplash.com/photo-1590658268037-6bf12165a8df?w=600&auto=format&fit=crop&q=80",
                delivery="Tomorrow by 11 AM",
                category="electronics",
                match_score=96,
                match_reason="ANC noise cancellation + 40-hour battery life",
                match_attributes={"feature": "Active Noise Cancellation", "battery": "40 Hrs"}
            )
        ]

        items = electronics_items if category == "electronics" else apparel_items
        if max_price_paise:
            items = [item for item in items if item.price_paise <= max_price_paise]
        return items

class DemoFoodAdapter(MerchantAdapter):
    async def search(self, query: str, category: str, max_price_paise: int = None) -> List[ProductResult]:
        food_items = [
            ProductResult(
                id="PROD_TEA_01",
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
                match_attributes={"cuisines": "Indian Beverage", "size": "200ml", "budget": "₹35 (Under ₹50 limit)"}
            ),
            ProductResult(
                id="PROD_PIZZA_01",
                title="Medium Artisan Margherita Wood-Fired Pizza",
                price_paise=34900,
                formatted_price="₹349",
                merchant="Crust & Oven (Zomato)",
                rating=4.6,
                reviews_count=650,
                product_url="https://www.zomato.com/ncr/crust-oven-sector-62-noida/order",
                image_url="https://images.unsplash.com/photo-1513104890138-7c749659a591?w=600&auto=format&fit=crop&q=80",
                delivery="25 Mins",
                category="food",
                match_score=95,
                match_reason="Hand-tossed sourdough pizza topped with fresh mozzarella and basil",
                match_attributes={"type": "Pizza", "portions": "Serves 1-2", "budget": "₹349 (Under ₹500)"}
            )
        ]
        if max_price_paise:
            food_items = [item for item in food_items if item.price_paise <= max_price_paise]
        return food_items

class DemoRechargeAdapter(MerchantAdapter):
    async def search(self, query: str, category: str, max_price_paise: int = None) -> List[ProductResult]:
        recharge_items = [
            ProductResult(
                id="PROD_RECHARGE_01",
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
                match_attributes={"validity": "28 Days", "data": "2GB/Day 5G", "calls": "Unlimited"}
            ),
            ProductResult(
                id="PROD_RECHARGE_02",
                title="Airtel ₹349 Truly Unlimited 5G Plan (2GB/Day + Wynk Music)",
                price_paise=34900,
                formatted_price="₹349",
                merchant="Airtel Telecom Direct",
                rating=4.8,
                reviews_count=3200,
                product_url="https://www.airtel.in/recharge-online",
                image_url="https://images.unsplash.com/photo-1563986768609-322da13575f3?w=600&auto=format&fit=crop&q=80",
                delivery="Instant Activation",
                category="recharge",
                match_score=96,
                match_reason="2GB/day data + Apollo 24/7 Circle & Free Hellotunes",
                match_attributes={"validity": "28 Days", "data": "2GB/Day 5G"}
            )
        ]
        if max_price_paise:
            recharge_items = [item for item in recharge_items if item.price_paise <= max_price_paise]
        return recharge_items
