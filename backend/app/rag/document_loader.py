import json
from typing import List, Dict, Any

DEFAULT_POLICY_DOCUMENTS = [
    {
        "document_id": "DOC_MERCHANT_AMAZON_01",
        "merchant_id": "Amazon India",
        "document_type": "return_policy",
        "title": "Amazon Electronics & Apparel Return & Refund Policy",
        "content": "Laptops and electronics can be returned within 7 days of delivery if defective or damaged. Items must include original box, accessories, and tag. Refunds are processed to original payment method within 3 business days of return pick-up. Apparel items have a 10-day exchange or return window.",
        "source": "merchant_policies/amazon_return_policy.pdf"
    },
    {
        "document_id": "DOC_MERCHANT_FLIPKART_01",
        "merchant_id": "Flipkart Store",
        "document_type": "return_policy",
        "title": "Flipkart Footwear & Mobile Return Rules",
        "content": "Running shoes and apparel have a 7-day replacement guarantee for size or manufacturing defects. Brand warranty applies for shoes and electronics. Refund request creates Instant Credit to connected payment vault.",
        "source": "merchant_policies/flipkart_policy.txt"
    },
    {
        "document_id": "DOC_MERCHANT_TELECOM_01",
        "merchant_id": "Jio Telecom Direct",
        "document_type": "recharge_policy",
        "title": "Prepaid Mobile Recharge Activation & Cancellation Terms",
        "content": "Prepaid mobile recharges are activated instantly upon transaction authorization. 5G unlimited data requires a 5G compatible device. Once executed, prepaid mobile recharges cannot be refunded or cancelled unless network activation failure occurs.",
        "source": "service_knowledge/jio_recharge_terms.json"
    },
    {
        "document_id": "DOC_MERCHANT_FOOD_01",
        "merchant_id": "Gupta Chai Corner (Swiggy)",
        "document_type": "food_policy",
        "title": "Quick Food Delivery & Cancellation Policy",
        "content": "Food orders are prepared immediately upon order confirmation. Order cancellation is permitted only within 60 seconds of placing order. Temperature-controlled packaging ensures tea stays hot during transit.",
        "source": "service_knowledge/swiggy_food_policy.md"
    }
]

class DocumentLoader:
    def __init__(self):
        self.documents = DEFAULT_POLICY_DOCUMENTS

    def load_all_documents(self) -> List[Dict[str, Any]]:
        return self.documents

document_loader = DocumentLoader()
