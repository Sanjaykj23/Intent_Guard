import re
import urllib.parse
from typing import Dict, Any

class EcommerceLinkExtractor:
    """
    E-Commerce Link Extraction Engine.
    Converts natural conversational user input into clean, functional search URLs.
    """
    FILLER_WORDS = [
        r"\bfind\s+me\s+a\b",
        r"\bfind\s+me\b",
        r"\bcan\s+you\s+show\s+me\b",
        r"\bcan\s+you\s+find\b",
        r"\bshow\s+me\b",
        r"\bi\s+want\s+to\s+buy\b",
        r"\bi\s+want\s+to\s+get\b",
        r"\bi'm\s+looking\s+for\b",
        r"\blooking\s+for\b",
        r"\bi\s+need\s+a\b",
        r"\bi\s+need\b",
        r"\bsearch\s+for\b",
        r"\bplease\s+find\b",
        r"\bplease\s+show\b"
    ]

    @classmethod
    def clean_keywords(cls, text: str) -> str:
        if not text or text.strip() == "{{USER_INPUT}}":
            return "products"

        cleaned = text.lower()

        # Strip filler phrases
        for pattern in cls.FILLER_WORDS:
            cleaned = re.sub(pattern, "", cleaned, flags=re.IGNORECASE)

        # Strip currency symbols (₹, $, €, £, rs., rs, inr) while preserving numbers
        cleaned = re.sub(r"[₹$€£]", "", cleaned)
        cleaned = re.sub(r"\b(rs\.?|inr)\s*", "", cleaned, flags=re.IGNORECASE)

        # Deduplicate repeated adjacent words (e.g. "under 1500 under 1500" -> "under 1500")
        words = cleaned.split()
        dedup_words = []
        for w in words:
            if not dedup_words or dedup_words[-1] != w:
                dedup_words.append(w)
        cleaned = " ".join(dedup_words)

        # Remove leading "a " or "an " if remaining
        cleaned = re.sub(r"^(a|an|the)\s+", "", cleaned, flags=re.IGNORECASE)

        # Normalize whitespace
        cleaned = " ".join(cleaned.split()).strip()
        return cleaned or "products"

    @classmethod
    def extract_urls(cls, user_input: str) -> Dict[str, str]:
        cleaned = cls.clean_keywords(user_input)
        encoded = urllib.parse.quote_plus(cleaned)

        return {
            "cleaned_keywords": cleaned,
            "google_shopping_url": f"https://www.google.com/search?tbm=shop&q={encoded}",
            "amazon_url": f"https://www.amazon.in/s?k={encoded}",
            "flipkart_url": f"https://www.flipkart.com/search?q={encoded}"
        }

link_extractor = EcommerceLinkExtractor()
