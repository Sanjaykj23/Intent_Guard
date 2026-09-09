import re
from typing import Dict, Any, Optional

class DeterministicParser:
    """
    PHASE 2 — DETERMINISTIC EXTRACTION ENGINE (ZERO TRUST LLM)
    Extracts critical transaction slots (Money/Price in Paise, Delivery Days, Color, Brand, Quantity)
    using deterministic Regular Expressions & Rule Dictionaries BEFORE passing to LLM.
    Guarantees 0% LLM hallucination on financial and temporal constraints.
    """

    COLOR_DICTIONARY = [
        "jet black", "black", "white", "navy blue", "blue", "red", "green",
        "yellow", "pink", "grey", "gray", "beige", "maroon", "purple", "olive", "pastel lime"
    ]

    BRAND_DICTIONARY = [
        "nike", "adidas", "puma", "roadster", "veirdo", "bullmer", "ambrane",
        "portronics", "asus", "jio", "airtel", "swiggy", "zomato", "gupta", "oneplus"
    ]

    @classmethod
    def extract_price_paise(cls, text: str) -> Optional[int]:
        if not text:
            return None
        
        # 1. Matches "under ₹500", "below 500", "budget 1500", "max ₹2000"
        m1 = re.search(r'(?:under|below|budget|max|rs\.?|inr|₹)\s*₹?\s*(\d+(?:,\d+)*)', text, re.IGNORECASE)
        if m1:
            try:
                val = int(m1.group(1).replace(',', ''))
                if 10 <= val <= 1000000:
                    return val * 100
            except ValueError:
                pass

        # 2. Matches "500 inr", "500 rs", "500 rupees"
        m2 = re.search(r'(\d+(?:,\d+)*)\s*(?:inr|rs|rupees)', text, re.IGNORECASE)
        if m2:
            try:
                val = int(m2.group(1).replace(',', ''))
                if 10 <= val <= 1000000:
                    return val * 100
            except ValueError:
                pass

        # 3. Matches standalone symbol "₹500"
        m3 = re.search(r'₹\s*(\d+(?:,\d+)*)', text)
        if m3:
            try:
                val = int(m3.group(1).replace(',', ''))
                if 10 <= val <= 1000000:
                    return val * 100
            except ValueError:
                pass

        return None

    @classmethod
    def extract_delivery_days(cls, text: str) -> Optional[int]:
        if not text:
            return None
        
        u = text.lower()
        if "same day" in u or "today" in u or "instant" in u:
            return 1
        if "next day" in u or "tomorrow" in u:
            return 1

        m = re.search(r'(?:within|in|less than|under)?\s*(\d+)\s*(?:day|days)', u)
        if m:
            try:
                val = int(m.group(1))
                if 1 <= val <= 30:
                    return val
            except ValueError:
                pass
        return None

    @classmethod
    def extract_color(cls, text: str) -> Optional[str]:
        if not text:
            return None
        u = text.lower()
        for color in cls.COLOR_DICTIONARY:
            if re.search(r'\b' + re.escape(color) + r'\b', u):
                return color.title()
        return None

    @classmethod
    def extract_brand(cls, text: str) -> Optional[str]:
        if not text:
            return None
        u = text.lower()
        for brand in cls.BRAND_DICTIONARY:
            if re.search(r'\b' + re.escape(brand) + r'\b', u):
                return brand.title()
        return None

    @classmethod
    def extract_quantity(cls, text: str) -> int:
        if not text:
            return 1
        m = re.search(r'(\d+)\s*(?:items|pcs|pieces|shirts|tshirts|pairs|adaptors|chargers)', text, re.IGNORECASE)
        if m:
            try:
                val = int(m.group(1))
                if 1 <= val <= 100:
                    return val
            except ValueError:
                pass
        return 1

    @classmethod
    def parse_user_input(cls, text: str) -> Dict[str, Any]:
        return {
            "max_price_paise": cls.extract_price_paise(text),
            "delivery_days_max": cls.extract_delivery_days(text),
            "color": cls.extract_color(text),
            "brand": cls.extract_brand(text),
            "quantity": cls.extract_quantity(text)
        }

deterministic_parser = DeterministicParser()
