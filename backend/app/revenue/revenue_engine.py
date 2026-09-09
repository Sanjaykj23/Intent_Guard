from typing import List, Dict, Any
from backend.app.schemas.intent_schemas import ProductResult

class MerchantRevenueEngine:
    def generate_growth_recommendations(self, top_product: ProductResult) -> Dict[str, Any]:
        """
        Generates Merchant Revenue Engine recommendations:
        1. Upselling (higher tier variant)
        2. Cross-Selling (complementary accessories)
        3. Smart Bundles (discounted item packages)
        """
        if not top_product:
            return {"upsell": None, "cross_sell": [], "bundle": None}

        cat = (top_product.category or "").lower()
        title = top_product.title.lower()

        upsell = None
        cross_sell = []
        bundle = None

        if "laptop" in title or cat == "electronics":
            upsell = {
                "type": "UPSELL",
                "title": "Upgrade to 1TB SSD & Intel Core i7 Variant",
                "price_paise": top_product.price_paise + 1200000,
                "formatted_price": f"₹{(top_product.price_paise + 1200000) // 100:,}",
                "description": "Double your storage and upgrade processing power for heavy AI workloads.",
                "merchant": top_product.merchant
            }
            cross_sell = [
                {
                    "id": "CS_MOUSE_01",
                    "title": "Logitech Wireless Ergonomic Silent Mouse",
                    "price_paise": 119900,
                    "formatted_price": "₹1,199",
                    "product_url": "https://www.amazon.in/dp/B07W5JK111"
                },
                {
                    "id": "CS_BAG_01",
                    "title": "Waterproof Padded Laptop Backpack (15.6\")",
                    "price_paise": 89900,
                    "formatted_price": "₹899",
                    "product_url": "https://www.amazon.in/dp/B08X599222"
                }
            ]
            bundle = {
                "type": "SMART_BUNDLE",
                "title": "Developer Workspace Essentials Bundle",
                "items": [top_product.title, "Logitech Wireless Mouse", "Padded Laptop Backpack"],
                "original_total_paise": top_product.price_paise + 119900 + 89900,
                "bundle_price_paise": top_product.price_paise + 150000, # Savings of ₹598
                "formatted_bundle_price": f"₹{(top_product.price_paise + 150000) // 100:,}",
                "savings_formatted": "Save ₹598 with Bundle Discount",
                "merchant": top_product.merchant
            }

        elif "tea" in title or cat == "food":
            cross_sell = [
                {
                    "id": "CS_BISCUIT_01",
                    "title": "Handcrafted Whole Wheat Bakery Biscuits (200g)",
                    "price_paise": 2500,
                    "formatted_price": "₹25",
                    "product_url": "https://www.swiggy.com/menu/bakery-biscuits"
                }
            ]
            bundle = {
                "type": "SMART_BUNDLE",
                "title": "Evening Tea & Snacks Combo",
                "items": [top_product.title, "Bakery Biscuits", "Crispy Veg Samosa (2 Pcs)"],
                "original_total_paise": 8500,
                "bundle_price_paise": 6500,
                "formatted_bundle_price": "₹65",
                "savings_formatted": "Save ₹20 Combo Discount",
                "merchant": top_product.merchant
            }

        elif "recharge" in title or cat == "recharge":
            upsell = {
                "type": "UPSELL",
                "title": "Upgrade to ₹399 Annual OTT Special Plan (2.5GB/Day)",
                "price_paise": 39900,
                "formatted_price": "₹399",
                "description": "Includes free Disney+ Hotstar Mobile subscription for 84 days.",
                "merchant": top_product.merchant
            }

        else: # Apparel / General
            cross_sell = [
                {
                    "id": "CS_SOCK_01",
                    "title": "Nike Cushion Cotton Ankle Socks (Pack of 3)",
                    "price_paise": 49900,
                    "formatted_price": "₹499",
                    "product_url": "https://www.flipkart.com/nike-socks/p/itm11"
                }
            ]

        return {
            "upsell": upsell,
            "cross_sell": cross_sell,
            "bundle": bundle
        }

revenue_engine = MerchantRevenueEngine()
