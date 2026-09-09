from typing import List, Dict, Any
from backend.app.schemas.intent_schemas import ProductResult, ExtractedIntent
from backend.app.rag.embedding_service import embedding_service

class Reranker:
    def rerank_products(
        self,
        products: List[ProductResult],
        intent: ExtractedIntent,
        weights: Dict[str, float] = None
    ) -> List[ProductResult]:
        """
        Applies configurable weighted scoring formula:
        Score = 0.40 * SemanticSimilarity + 0.25 * ConstraintMatch + 0.15 * PriceMatch + 0.10 * Rating + 0.10 * Freshness
        """
        w = weights or {
            "semantic": 0.40,
            "constraint": 0.25,
            "price": 0.15,
            "rating": 0.10,
            "freshness": 0.10
        }

        query_vec = embedding_service.get_embedding(intent.product or "")

        for prod in products:
            prod_vec = embedding_service.get_embedding(f"{prod.title} {prod.match_reason}")
            sim = max(0.0, embedding_service.cosine_similarity(query_vec, prod_vec))

            # Constraint Match
            constraint_match = 1.0 if not intent.max_price_paise or prod.price_paise <= intent.max_price_paise else 0.2

            # Price Match (Closer to budget is better)
            price_match = 1.0
            if intent.max_price_paise:
                diff = abs(intent.max_price_paise - prod.price_paise)
                price_match = max(0.1, 1.0 - (diff / intent.max_price_paise))

            # Rating normalized (out of 5)
            rating_norm = (prod.rating or 4.0) / 5.0

            # Freshness (delivery speed)
            freshness = 0.9 if "tomorrow" in (prod.delivery or "").lower() or "instant" in (prod.delivery or "").lower() else 0.7

            final_score = (
                w["semantic"] * sim +
                w["constraint"] * constraint_match +
                w["price"] * price_match +
                w["rating"] * rating_norm +
                w["freshness"] * freshness
            )

            prod.match_score = int(final_score * 100)

        # Sort descending by match_score
        return sorted(products, key=lambda x: x.match_score, reverse=True)

reranker = Reranker()
