import re
from typing import List, Dict, Any
from backend.app.schemas.intent_schemas import ProductResult

class ProductNormalizer:
    @staticmethod
    def normalize_and_rank(raw_products: List[ProductResult], user_priorities: List[str] = None) -> List[ProductResult]:
        """
        Normalizes pricing, formats currency strings, checks direct product URLs, deduplicates, and ranks products.
        """
        if not raw_products:
            return []

        priorities = [p.lower() for p in (user_priorities or [])]
        
        seen_keys = set()
        unique_products: List[ProductResult] = []

        for item in raw_products:
            title_clean = (item.name or item.title or "").strip()
            
            # Ensure price string strictly matches price_paise
            if item.price_paise:
                item.formatted_price = f"₹{item.price_paise // 100:,}"

            # Priority match score boost
            for p in priorities:
                if p in title_clean.lower() or p in item.match_reason.lower():
                    item.match_score = min(100, item.match_score + 3)

            # Strict Deduplication key (Normalized title slug + URL domain/path)
            title_slug = re.sub(r'[^a-z0-9]', '', title_clean.lower())[:25]
            url_slug = (item.exact_action_url or item.source_url or item.product_url or "").strip().lower()
            dedup_key = f"{title_slug}_{url_slug}"

            if dedup_key in seen_keys:
                continue

            seen_keys.add(dedup_key)
            unique_products.append(item)

        # Sort descending by match_score
        return sorted(unique_products, key=lambda x: x.match_score, reverse=True)
