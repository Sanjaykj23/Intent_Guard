import pytest
from backend.app.rag.document_loader import document_loader
from backend.app.rag.chunker import chunker
from backend.app.rag.embedding_service import embedding_service
from backend.app.vector_db.qdrant_service import qdrant_service
from backend.app.rag.retriever import retriever
from backend.app.schemas.intent_schemas import ExtractedIntent, ProductResult

def test_document_loader_and_chunker():
    docs = document_loader.load_all_documents()
    assert len(docs) > 0
    chunks = chunker.chunk_document(docs[0])
    assert len(chunks) > 0
    assert "chunk_id" in chunks[0]
    assert "content" in chunks[0]

def test_dense_embeddings_and_cosine_similarity():
    v1 = embedding_service.get_embedding("electronics 7 days return policy")
    v2 = embedding_service.get_embedding("laptops return window is 7 days")
    v3 = embedding_service.get_embedding("masala kulhad chai beverage")

    sim_high = embedding_service.cosine_similarity(v1, v2)
    sim_low = embedding_service.cosine_similarity(v1, v3)

    assert sim_high > sim_low

def test_qdrant_vector_db_policy_search():
    results = qdrant_service.search_similar("merchant_policies", "return policy for laptops", top_k=2)
    assert len(results) > 0
    top_payload = results[0]["payload"]
    assert "content" in top_payload

def test_rag_retriever_and_temporary_vector_cache():
    context = retriever.retrieve_policy_context("Can I return a laptop after buying it?")
    assert "return" in context.lower() or "7 days" in context.lower()

    # Test dynamic reranker
    intent = ExtractedIntent(
        intent="product_search",
        category="apparel",
        product="black running shoes",
        max_price_paise=500000,
        currency="INR"
    )
    mock_prods = [
        ProductResult(
            id="P1", title="Black Running Shoes", price_paise=349500, formatted_price="₹3,495",
            merchant="Flipkart", rating=4.8, reviews_count=100, product_url="https://flipkart.com/p1",
            image_url="", delivery="Tomorrow", category="apparel", match_score=80, match_reason="", match_attributes={}
        )
    ]
    reranked = retriever.cache_and_rerank_live_products(mock_prods, intent)
    assert len(reranked) == 1
    assert reranked[0].match_score > 0
