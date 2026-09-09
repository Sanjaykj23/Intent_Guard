from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any

class IntentRequest(BaseModel):
    user_message: str
    user_id: Optional[str] = "USER_DEFAULT_001"

class ExtractedIntent(BaseModel):
    intent: str = Field(description="Detected task type: greeting, product_search, food_order, mobile_recharge, bill_payment, policy_question, compare_products")
    category: Optional[str] = Field(default=None, description="Category like apparel, electronics, food, recharge, general")
    product: Optional[str] = Field(default=None, description="Target item name or query keywords")
    max_price_paise: Optional[int] = Field(default=None, description="Budget upper limit in paise")
    currency: str = "INR"
    quantity: int = 1
    priorities: List[str] = Field(default_factory=list, description="Extracted priorities like camera, battery, fit")
    delivery_location: Optional[str] = None
    delivery_days_max: Optional[int] = None
    color: Optional[str] = None
    brand: Optional[str] = None
    transaction_required: bool = False
    confidence: float = 0.95

class CanonicalIntent(BaseModel):
    intent_id: str
    action: str              # "SEARCH_PRODUCT", "ORDER_FOOD", "MOBILE_RECHARGE", "PAY_BILL", "GREETING", "POLICY_QUESTION"
    category: str            # "apparel", "electronics", "food", "recharge", "utility", "general"
    product_query: str
    max_price_paise: Optional[int] = None
    currency: str = "INR"
    delivery_days_max: Optional[int] = None
    color: Optional[str] = None
    brand: Optional[str] = None
    quantity: int = 1
    status: str = "VALIDATED"  # "VALIDATED" | "REJECTED"
    slot_sources: Dict[str, str] = Field(default_factory=dict) # e.g. {"max_price_paise": "DETERMINISTIC_REGEX", "action": "LLM_INFERENCE"}

import re
from pydantic import field_validator

class UserRegistration(BaseModel):
    name: str
    email: str
    password: str
    phone: str = Field(default="+919876543210", description="Mobile number in E.164 format e.g. +919876543210")
    address: str = Field(default="123 Tech Park, Bengaluru, KA", description="Delivery address")
    razorpay_mandate_token: Optional[str] = "mandate_token_demo_9921"

    @field_validator('phone')
    @classmethod
    def validate_e164_phone(cls, v: str) -> str:
        clean_v = v.strip()
        if not clean_v.startswith("+"):
            clean_v = f"+91{clean_v}"
        if not re.match(r"^\+[1-9]\d{7,14}$", clean_v):
            raise ValueError("Mobile number must be in valid E.164 format (e.g., +919876543210)")
        return clean_v

class UserLoginRequest(BaseModel):
    email: str
    password: str

class UPICircleSetupRequest(BaseModel):
    primary_vpa: str = Field(description="Primary user bank VPA e.g. user@upi")
    per_txn_limit_paise: int = Field(default=500000, description="Max per-transaction limit in paise (hard cap ₹5,000)")
    monthly_limit_paise: int = Field(default=1500000, description="Max monthly cumulative limit in paise (hard cap ₹15,000)")
    upi_pin: Optional[str] = Field(default=None, description="4 or 6-digit Primary Bank UPI PIN for initial mandate authorization")

    @field_validator('primary_vpa')
    @classmethod
    def validate_vpa(cls, v: str) -> str:
        clean = v.strip()
        if "@" not in clean or len(clean) < 4:
            raise ValueError("Invalid VPA format. Must contain '@' e.g. user@upi")
        return clean

class UserPolicySchema(BaseModel):
    user_id: str
    daily_limit_paise: int = 500000 # ₹5,000
    transaction_limit_paise: int = 100000 # ₹1,000
    auto_approval_threshold_paise: int = 20000 # ₹200
    allowed_categories: List[str] = ["apparel", "electronics", "food", "recharge"]
    policy_version: int = 1

from pydantic import BaseModel, Field, model_validator
import uuid

class UCPActionCandidate(BaseModel):
    ucp_version: str = "v1.0"
    candidate_id: str = ""
    provider: str = "Universal Provider"
    merchant_id: str = "MERCHANT_DEFAULT"
    action_type: str = "PURCHASE_PRODUCT"
    name: str = ""
    price_paise: Optional[int] = None
    formatted_price: str = ""
    currency: str = "INR"
    source_url: Optional[str] = ""
    exact_action_url: Optional[str] = ""
    acm_stage: str = "DISCOVER" # DISCOVER | QUOTE | LOCK | PAY | AUDIT
    idempotency_key: str = ""
    verified: bool = False       # True ONLY if source verified by provider adapter
    source: str = "merchant_api"
    rating: float = 4.6
    reviews_count: int = 500
    delivery: str = "Fast Delivery"
    image_url: str = ""
    category: str = "general"
    retrieved_at: str = ""
    match_score: int = 95
    match_reason: str = ""
    match_attributes: Dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode='before')
    @classmethod
    def harmonize_fields(cls, values: Any) -> Any:
        if isinstance(values, dict):
            # candidate_id vs id
            if "candidate_id" not in values or not values.get("candidate_id"):
                values["candidate_id"] = values.get("id") or f"ucp_cand_{uuid.uuid4().hex[:8]}"
            # name vs title
            if "name" not in values or not values.get("name"):
                values["name"] = values.get("title") or "Item"
            # provider vs merchant
            if "provider" not in values or not values.get("provider"):
                values["provider"] = values.get("merchant") or "Merchant"
            # merchant_id
            if "merchant_id" not in values or not values.get("merchant_id"):
                m_name = values.get("provider") or values.get("merchant") or "DEFAULT"
                values["merchant_id"] = f"MERCHANT_{m_name.upper().replace(' ', '_')}"
            # action_type
            if "action_type" not in values or not values.get("action_type"):
                cat = (values.get("category") or "").lower()
                if cat == "food":
                    values["action_type"] = "ORDER_FOOD"
                elif cat in ["recharge", "telecom"]:
                    values["action_type"] = "MOBILE_RECHARGE"
                elif cat == "utility":
                    values["action_type"] = "PAY_BILL"
                else:
                    values["action_type"] = "PURCHASE_PRODUCT"
            # URLs: source_url and exact_action_url vs product_url
            prod_url = values.get("product_url")
            if "source_url" not in values or values["source_url"] is None:
                values["source_url"] = prod_url or ""
            if "exact_action_url" not in values or values["exact_action_url"] is None:
                values["exact_action_url"] = prod_url or ""
        return values

    @property
    def id(self) -> str:
        return self.candidate_id

    @property
    def title(self) -> str:
        return self.name

    @property
    def merchant(self) -> str:
        return self.provider

    @property
    def product_url(self) -> Optional[str]:
        return self.exact_action_url or self.source_url

# Backward compatibility alias
ProductResult = UCPActionCandidate

class QuoteSchema(BaseModel):
    quote_id: str
    user_id: str
    merchant_name: str
    product_name: str
    price_paise: int
    product_url: str
    expires_at: str
    quote_hash: str

class PolicyCheckResult(BaseModel):
    allowed: bool
    status_code: str
    risk_level: str # LOW, MEDIUM, HIGH
    auto_approved: bool
    reason: str
    daily_spent_paise: int
    daily_limit_paise: int
    transaction_limit_paise: int

class TransactionExecuteRequest(BaseModel):
    quote_id: str
    user_id: str
    amount_paise: int
    upi_vpa: Optional[str] = None
    upi_pin: Optional[str] = None

class AuditEventSchema(BaseModel):
    id: int
    event_id: str
    event_type: str
    payload_json: str
    previous_hash: str
    current_hash: str
    timestamp: str
