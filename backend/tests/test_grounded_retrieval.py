import pytest
from backend.app.normalizer.url_classifier import url_classifier
from backend.app.search.query_builder import query_builder
from backend.app.ai.llama_service import llama_service
from backend.app.schemas.intent_schemas import ProductResult

def test_url_classifier_exact_vs_search_page():
    amazon_product_url = "https://www.amazon.in/dp/B08X123456"
    flipkart_search_url = "https://www.flipkart.com/search?q=mobile+charger"

    res_product = url_classifier.classify_url(amazon_product_url)
    assert res_product["url_type"] == "EXACT_PRODUCT_PAGE"
    assert res_product["is_exact_product"] is True

    res_search = url_classifier.classify_url(flipkart_search_url)
    assert res_search["url_type"] == "MERCHANT_SEARCH_PAGE"
    assert res_search["is_exact_product"] is False

def test_query_builder_deterministic_terms():
    slots = {"product": "mobile charger", "max_price_paise": 50000, "features": ["20W fast charging"]}
    queries = query_builder.build_search_queries(slots)
    assert len(queries) == 3
    assert "mobile charger" in queries[0]
    assert "under 500 INR" in queries[0]

@pytest.mark.asyncio
async def test_llama_id_only_recommendation_protocol():
    mock_candidates = [
        ProductResult(
            id="p1", title="Ambrane 20W Charger", price_paise=44900, formatted_price="₹449",
            merchant="Amazon India", rating=4.7, reviews_count=100, product_url="https://amazon.in/dp/B08X1",
            image_url="", delivery="Tomorrow", category="electronics", match_score=95, match_reason="", match_attributes={}
        ),
        ProductResult(
            id="p2", title="Portronics Fast Charger", price_paise=34900, formatted_price="₹349",
            merchant="Flipkart Store", rating=4.5, reviews_count=50, product_url="https://flipkart.com/p/itm2",
            image_url="", delivery="Tomorrow", category="electronics", match_score=90, match_reason="", match_attributes={}
        )
    ]
    rec_res = await llama_service.recommend_verified_candidates(mock_candidates, "I want a mobile charger under 500")
    assert "recommended_ids" in rec_res
    assert len(rec_res["recommended_ids"]) > 0
    # Every recommended ID must be in candidates!
    valid_ids = {c.id for c in mock_candidates}
    for r_id in rec_res["recommended_ids"]:
        assert r_id in valid_ids
