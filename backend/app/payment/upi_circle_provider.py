"""
UPI Circle Provider Abstraction Layer & Mock Implementation
Demonstrates provider decoupling for hackathon demo.
Can be swapped seamlessly with an authorized bank PSP/TPAP integration in production.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, Tuple, Set
import uuid
import time
from datetime import datetime, timedelta, timezone

from backend.app.payment.mock_bank import mock_bank
from backend.app.payment.merchant_registry import ALLOWED_CATEGORIES, BLOCKED_CATEGORIES

class UPICircleProvider(ABC):
    """
    Abstract Interface for NPCI UPI Circle Delegation Providers.
    Decouples the Payment Decision Engine (PDE) from payment rail implementations.
    """

    @abstractmethod
    async def create_delegation(
        self,
        primary_user_id: str,
        monthly_limit_paise: int = 1500000,
        transaction_limit_paise: int = 500000,
        allowed_categories: Optional[list] = None,
        blocked_categories: Optional[list] = None,
        secondary_profile_id: str = "AI_AGENT_001"
    ) -> Dict[str, Any]:
        pass

    @abstractmethod
    async def get_delegation(self, user_id_or_delegation_id: str) -> Optional[Dict[str, Any]]:
        pass

    @abstractmethod
    async def revoke_delegation(self, user_id_or_delegation_id: str) -> bool:
        pass

    @abstractmethod
    async def validate_delegation(
        self,
        delegation_id: str,
        amount_paise: int,
        category: str
    ) -> Tuple[bool, str]:
        pass

    @abstractmethod
    async def initiate_payment(
        self,
        delegation_id: str,
        amount_paise: int,
        merchant_vpa: str,
        category: str,
        transaction_id: str,
        merchant_name: str = "Demo Merchant"
    ) -> Dict[str, Any]:
        pass

    @abstractmethod
    async def get_payment_status(self, transaction_id: str) -> Dict[str, Any]:
        pass


class MockUPICircleProvider(UPICircleProvider):
    """
    Simulated UPI Circle Provider Implementation for Hackathon Prototype.
    Manages in-memory and database delegation state per user ID and routes debits through MockBankAccount.
    """

    def __init__(self):
        self._delegations: Dict[str, Dict[str, Any]] = {}
        self._transactions: Dict[str, Dict[str, Any]] = {}
        self._user_to_delegation: Dict[str, str] = {}
        self._revoked_users: Set[str] = set()
        self._seed_demo_delegation()

    def _seed_demo_delegation(self):
        demo_user = "USER_DEFAULT_001"
        self.create_delegation_sync(
            primary_user_id=demo_user,
            monthly_limit_paise=1500000,
            transaction_limit_paise=500000
        )

    def create_delegation_sync(
        self,
        primary_user_id: str,
        monthly_limit_paise: int = 1500000,
        transaction_limit_paise: int = 500000,
        secondary_profile_id: str = "AI_AGENT_001"
    ) -> Dict[str, Any]:
        if primary_user_id in self._revoked_users:
            self._revoked_users.remove(primary_user_id)

        del_id = f"DEL_{primary_user_id}"
        now = datetime.now(timezone.utc)

        eff_monthly = min(monthly_limit_paise, 1500000)
        eff_per_txn = min(transaction_limit_paise, 500000)

        existing_spend = 0
        if primary_user_id in self._delegations:
            existing_spend = self._delegations[primary_user_id].get("spent_this_month_paise", 0)

        record = {
            "delegation_id": del_id,
            "primary_user_id": primary_user_id,
            "secondary_profile_id": secondary_profile_id,
            "status": "ACTIVE",
            "monthly_limit_paise": eff_monthly,
            "transaction_limit_paise": eff_per_txn,
            "spent_this_month_paise": existing_spend,
            "monthly_limit": eff_monthly / 100.0,
            "transaction_limit": eff_per_txn / 100.0,
            "spent_this_month": existing_spend / 100.0,
            "remaining_this_month": (eff_monthly - existing_spend) / 100.0,
            "currency": "INR",
            "expires_at": (now + timedelta(days=365)).isoformat(),
            "allowed_categories": list(ALLOWED_CATEGORIES),
            "blocked_categories": list(BLOCKED_CATEGORIES),
            "created_at": now.isoformat()
        }

        self._delegations[primary_user_id] = record
        self._delegations[del_id] = record
        self._user_to_delegation[primary_user_id] = del_id
        return record

    async def create_delegation(
        self,
        primary_user_id: str,
        monthly_limit_paise: int = 1500000,
        transaction_limit_paise: int = 500000,
        allowed_categories: Optional[list] = None,
        blocked_categories: Optional[list] = None,
        secondary_profile_id: str = "AI_AGENT_001"
    ) -> Dict[str, Any]:
        return self.create_delegation_sync(
            primary_user_id=primary_user_id,
            monthly_limit_paise=monthly_limit_paise,
            transaction_limit_paise=transaction_limit_paise,
            secondary_profile_id=secondary_profile_id
        )

    async def get_delegation(self, user_id_or_delegation_id: str) -> Optional[Dict[str, Any]]:
        if not user_id_or_delegation_id:
            user_id_or_delegation_id = "USER_DEFAULT_001"

        if user_id_or_delegation_id in self._delegations:
            rec = self._delegations[user_id_or_delegation_id]
            rec["spent_this_month"] = rec["spent_this_month_paise"] / 100.0
            rec["remaining_this_month"] = (rec["monthly_limit_paise"] - rec["spent_this_month_paise"]) / 100.0
            return rec

        del_id = self._user_to_delegation.get(user_id_or_delegation_id)
        if del_id and del_id in self._delegations:
            rec = self._delegations[del_id]
            rec["spent_this_month"] = rec["spent_this_month_paise"] / 100.0
            rec["remaining_this_month"] = (rec["monthly_limit_paise"] - rec["spent_this_month_paise"]) / 100.0
            return rec

        return None

    async def revoke_delegation(self, user_id_or_delegation_id: str) -> bool:
        rec = await self.get_delegation(user_id_or_delegation_id)
        if rec:
            rec["status"] = "INACTIVE"
            user_id = rec["primary_user_id"]
            self._revoked_users.add(user_id)
            if user_id in self._delegations:
                self._delegations[user_id]["status"] = "INACTIVE"
            return True
        return False

    async def validate_delegation(
        self,
        delegation_id: str,
        amount_paise: int,
        category: str
    ) -> Tuple[bool, str]:
        rec = await self.get_delegation(delegation_id)
        if not rec:
            return False, "DELEGATION_NOT_FOUND"

        if rec["status"] != "ACTIVE":
            return False, "DELEGATION_INACTIVE"

        if amount_paise <= 0:
            return False, "INVALID_AMOUNT"

        if amount_paise > rec["transaction_limit_paise"]:
            return False, "TRANSACTION_LIMIT_EXCEEDED"

        remaining_paise = rec["monthly_limit_paise"] - rec["spent_this_month_paise"]
        if amount_paise > remaining_paise:
            return False, "MONTHLY_LIMIT_EXCEEDED"

        cat_upper = category.upper()
        if cat_upper in rec["blocked_categories"]:
            return False, "CATEGORY_BLOCKED"

        return True, "VALIDATED"

    async def initiate_payment(
        self,
        delegation_id: str,
        amount_paise: int,
        merchant_vpa: str,
        category: str,
        transaction_id: str,
        merchant_name: str = "Demo Merchant"
    ) -> Dict[str, Any]:
        rec = await self.get_delegation(delegation_id)
        if not rec:
            return {"status": "FAILED", "reason": "DELEGATION_NOT_FOUND", "transaction_id": transaction_id}

        primary_user_id = rec["primary_user_id"]

        # Debit MockBankAccount
        debit_ok, debit_msg = mock_bank.debit_account(primary_user_id, amount_paise, merchant_vpa)
        if not debit_ok:
            return {
                "transaction_id": transaction_id,
                "delegation_id": rec["delegation_id"],
                "amount_paise": amount_paise,
                "merchant_vpa": merchant_vpa,
                "merchant_name": merchant_name,
                "category": category,
                "status": "FAILED",
                "reason": debit_msg,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }

        # Update spent amount on delegation record
        rec["spent_this_month_paise"] += amount_paise
        rec["spent_this_month"] = rec["spent_this_month_paise"] / 100.0
        rec["remaining_this_month"] = (rec["monthly_limit_paise"] - rec["spent_this_month_paise"]) / 100.0

        if primary_user_id in self._delegations:
            self._delegations[primary_user_id]["spent_this_month_paise"] = rec["spent_this_month_paise"]
            self._delegations[primary_user_id]["spent_this_month"] = rec["spent_this_month"]
            self._delegations[primary_user_id]["remaining_this_month"] = rec["remaining_this_month"]

        record = {
            "transaction_id": transaction_id,
            "delegation_id": rec["delegation_id"],
            "user_id": primary_user_id,
            "amount_paise": amount_paise,
            "amount": amount_paise / 100.0,
            "merchant_vpa": merchant_vpa,
            "merchant": merchant_name,
            "category": category,
            "status": "SUCCESS",
            "reason": "Payment executed successfully under UPI Circle delegation",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        self._transactions[transaction_id] = record
        return record

    async def get_payment_status(self, transaction_id: str) -> Dict[str, Any]:
        return self._transactions.get(transaction_id, {"status": "NOT_FOUND", "transaction_id": transaction_id})

    def reset_provider(self):
        self._delegations.clear()
        self._transactions.clear()
        self._user_to_delegation.clear()
        self._revoked_users.clear()
        self._seed_demo_delegation()


mock_upi_circle_provider = MockUPICircleProvider()
