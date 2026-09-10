"""
UPI Circle Payment Decision Engine (PDE) - Core Implementation
Production-ready Zero-Trust Payment Execution Barrier for Agentic Commerce & NPCI UPI Rails
Integrates provider abstraction, transaction splitting detection, risk scoring, and atomic ledger persistence.
"""

import hashlib
import json
import time
import uuid
import asyncio
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, List, Optional, Tuple
from enum import Enum
from pydantic import BaseModel, Field

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from backend.app.models.db_models import (
    UPICircleMandateModel,
    MandateSpendLedgerModel,
    PaymentDecisionModel,
    AuditLogModel
)
from backend.app.payment.mock_bank import mock_bank
from backend.app.payment.merchant_registry import merchant_registry, ALLOWED_CATEGORIES, BLOCKED_CATEGORIES
from backend.app.payment.upi_circle_provider import mock_upi_circle_provider


# =====================================================================
# 1. ENUMS & DATA MODELS
# =====================================================================

class DecisionStatus(str, Enum):
    APPROVED = "APPROVED"
    DENIED = "DENIED"
    REJECTED = "REJECTED"
    REQUIRES_USER_APPROVAL = "REQUIRES_USER_APPROVAL"
    ESCALATED_TO_PIN = "ESCALATED_TO_PIN"
    IN_DOUBT = "IN_DOUBT"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"

# Requirement aliases
DecisionVerdict = DecisionStatus
DecisionVerdict.ESCALATE_TO_PIN = DecisionStatus.REQUIRES_USER_APPROVAL


class MandateState(str, Enum):
    ACTIVE = "ACTIVE"
    PAUSED = "PAUSED"
    REVOKED = "REVOKED"
    EXPIRED = "EXPIRED"


class PaymentIntentRequest(BaseModel):
    user_id: str
    session_id: Optional[str] = "SESSION_DEFAULT"
    mandate_id: Optional[str] = "DEL_001"
    item_id: Optional[str] = "ITEM_DEFAULT"
    item_title: Optional[str] = "Demo Purchase"
    claimed_price_paise: int
    merchant_vpa: str
    merchant_mcc: Optional[str] = "5691"
    merchant: Optional[str] = "Demo Merchant"
    category: Optional[str] = "SHOPPING"
    currency: str = "INR"
    intent: Optional[str] = "PURCHASE"

    @property
    def amount(self) -> float:
        return self.claimed_price_paise / 100.0


class PipelineContext(BaseModel):
    request: PaymentIntentRequest
    idempotency_key: str = ""
    catalog_price_paise: Optional[int] = None
    in_stock: bool = True
    mandate: Optional[Dict[str, Any]] = None
    db_mandate: Optional[Any] = None
    decision: DecisionStatus = DecisionStatus.APPROVED
    reason_code: str = "POLICY_PASS"
    rejection_reason: Optional[str] = None
    step_up_reason: Optional[str] = None
    risk_score: float = 0.10
    risk_level: str = "LOW"
    checks: Dict[str, bool] = Field(default_factory=dict)
    execution_trace: List[Dict[str, Any]] = Field(default_factory=list)
    db_session: Optional[Any] = Field(default=None, exclude=True)

    class Config:
        arbitrary_types_allowed = True


# =====================================================================
# 2. REDIS / IN-MEMORY MOCK STORE FOR DISTRIBUTED LOCKS, VELOCITY & SPLITTING
# =====================================================================

class DistributedStore:
    """
    Production Redis client simulation supporting atomic SETNX, sliding window velocity,
    and transaction splitting history.
    """
    def __init__(self):
        self.locks: Dict[str, float] = {}
        self.velocity_logs: Dict[str, List[float]] = {}
        self.txn_history: Dict[str, List[Dict[str, Any]]] = {}
        self.mandates_db: Dict[str, Dict[str, Any]] = {}
        self.catalog_db: Dict[str, Dict[str, Any]] = {}
        self._seed_default_data()

    def _seed_default_data(self):
        self.mandates_db["MANDATE_UPI_9901"] = {
            "mandate_id": "MANDATE_UPI_9901",
            "primary_user_vpa": "primary@upi",
            "secondary_agent_vpa": "agent.intentguard@psp",
            "per_txn_limit_paise": 500000,
            "monthly_limit_paise": 1500000,
            "current_monthly_spend_paise": 0,
            "state": MandateState.ACTIVE,
            "expiry_date": "2026-12-31T23:59:59Z"
        }

        self.catalog_db["PROD_SHIRT_01"] = {"item_id": "PROD_SHIRT_01", "price_paise": 49900, "in_stock": True, "mcc": "5691"}
        self.catalog_db["PROD_SHOES_01"] = {"item_id": "PROD_SHOES_01", "price_paise": 349500, "in_stock": True, "mcc": "5661"}
        self.catalog_db["PROD_LAPTOP_01"] = {"item_id": "PROD_LAPTOP_01", "price_paise": 450000, "in_stock": True, "mcc": "5732"}
        self.catalog_db["PROD_TEA_01"] = {"item_id": "PROD_TEA_01", "price_paise": 3500, "in_stock": True, "mcc": "5812"}

    async def acquire_lock(self, key: str, ttl_seconds: int = 300) -> bool:
        now = time.time()
        if key in self.locks and self.locks[key] < now:
            del self.locks[key]

        if key in self.locks:
            return False

        self.locks[key] = now + ttl_seconds
        return True

    async def check_sliding_velocity(self, key: str, window_seconds: int = 600, max_allowed: int = 3) -> bool:
        now = time.time()
        cutoff = now - window_seconds
        logs = self.velocity_logs.get(key, [])
        logs = [t for t in logs if t > cutoff]
        self.velocity_logs[key] = logs

        if len(logs) >= max_allowed:
            return False
        return True

    async def record_velocity_event(self, key: str):
        if key not in self.velocity_logs:
            self.velocity_logs[key] = []
        self.velocity_logs[key].append(time.time())

    async def record_transaction_intent(self, user_id: str, req: PaymentIntentRequest):
        now = time.time()
        if user_id not in self.txn_history:
            self.txn_history[user_id] = []
        self.txn_history[user_id].append({
            "timestamp": now,
            "merchant_vpa": req.merchant_vpa,
            "item_title": req.item_title,
            "claimed_price_paise": req.claimed_price_paise,
            "category": req.category
        })

    async def check_transaction_splitting(self, user_id: str, req: PaymentIntentRequest, window_seconds: int = 600) -> bool:
        """
        Detects if user is attempting to split a single transaction over ₹5,000
        into multiple smaller transactions (e.g. two ₹4,000 purchases) within window.
        Returns True if transaction splitting is suspected.
        """
        now = time.time()
        cutoff = now - window_seconds
        history = self.txn_history.get(user_id, [])
        recent = [tx for tx in history if tx["timestamp"] > cutoff]

        if not recent:
            return False

        current_amount = req.claimed_price_paise
        for past_tx in recent:
            past_amount = past_tx["claimed_price_paise"]
            combined = past_amount + current_amount
            # Check if same merchant/product and combined total breaches ₹5,000 per-txn cap
            if combined > 500000:
                if (past_tx["merchant_vpa"] == req.merchant_vpa or 
                    past_tx["category"] == req.category or 
                    past_tx["item_title"].lower() in req.item_title.lower() or 
                    req.item_title.lower() in past_tx["item_title"].lower()):
                    return True
        return False


store = DistributedStore()


# =====================================================================
# 3. PIPELINE FILTERS (CHAIN OF RESPONSIBILITY)
# =====================================================================

class BaseFilter:
    async def process(self, ctx: PipelineContext) -> bool:
        raise NotImplementedError


class IdempotencyFilter(BaseFilter):
    async def process(self, ctx: PipelineContext) -> bool:
        req = ctx.request
        raw_fp = f"{req.user_id}:{req.session_id}:{req.item_id}:{req.claimed_price_paise}"
        ctx.idempotency_key = f"idemp:{hashlib.sha256(raw_fp.encode()).hexdigest()}"

        acquired = await store.acquire_lock(ctx.idempotency_key, ttl_seconds=300)
        ctx.checks["authentication"] = True
        ctx.checks["idempotency_lock"] = acquired

        trace_entry = {
            "filter": "IdempotencyFilter",
            "idempotency_key": ctx.idempotency_key,
            "acquired": acquired,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

        if not acquired:
            ctx.decision = DecisionStatus.DENIED
            ctx.reason_code = "DUPLICATE_TRANSACTION"
            ctx.rejection_reason = f"Duplicate payment request detected (Idempotency Lock Active)"
            ctx.checks["idempotency_pass"] = False
            trace_entry["status"] = "HALTED"
            ctx.execution_trace.append(trace_entry)
            return False

        ctx.checks["idempotency_pass"] = True
        trace_entry["status"] = "PASSED"
        ctx.execution_trace.append(trace_entry)
        return True


class RateAndVelocityFilter(BaseFilter):
    def __init__(self, window_seconds: int = 600, max_purchases: int = 3):
        self.window_seconds = window_seconds
        self.max_purchases = max_purchases

    async def process(self, ctx: PipelineContext) -> bool:
        vel_key = f"vel:{ctx.request.user_id}"
        allowed = await store.check_sliding_velocity(vel_key, self.window_seconds, self.max_purchases)
        ctx.checks["transaction_velocity"] = allowed

        trace_entry = {
            "filter": "RateAndVelocityFilter",
            "velocity_key": vel_key,
            "allowed": allowed,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

        if not allowed:
            ctx.decision = DecisionStatus.REQUIRES_USER_APPROVAL
            ctx.reason_code = "VELOCITY_EXCEEDED"
            ctx.step_up_reason = f"Velocity threshold exceeded (max {self.max_purchases} purchases per {self.window_seconds // 60} minutes)"
            trace_entry["status"] = "ESCALATED"
            ctx.execution_trace.append(trace_entry)
            return False

        trace_entry["status"] = "PASSED"
        ctx.execution_trace.append(trace_entry)
        return True


class TransactionSplittingFilter(BaseFilter):
    """
    Filter 2b: Anti-Transaction Splitting Protection
    Prevents bypassing the ₹5,000 cap by splitting one intended purchase into multiple smaller transactions.
    """
    async def process(self, ctx: PipelineContext) -> bool:
        req = ctx.request
        is_splitting = await store.check_transaction_splitting(req.user_id, req)
        ctx.checks["transaction_splitting_pass"] = not is_splitting

        trace_entry = {
            "filter": "TransactionSplittingFilter",
            "is_splitting_suspected": is_splitting,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

        if is_splitting:
            ctx.decision = DecisionStatus.DENIED
            ctx.reason_code = "POSSIBLE_TRANSACTION_SPLITTING"
            ctx.rejection_reason = "Possible transaction splitting detected: Combined purchases to merchant exceed ₹5,000 per-transaction limit"
            trace_entry["status"] = "HALTED"
            ctx.execution_trace.append(trace_entry)
            return False

        trace_entry["status"] = "PASSED"
        ctx.execution_trace.append(trace_entry)
        return True


class CatalogTruthFilter(BaseFilter):
    async def process(self, ctx: PipelineContext) -> bool:
        item_id = ctx.request.item_id
        catalog_item = store.catalog_db.get(item_id)

        trace_entry = {
            "filter": "CatalogTruthFilter",
            "item_id": item_id,
            "claimed_price_paise": ctx.request.claimed_price_paise,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

        if not catalog_item:
            # If item not in catalog db, verify basic sanity (amount > 0 and currency INR)
            ctx.checks["amount_positive"] = ctx.request.claimed_price_paise > 0
            ctx.checks["currency_inr"] = ctx.request.currency.upper() == "INR"
            trace_entry["status"] = "PASSED_DIRECT"
            ctx.execution_trace.append(trace_entry)
            return True

        ctx.catalog_price_paise = catalog_item["price_paise"]
        ctx.in_stock = catalog_item["in_stock"]
        ctx.checks["catalog_in_stock"] = ctx.in_stock

        if not ctx.in_stock:
            ctx.decision = DecisionStatus.DENIED
            ctx.reason_code = "OUT_OF_STOCK"
            ctx.rejection_reason = f"Item '{item_id}' is currently out of stock"
            trace_entry["status"] = "HALTED"
            ctx.execution_trace.append(trace_entry)
            return False

        # Zero-Tolerance Price Match
        if ctx.request.claimed_price_paise != ctx.catalog_price_paise:
            ctx.decision = DecisionStatus.DENIED
            ctx.reason_code = "PRICE_MISMATCH"
            ctx.rejection_reason = (
                f"AI Hallucination Detected: Claimed price ₹{ctx.request.claimed_price_paise / 100:.2f} "
                f"does not match verified catalog price ₹{ctx.catalog_price_paise / 100:.2f}"
            )
            ctx.checks["price_match"] = False
            trace_entry["status"] = "HALTED"
            ctx.execution_trace.append(trace_entry)
            return False

        ctx.checks["price_match"] = True
        trace_entry["status"] = "PASSED"
        ctx.execution_trace.append(trace_entry)
        return True


class MandatePolicyFilter(BaseFilter):
    """
    Filter 4: NPCI UPI Circle Delegation Policy Checks.
    Evaluates: delegation active, not expired, ₹5,000 per-txn cap, ₹15,000 monthly cap, allowed/blocked categories.
    """
    async def process(self, ctx: PipelineContext) -> bool:
        req = ctx.request
        price_paise = req.claimed_price_paise
        now = datetime.now(timezone.utc)

        # Retrieve delegation strictly for user ID
        user_id = req.user_id or "USER_DEFAULT_001"
        delegation = await mock_upi_circle_provider.get_delegation(user_id)

        db_mandate_active = True
        if ctx.db_session and user_id:
            m_res = await ctx.db_session.execute(
                select(UPICircleMandateModel).where(UPICircleMandateModel.primary_user_id == user_id)
            )
            db_mandate = m_res.scalars().first()
            if db_mandate and db_mandate.mandate_status != "ACTIVE":
                db_mandate_active = False

        if not delegation or delegation.get("status") != "ACTIVE" or not db_mandate_active:
            ctx.decision = DecisionStatus.DENIED
            ctx.reason_code = "DELEGATION_DISCONNECTED"
            ctx.rejection_reason = "Transaction Rejected: UPI Circle delegation is disconnected or inactive. Please connect UPI Circle to proceed with payments."
            ctx.checks["delegation_exists"] = False
            ctx.checks["delegation_active"] = False
            return False

        ctx.mandate = delegation
        ctx.checks["delegation_exists"] = True
        ctx.checks["delegation_active"] = True

        # Check Expiration
        if delegation.get("expires_at"):
            try:
                exp_dt = datetime.fromisoformat(str(delegation["expires_at"]).replace("Z", "+00:00"))
                if exp_dt < now:
                    ctx.decision = DecisionStatus.DENIED
                    ctx.reason_code = "DELEGATION_EXPIRED"
                    ctx.rejection_reason = f"UPI Circle delegation expired on {exp_dt.isoformat()}"
                    ctx.checks["delegation_not_expired"] = False
                    return False
            except Exception:
                pass
        ctx.checks["delegation_not_expired"] = True

        # Amount validation
        if price_paise <= 0:
            ctx.decision = DecisionStatus.DENIED
            ctx.reason_code = "INVALID_AMOUNT"
            ctx.rejection_reason = "Transaction amount must be positive"
            ctx.checks["amount_positive"] = False
            return False
        ctx.checks["amount_positive"] = True

        if req.currency.upper() != "INR":
            ctx.decision = DecisionStatus.DENIED
            ctx.reason_code = "INVALID_CURRENCY"
            ctx.rejection_reason = "Currency must be INR"
            ctx.checks["currency_inr"] = False
            return False
        ctx.checks["currency_inr"] = True

        # Category Allowed / Blocked Check
        cat_upper = (req.category or "SHOPPING").upper()
        blocked_cats = delegation.get("blocked_categories", list(BLOCKED_CATEGORIES))
        allowed_cats = delegation.get("allowed_categories", list(ALLOWED_CATEGORIES))

        if cat_upper in blocked_cats:
            ctx.decision = DecisionStatus.DENIED
            ctx.reason_code = "CATEGORY_BLOCKED"
            ctx.rejection_reason = f"Category '{cat_upper}' is blocked under security policy"
            ctx.checks["category_not_blocked"] = False
            return False
        ctx.checks["category_not_blocked"] = True

        if allowed_cats and cat_upper not in allowed_cats:
            ctx.decision = DecisionStatus.DENIED
            ctx.reason_code = "CATEGORY_NOT_ALLOWED"
            ctx.rejection_reason = f"Category '{cat_upper}' is not in approved category allowlist"
            ctx.checks["category_allowed"] = False
            return False
        ctx.checks["category_allowed"] = True

        # Per-Txn Limit Check (₹5,000 cap)
        per_txn_cap = delegation.get("transaction_limit_paise", 500000)
        if price_paise > per_txn_cap:
            ctx.decision = DecisionStatus.DENIED
            ctx.reason_code = "TRANSACTION_LIMIT_EXCEEDED"
            ctx.rejection_reason = f"Requested amount ₹{price_paise/100:.2f} exceeds delegated transaction limit of ₹{per_txn_cap/100:.2f}"
            ctx.checks["transaction_limit"] = False
            return False
        ctx.checks["transaction_limit"] = True

        # Monthly Spend Limit Check (₹15,000 cap)
        monthly_spend = delegation.get("spent_this_month_paise", 0)
        monthly_cap = delegation.get("monthly_limit_paise", 1500000)

        if (monthly_spend + price_paise) > monthly_cap:
            ctx.decision = DecisionStatus.DENIED
            ctx.reason_code = "MONTHLY_LIMIT_EXCEEDED"
            ctx.rejection_reason = f"Requested amount ₹{price_paise/100:.2f} exceeds remaining monthly limit of ₹{(monthly_cap - monthly_spend)/100:.2f}"
            ctx.checks["monthly_limit"] = False
            return False
        ctx.checks["monthly_limit"] = True

        # Check Mock Bank Sufficient Balance
        user_balance_paise = mock_bank.get_balance_paise(req.user_id)
        if user_balance_paise < price_paise:
            ctx.decision = DecisionStatus.FAILED
            ctx.reason_code = "INSUFFICIENT_FUNDS"
            ctx.rejection_reason = f"Insufficient mock bank balance (Available: ₹{user_balance_paise/100:.2f})"
            ctx.checks["sufficient_balance"] = False
            return False
        ctx.checks["sufficient_balance"] = True

        return True


class MerchantValidationFilter(BaseFilter):
    async def process(self, ctx: PipelineContext) -> bool:
        req = ctx.request
        m_info = merchant_registry.resolve_merchant(req.merchant_vpa or req.merchant, req.category)
        
        ctx.checks["merchant_verified"] = m_info["verified"]
        trace_entry = {
            "filter": "MerchantValidationFilter",
            "merchant_info": m_info,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

        if not m_info["verified"]:
            ctx.decision = DecisionStatus.DENIED
            ctx.reason_code = "UNVERIFIED_MERCHANT"
            ctx.rejection_reason = f"Merchant '{req.merchant}' is not verified in merchant registry"
            trace_entry["status"] = "HALTED"
            ctx.execution_trace.append(trace_entry)
            return False

        trace_entry["status"] = "PASSED"
        ctx.execution_trace.append(trace_entry)
        return True


class RiskModelFilter(BaseFilter):
    """
    Filter 6: Deterministic Risk Scoring Model
    Calculates score: LOW (0.00-0.39), MEDIUM (0.40-0.69), HIGH (0.70-1.00).
    Requires explicit user approval for high-risk purchases (e.g. ₹4,500 electronics).
    """
    async def process(self, ctx: PipelineContext) -> bool:
        req = ctx.request
        price_paise = req.claimed_price_paise
        cat = (req.category or "SHOPPING").upper()

        score = 0.05
        # High value transaction boost
        if price_paise > 400000: # > ₹4,000
            score += 0.40
        elif price_paise > 200000: # > ₹2,000
            score += 0.20

        # Electronics / Shopping category risk boost
        if cat in ["SHOPPING", "ELECTRONICS"]:
            score += 0.25

        ctx.risk_score = round(score, 2)
        if score >= 0.70:
            ctx.risk_level = "HIGH"
        elif score >= 0.40:
            ctx.risk_level = "MEDIUM"
        else:
            ctx.risk_level = "LOW"

        ctx.checks["risk_check"] = True

        if ctx.risk_level == "HIGH" or (ctx.risk_level == "MEDIUM" and price_paise >= 400000):
            ctx.decision = DecisionStatus.REQUIRES_USER_APPROVAL
            ctx.reason_code = "HIGH_RISK_REQUIRES_APPROVAL"
            ctx.step_up_reason = f"High-risk transaction (Score: {ctx.risk_score}, Amount: ₹{price_paise/100:.2f}) requires explicit user approval"
            return False

        return True


# =====================================================================
# 4. PAYMENT DECISION ENGINE COORDINATOR
# =====================================================================

class PaymentDecisionEngine:
    def __init__(self):
        self.pipeline: List[BaseFilter] = [
            IdempotencyFilter(),
            RateAndVelocityFilter(),
            TransactionSplittingFilter(),
            CatalogTruthFilter(),
            MandatePolicyFilter(),
            MerchantValidationFilter(),
            RiskModelFilter()
        ]

    async def evaluate_intent(
        self,
        request: PaymentIntentRequest,
        db: Optional[AsyncSession] = None
    ) -> PipelineContext:
        ctx = PipelineContext(request=request, db_session=db)

        for filter_step in self.pipeline:
            should_continue = await filter_step.process(ctx)
            if not should_continue:
                break

        # Record intent in splitting history
        await store.record_transaction_intent(request.user_id, request)

        return ctx

    async def execute_approved_payment(
        self,
        ctx: PipelineContext,
        transaction_id: Optional[str] = None
    ) -> Dict[str, Any]:
        req = ctx.request
        txn_id = transaction_id or f"TXN_{uuid.uuid4().hex[:8].upper()}"

        if ctx.decision not in [DecisionStatus.APPROVED, DecisionStatus.COMPLETED]:
            return {
                "decision": ctx.decision.value,
                "status": "DENIED",
                "transaction_id": txn_id,
                "reason": ctx.rejection_reason or ctx.step_up_reason or "Payment decision not approved",
                "reason_code": ctx.reason_code
            }

        delegation_id = ctx.mandate.get("delegation_id", "DEL_001") if ctx.mandate else "DEL_001"

        # Route debit strictly via UPICircleProvider interface
        res = await mock_upi_circle_provider.initiate_payment(
            delegation_id=delegation_id,
            amount_paise=req.claimed_price_paise,
            merchant_vpa=req.merchant_vpa,
            category=req.category or "SHOPPING",
            transaction_id=txn_id,
            merchant_name=req.merchant or "Demo Merchant"
        )

        return res


pde_engine = PaymentDecisionEngine()
