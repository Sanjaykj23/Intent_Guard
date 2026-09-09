import pytest
from backend.app.search.providers.live_search_provider import live_search_provider
from backend.app.normalizer.product_normalizer import ProductNormalizer
from backend.app.revenue.revenue_engine import revenue_engine
from backend.app.schemas.intent_schemas import ProductResult

@pytest.mark.asyncio
async def test_live_search_provider_execution():
    products = await live_search_provider.search_products("laptop", max_price_paise=7000000)
    assert len(products) > 0
    top = products[0]
    assert top.product_url.startswith("https://")
    assert top.price_paise <= 7000000

@pytest.mark.asyncio
async def test_live_food_search():
    food = await live_search_provider.search_food("tea", max_price_paise=5000)
    assert len(food) > 0
    assert "tea" in food[0].title.lower() or "chai" in food[0].title.lower()

def test_product_normalizer_and_scoring():
    raw = [
        ProductResult(
            id="P1", title="ASUS Laptop", price_paise=5000000, formatted_price="₹50,000",
            merchant="Amazon", rating=4.5, reviews_count=10, product_url="https://amazon.in/p1",
            image_url="", delivery="Tomorrow", category="electronics", match_score=80, match_reason="", match_attributes={}
        )
    ]
    normalized = ProductNormalizer.normalize_and_rank(raw, user_priorities=["laptop"])
    assert len(normalized) == 1
    assert normalized[0].match_score >= 80

def test_merchant_revenue_engine_upsell_and_bundles():
    mock_laptop = ProductResult(
        id="P1", title="ASUS Vivobook 15 Intel Core i5 Laptop", price_paise=5299000, formatted_price="₹52,990",
        merchant="Amazon India", rating=4.7, reviews_count=10, product_url="https://amazon.in/p1",
        image_url="", delivery="Tomorrow", category="electronics", match_score=95, match_reason="", match_attributes={}
    )

    recs = revenue_engine.generate_growth_recommendations(mock_laptop)
    assert "upsell" in recs and recs["upsell"] is not None
    assert "bundle" in recs and recs["bundle"] is not None
    assert recs["bundle"]["type"] == "SMART_BUNDLE"
    assert "Save ₹" in recs["bundle"]["savings_formatted"]
