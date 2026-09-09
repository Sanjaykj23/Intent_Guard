import hashlib
import uuid
from typing import Dict, Any

class RazorpayVault:
    @staticmethod
    def hash_mandate_token(raw_token: str) -> str:
        """
        Creates SHA-256 hash of Razorpay payment mandate token.
        Raw tokens/secrets are NEVER exposed to the LLM or stored unhashed.
        """
        return hashlib.sha256(raw_token.encode('utf-8')).hexdigest()

    @staticmethod
    def generate_mock_mandate(user_email: str) -> Dict[str, str]:
        raw_token = f"rzp_mandate_token_{uuid.uuid4().hex[:12]}"
        cust_id = f"cust_{uuid.uuid4().hex[:8]}"
        token_hash = RazorpayVault.hash_mandate_token(raw_token)
        return {
            "razorpay_customer_id": cust_id,
            "razorpay_mandate_token_ref": raw_token,
            "token_hash_sha256": token_hash
        }

    @classmethod
    def hash_token(cls, raw_token: str) -> str:
        return cls.hash_mandate_token(raw_token)

    @classmethod
    def verify_token(cls, raw_token: str, token_hash: str) -> bool:
        return cls.hash_mandate_token(raw_token) == token_hash

razorpay_vault = RazorpayVault()
