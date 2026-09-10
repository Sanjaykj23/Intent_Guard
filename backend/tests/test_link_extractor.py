import pytest
from backend.app.search.link_extractor import EcommerceLinkExtractor

def test_link_extractor_cleaning():
    input1 = "find me wireless earbuds under ₹1500"
    res1 = EcommerceLinkExtractor.extract_urls(input1)
    assert res1["cleaned_keywords"] == "wireless earbuds under 1500"
    assert res1["google_shopping_url"] == "https://www.google.com/search?tbm=shop&q=wireless+earbuds+under+1500"
    assert res1["amazon_url"] == "https://www.amazon.in/s?k=wireless+earbuds+under+1500"
    assert res1["flipkart_url"] == "https://www.flipkart.com/search?q=wireless+earbuds+under+1500"

def test_link_extractor_dollar_filler():
    input2 = "I want to buy running shoes $20"
    res2 = EcommerceLinkExtractor.extract_urls(input2)
    assert res2["cleaned_keywords"] == "running shoes 20"
    assert "https://www.google.com/search?tbm=shop&q=running+shoes+20" in res2["google_shopping_url"]
    assert "https://www.amazon.in/s?k=running+shoes+20" in res2["amazon_url"]
    assert "https://www.flipkart.com/search?q=running+shoes+20" in res2["flipkart_url"]

def test_link_extractor_placeholder():
    res3 = EcommerceLinkExtractor.extract_urls("{{USER_INPUT}}")
    assert res3["cleaned_keywords"] == "products"
    assert res3["google_shopping_url"] == "https://www.google.com/search?tbm=shop&q=products"
