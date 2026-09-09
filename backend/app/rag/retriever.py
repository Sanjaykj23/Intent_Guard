from typing import List, Dict, Any
from backend.app.vector_db.qdrant_service import qdrant_service
from backend.app.schemas.intent_schemas import ExtractedIntent, ProductResult
from backend.app.rag.reranker import reranker

class HybridRAGRetriever:
    def retrieve_policy_context(self, user_query: str) -> str:
        """
        Queries merchant_policies and service_knowledge vector collections.
        Returns top relevant policy context to inject into Llama LLM prompt.
        """
        policy_results = qdrant_service.search_similar("merchant_policies", user_query, top_k=2)
        service_results = qdrant_service.search_similar("service_knowledge", user_query, top_k=1)

        combined = policy_results + service_results
        if not combined:
            return ""

        context_blocks = []
        for r in combined:
            payload = r.get("payload", {})
            title = payload.get("source", "Policy Document")
            content = payload.get("content", "")
            context_blocks.append(f"[{title}]: {content}")

        return "\n".join(context_blocks)

    def cache_and_rerank_live_products(self, products: List[ProductResult], intent: ExtractedIntent) -> List[ProductResult]:
        """
        Stores temporary product vectors in Qdrant live_search_cache (10-min TTL)
        and applies reranker.
        """
        for p in products:
            qdrant_service.upsert(
                collection_name="live_search_cache",
                id_=p.id,
                text=f"{p.title} {p.category} {p.formatted_price}",
                payload={"title": p.title, "merchant": p.merchant, "url": p.product_url},
                ttl_seconds=600 # 10 minute TTL
            )

        return reranker.rerank_products(products, intent)

retriever = HybridRAGRetriever()
