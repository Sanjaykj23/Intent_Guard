"""
Mock Merchant Registry for Hackathon Prototype
Maps merchants, VPAs, category classifications, and verification statuses.
"""

from typing import Dict, Any, Optional

ALLOWED_CATEGORIES = {"GROCERY", "FOOD", "MOBILE_RECHARGE", "TRANSPORT", "SHOPPING"}
BLOCKED_CATEGORIES = {"GAMBLING", "CRYPTO", "CASH_WITHDRAWAL"}

MERCHANT_REGISTRY: Dict[str, Dict[str, Any]] = {
    "grocery@demo": {
        "name": "Demo Grocery Store",
        "vpa": "grocery@demo",
        "category": "GROCERY",
        "mcc": "5411",
        "verified": True
    },
    "food@demo": {
        "name": "Demo Food Store",
        "vpa": "food@demo",
        "category": "FOOD",
        "mcc": "5812",
        "verified": True
    },
    "electronics@demo": {
        "name": "Demo Electronics",
        "vpa": "electronics@demo",
        "category": "SHOPPING",
        "mcc": "5732",
        "verified": True
    },
    "recharge@demo": {
        "name": "Demo Mobile Recharge",
        "vpa": "recharge@demo",
        "category": "MOBILE_RECHARGE",
        "mcc": "4814",
        "verified": True
    },
    "transport@demo": {
        "name": "Demo Transport",
        "vpa": "transport@demo",
        "category": "TRANSPORT",
        "mcc": "4121",
        "verified": True
    },
    "demostore@demo": {
        "name": "Demo Store",
        "vpa": "demostore@demo",
        "category": "SHOPPING",
        "mcc": "5691",
        "verified": True
    },
    "crypto@demo": {
        "name": "Demo Crypto",
        "vpa": "crypto@demo",
        "category": "CRYPTO",
        "mcc": "6051",
        "verified": False
    },
    "casino@demo": {
        "name": "Demo Casino",
        "vpa": "casino@demo",
        "category": "GAMBLING",
        "mcc": "7995",
        "verified": False
    }
}

class MerchantRegistry:
    @staticmethod
    def get_merchant_by_vpa(vpa: str) -> Optional[Dict[str, Any]]:
        clean_vpa = vpa.strip().lower()
        if clean_vpa in MERCHANT_REGISTRY:
            return MERCHANT_REGISTRY[clean_vpa]
        
        # Fuzzy fallback lookup by merchant name or keyword
        for item in MERCHANT_REGISTRY.values():
            if item["vpa"] == clean_vpa or item["name"].lower() in clean_vpa:
                return item
        return None

    @staticmethod
    def resolve_merchant(name_or_vpa: str, category: str = "SHOPPING") -> Dict[str, Any]:
        target = name_or_vpa.strip().lower()
        
        # Try direct match
        for vpa, m in MERCHANT_REGISTRY.items():
            if vpa == target or m["name"].lower() == target:
                return m

        # Try category match
        cat_upper = category.upper()
        if cat_upper == "CRYPTO":
            return MERCHANT_REGISTRY["crypto@demo"]
        elif cat_upper == "GAMBLING":
            return MERCHANT_REGISTRY["casino@demo"]
        elif cat_upper == "GROCERY":
            return MERCHANT_REGISTRY["grocery@demo"]
        elif cat_upper == "FOOD":
            return MERCHANT_REGISTRY["food@demo"]
        elif cat_upper == "MOBILE_RECHARGE":
            return MERCHANT_REGISTRY["recharge@demo"]
        elif cat_upper == "TRANSPORT":
            return MERCHANT_REGISTRY["transport@demo"]
        elif "electronic" in target or "phone" in target or "laptop" in target:
            return MERCHANT_REGISTRY["electronics@demo"]

        # Default fallback merchant
        return {
            "name": name_or_vpa if name_or_vpa else "Demo Store",
            "vpa": f"{target.replace(' ', '')}@demo" if "@" not in target else target,
            "category": cat_upper if cat_upper in ALLOWED_CATEGORIES or cat_upper in BLOCKED_CATEGORIES else "SHOPPING",
            "mcc": "5691",
            "verified": True
        }

merchant_registry = MerchantRegistry()
