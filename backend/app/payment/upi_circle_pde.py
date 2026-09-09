"""
UPI Circle Payment Decision Engine (PDE) - Core Implementation
Production-ready Zero-Trust Payment Execution Barrier for Agentic Commerce & NPCI UPI Rails
Directly integrated with SQLAlchemy AsyncSession and PostgreSQL ORM Models.
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


# =====================================================================
# 1. ENUMS & DATA MODELS
# =====================================================================

class DecisionStatus(str, Enum):
    APPROVED = "APPROVED"
    ESCALATED_TO_PIN = "ESCALATED_TO_PIN"
    REJECTED = "REJECTED"
    IN_DOUBT = "IN_DOUBT"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"

# Requirement alias
DecisionVerdict = DecisionStatus
DecisionVerdict.ESCALATE_TO_PIN = DecisionStatus.ESCALATED_TO_PIN



class MandateState(str, Enum):
    ACTIVE = "ACTIVE"
    PAUSED = "PAUSED"
    REVOKED = "REVOKED"
    EXPIRED = "EXPIRED"


class PaymentIntentRequest(BaseModel):
    user_id: str
    session_id: str
    mandate_id: str
    item_id: str
    item_title: str
    claimed_price_paise: int
    merchant_vpa: str
    merchant_mcc: str
    currency: str = "INR"


class PipelineContext(BaseModel):
    request: PaymentIntentRequest
    idempotency_key: str
    catalog_price_paise: Optional[int] = None
    in_stock: bool = False
    mandate: Optional[Dict[str, Any]] = None
    db_mandate: Optional[Any] = None
    decision: DecisionStatus = DecisionStatus.APPROVED
    rejection_reason: Optional[str] = None
    step_up_reason: Optional[str] = None
    execution_trace: List[Dict[str, Any]] = Field(default_factory=list)
    db_session: Optional[Any] = Field(default=None, exclude=True)

    class Config:
        arbitrary_types_allowed = True


# =====================================================================
# 2. REDIS / IN-MEMORY MOCK STORE FOR DISTRIBUTED LOCKS & VELOCITY
# =====================================================================

class DistributedStore:
    """
    Production Redis client wrapper simulation supporting atomic SETNX, TTLs,
    and sliding-window velocity logs.
    """
    def __init__(self):
        self.locks: Dict[str, float] = {}
        self.velocity_logs: Dict[str, List[float]] = {}
        self.mandates_db: Dict[str, Dict[str, Any]] = {}
        self.catalog_db: Dict[str, Dict[str, Any]] = {}
        self._seed_default_data()

    def _seed_default_data(self):
        # Default UPI Circle mandate (Secondary user delegation)
        self.mandates_db["MANDATE_UPI_9901"] = {
            "mandate_id": "MANDATE_UPI_9901",
            "primary_user_vpa": "primary@upi",
            "secondary_agent_vpa": "agent.intentguard@psp",
            "per_txn_limit_paise": 500000,      # ₹5,000 (NPCI limit for full delegation)
            "monthly_limit_paise": 1500000,    # ₹15,000 (NPCI monthly cumulative cap)
            "current_monthly_spend_paise": 250000, # ₹2,500 spent so far
            "state": MandateState.ACTIVE,
            "expiry_date": "2026-12-31T23:59:59Z"
        }
        
        # Product catalog truth source
        self.catalog_db["PROD_SHIRT_01"] = {"item_id": "PROD_SHIRT_01", "price_paise": 49900, "in_stock": True, "mcc": "5691"}
        self.catalog_db["PROD_SHOES_01"] = {"item_id": "PROD_SHOES_01", "price_paise": 349500, "in_stock": True, "mcc": "5661"}
        self.catalog_db["PROD_LAPTOP_01"] = {"item_id": "PROD_LAPTOP_01", "price_paise": 5299000, "in_stock": True, "mcc": "5732"}
        self.catalog_db["PROD_TEA_01"] = {"item_id": "PROD_TEA_01", "price_paise": 3500, "in_stock": True, "mcc": "5812"}

    async def acquire_lock(self, key: str, ttl_seconds: int = 300) -> bool:
        now = time.time()
        if key in self.locks and self.locks[key] < now:
            del self.locks[key]

        if key in self.locks:
            return False  # Lock already held

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


store = DistributedStore()


# =====================================================================
# 3. PIPELINE FILTERS (CHAIN OF RESPONSIBILITY)
# =====================================================================

class BaseFilter:
    async def process(self, ctx: PipelineContext) -> bool:
        raise NotImplementedError


class IdempotencyFilter(BaseFilter):
    """
    Filter 1: Replay Attack Protection & Idempotency Key Lock.
    """
    async def process(self, ctx: PipelineContext) -> bool:
        req = ctx.request
        raw_fingerprint = f"{req.user_id}:{req.session_id}:{req.item_id}:{req.claimed_price_paise}"
        ctx.idempotency_key = f"idemp:{hashlib.sha256(raw_fingerprint.encode()).hexdigest()}"

        acquired = await store.acquire_lock(ctx.idempotency_key, ttl_seconds=300)
        trace_entry = {
            "filter": "IdempotencyFilter",
            "idempotency_key": ctx.idempotency_key,
            "acquired": acquired,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

        if not acquired:
            ctx.decision = DecisionStatus.REJECTED
            ctx.rejection_reason = f"Duplicate payment request detected (Idempotency Lock Active: {ctx.idempotency_key})"
            trace_entry["status"] = "HALTED"
            ctx.execution_trace.append(trace_entry)
            return False

        trace_entry["status"] = "PASSED"
        ctx.execution_trace.append(trace_entry)
        return True


class RateAndVelocityFilter(BaseFilter):
    """
    Filter 2: Sliding Window Velocity Limiter (Max 3 auto-purchases per 10 mins).
    """
    def __init__(self, window_seconds: int = 600, max_purchases: int = 3):
        self.window_seconds = window_seconds
        self.max_purchases = max_purchases

    async def process(self, ctx: PipelineContext) -> bool:
        vel_key = f"vel:{ctx.request.user_id}"
        allowed = await store.check_sliding_velocity(vel_key, self.window_seconds, self.max_purchases)

        trace_entry = {
            "filter": "RateAndVelocityFilter",
            "velocity_key": vel_key,
            "allowed": allowed,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

        if not allowed:
            ctx.decision = DecisionStatus.ESCALATED_TO_PIN
            ctx.step_up_reason = f"Velocity threshold exceeded (max {self.max_purchases} auto-purchases per {self.window_seconds // 60} minutes)"
            trace_entry["status"] = "ESCALATED"
            ctx.execution_trace.append(trace_entry)
            return False

        trace_entry["status"] = "PASSED"
        ctx.execution_trace.append(trace_entry)
        return True


class CatalogTruthFilter(BaseFilter):
    """
    Filter 3: Anti-Hallucination Catalog Verification.
    """
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
            ctx.decision = DecisionStatus.REJECTED
            ctx.rejection_reason = f"Item '{item_id}' not found in verified catalog"
            trace_entry["status"] = "HALTED"
            ctx.execution_trace.append(trace_entry)
            return False

        ctx.catalog_price_paise = catalog_item["price_paise"]
        ctx.in_stock = catalog_item["in_stock"]
        trace_entry["catalog_price_paise"] = ctx.catalog_price_paise
        trace_entry["in_stock"] = ctx.in_stock

        if not ctx.in_stock:
            ctx.decision = DecisionStatus.REJECTED
            ctx.rejection_reason = f"Item '{item_id}' is currently out of stock"
            trace_entry["status"] = "HALTED"
            ctx.execution_trace.append(trace_entry)
            return False

        # Zero-Tolerance Price Match
        if ctx.request.claimed_price_paise != ctx.catalog_price_paise:
            ctx.decision = DecisionStatus.REJECTED
            ctx.rejection_reason = (
                f"AI Hallucination Detected: Claimed price ₹{ctx.request.claimed_price_paise / 100:.2f} "
                f"does not match verified catalog price ₹{ctx.catalog_price_paise / 100:.2f}"
            )
            trace_entry["status"] = "HALTED"
            ctx.execution_trace.append(trace_entry)
            return False

        trace_entry["status"] = "PASSED"
        ctx.execution_trace.append(trace_entry)
        return True


class MandatePolicyFilter(BaseFilter):
    """
    Filter 4: NPCI UPI Circle Mandate & Spend Policy Evaluation.
    Queries SQLAlchemy AsyncSession (UPICircleMandateModel) or in-memory fallback.
    Enforces ACTIVE state, expiry timestamp, 24h cooling off, ₹5,000 per-txn cap, and ₹15,000 monthly cumulative spend cap.
    """
    async def process(self, ctx: PipelineContext) -> bool:
        mandate_id = ctx.request.mandate_id
        req = ctx.request
        price_paise = req.claimed_price_paise
        now = datetime.now(timezone.utc)

        trace_entry = {
            "filter": "MandatePolicyFilter",
            "mandate_id": mandate_id,
            "timestamp": now.isoformat()
        }

        # 1. Query via SQLAlchemy AsyncSession if present
        if ctx.db_session:
            try:
                res = await ctx.db_session.execute(
                    select(UPICircleMandateModel).where(
                        (UPICircleMandateModel.mandate_id == mandate_id) |
                        (UPICircleMandateModel.primary_user_id == req.user_id)
                    )
                )
                db_mandate = res.scalars().first()
                if db_mandate:
                    ctx.db_mandate = db_mandate

                    # Check mandate state (must be ACTIVE)
                    mandate_status = db_mandate.mandate_status or db_mandate.mandate_state
                    if mandate_status != "ACTIVE":
                        ctx.decision = DecisionStatus.REJECTED
                        ctx.rejection_reason = f"UPI Circle Mandate '{mandate_id}' status is '{mandate_status}' (must be ACTIVE)"
                        trace_entry["status"] = "HALTED"
                        ctx.execution_trace.append(trace_entry)
                        return False

                    # Check expiry timestamp (valid_until)
                    if db_mandate.valid_until:
                        valid_until = db_mandate.valid_until
                        if valid_until.tzinfo is None:
                            valid_until = valid_until.replace(tzinfo=timezone.utc)
                        if valid_until < now:
                            ctx.decision = DecisionStatus.REJECTED
                            ctx.rejection_reason = f"UPI Circle Mandate '{mandate_id}' has expired on {valid_until.isoformat()}"
                            trace_entry["status"] = "HALTED"
                            ctx.execution_trace.append(trace_entry)
                            return False

                    # Check NPCI 24-hour cooling-off window (cooling_off_until)
                    if db_mandate.cooling_off_until:
                        cooling_until = db_mandate.cooling_off_until
                        if cooling_until.tzinfo is None:
                            cooling_until = cooling_until.replace(tzinfo=timezone.utc)
                        if cooling_until > now:
                            if price_paise > 200000 or ((db_mandate.current_month_spend_paise or 0) + price_paise) > 200000:
                                ctx.decision = DecisionVerdict.ESCALATE_TO_PIN
                                ctx.step_up_reason = f"Transaction exceeds NPCI 24-hour cooling-off autonomous limit of ₹2,000 (until {cooling_until.isoformat()}). Step-up UPI PIN authorization required."
                                trace_entry["status"] = "ESCALATED"
                                ctx.execution_trace.append(trace_entry)
                                return False

                    monthly_spend = db_mandate.current_month_spend_paise or 0
                    monthly_cap = db_mandate.monthly_limit_paise or 1500000
                    per_txn_cap = db_mandate.per_txn_limit_paise or 500000
                    npci_hard_cap = 500000  # ₹5,000 NPCI hard cap in paise

                    # Monthly Limit Check
                    if (monthly_spend + price_paise) > monthly_cap:
                        ctx.decision = DecisionStatus.REJECTED
                        ctx.rejection_reason = f"Monthly cumulative spend quota breached. Attempted: ₹{(monthly_spend + price_paise)/100:.2f}, Cap: ₹{monthly_cap/100:.2f}"
                        trace_entry["status"] = "HALTED"
                        ctx.execution_trace.append(trace_entry)
                        return False

                    # Per-Txn Limit Check & ₹5,000 NPCI hard cap -> Escalate to PIN
                    effective_per_txn_cap = min(per_txn_cap, npci_hard_cap)
                    if price_paise > effective_per_txn_cap:
                        ctx.decision = DecisionVerdict.ESCALATE_TO_PIN
                        ctx.step_up_reason = (
                            f"Transaction amount ₹{price_paise / 100:.2f} exceeds NPCI UPI Circle "
                            f"autonomous limit of ₹{effective_per_txn_cap / 100:.2f}. Step-up UPI PIN authorization required."
                        )
                        trace_entry["status"] = "ESCALATED"
                        ctx.execution_trace.append(trace_entry)
                        return False

                    trace_entry["status"] = "PASSED"
                    ctx.execution_trace.append(trace_entry)
                    return True
            except Exception as e:
                print(f"[MandatePolicyFilter AsyncSession Note]: {e}")

        # 2. In-Memory Store Fallback (for unit testing)
        mandate = store.mandates_db.get(mandate_id)
        if not mandate or mandate.get("state") != MandateState.ACTIVE:
            ctx.decision = DecisionStatus.REJECTED
            ctx.rejection_reason = f"UPI Circle Mandate '{mandate_id}' is invalid or revoked"
            trace_entry["status"] = "HALTED"
            ctx.execution_trace.append(trace_entry)
            return False

        ctx.mandate = mandate

        # Check in-memory expiry
        if mandate.get("expiry_date"):
            try:
                exp_str = str(mandate["expiry_date"]).replace("Z", "+00:00")
                exp_dt = datetime.fromisoformat(exp_str)
                if exp_dt.tzinfo is None:
                    exp_dt = exp_dt.replace(tzinfo=timezone.utc)
                if exp_dt < now:
                    ctx.decision = DecisionStatus.REJECTED
                    ctx.rejection_reason = f"UPI Circle Mandate '{mandate_id}' has expired"
                    trace_entry["status"] = "HALTED"
                    ctx.execution_trace.append(trace_entry)
                    return False
            except Exception:
                pass

        # Check in-memory cooling-off window
        if mandate.get("cooling_off_until"):
            try:
                cool_str = str(mandate["cooling_off_until"]).replace("Z", "+00:00")
                cool_dt = datetime.fromisoformat(cool_str)
                if cool_dt.tzinfo is None:
                    cool_dt = cool_dt.replace(tzinfo=timezone.utc)
                if cool_dt > now:
                    m_spend = mandate.get("current_monthly_spend_paise", 0)
                    if price_paise > 200000 or (m_spend + price_paise) > 200000:
                        ctx.decision = DecisionVerdict.ESCALATE_TO_PIN
                        ctx.step_up_reason = f"Transaction exceeds NPCI 24-hour cooling-off limit of ₹2,000 (until {cool_dt.isoformat()}). Step-up UPI PIN authorization required."
                        trace_entry["status"] = "ESCALATED"
                        ctx.execution_trace.append(trace_entry)
                        return False
            except Exception:
                pass

        monthly_spend = mandate.get("current_monthly_spend_paise", 0)
        monthly_cap = mandate.get("monthly_limit_paise", 1500000)
        per_txn_cap = mandate.get("per_txn_limit_paise", 500000)
        npci_hard_cap = 500000

        if (monthly_spend + price_paise) > monthly_cap:
            ctx.decision = DecisionStatus.REJECTED
            ctx.rejection_reason = f"Monthly cumulative spend quota breached. Attempted total: ₹{(monthly_spend + price_paise) / 100:.2f}, Limit: ₹{monthly_cap / 100:.2f}"
            trace_entry["status"] = "HALTED"
            ctx.execution_trace.append(trace_entry)
            return False

        effective_per_txn_cap = min(per_txn_cap, npci_hard_cap)
        if price_paise > effective_per_txn_cap:
            ctx.decision = DecisionVerdict.ESCALATE_TO_PIN
            ctx.step_up_reason = f"Transaction amount ₹{price_paise / 100:.2f} exceeds NPCI UPI Circle autonomous full delegation limit of ₹{effective_per_txn_cap / 100:.2f}. Step-up UPI PIN authorization required."
            trace_entry["status"] = "ESCALATED"
            ctx.execution_trace.append(trace_entry)
            return False

        trace_entry["status"] = "PASSED"
        ctx.execution_trace.append(trace_entry)
        return True


class MerchantMCCAllowlistFilter(BaseFilter):
    """
    Filter 5: Destination Merchant VPA & Category Code (MCC) Allowlist Validation.
    """
    ALLOWED_MCCS = {"5691", "5661", "5812", "5411", "5732", "4814"}
    ALLOWED_VPA_DOMAINS = {"@amazon", "@flipkart", "@myntra", "@swiggy", "@zomato", "@jio", "@upi"}

    async def process(self, ctx: PipelineContext) -> bool:
        req = ctx.request
        vpa_domain = "@" + req.merchant_vpa.split("@")[-1] if "@" in req.merchant_vpa else ""

        trace_entry = {
            "filter": "MerchantMCCAllowlistFilter",
            "merchant_vpa": req.merchant_vpa,
            "merchant_mcc": req.merchant_mcc,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

        if req.merchant_mcc not in self.ALLOWED_MCCS:
            ctx.decision = DecisionStatus.REJECTED
            ctx.rejection_reason = f"Merchant MCC '{req.merchant_mcc}' is not on the allowed payment category list"
            trace_entry["status"] = "HALTED"
            ctx.execution_trace.append(trace_entry)
            return False

        if vpa_domain not in self.ALLOWED_VPA_DOMAINS:
            ctx.decision = DecisionStatus.REJECTED
            ctx.rejection_reason = f"Merchant VPA domain '{vpa_domain}' is not in verified PSP merchant registry"
            trace_entry["status"] = "HALTED"
            ctx.execution_trace.append(trace_entry)
            return False

        trace_entry["status"] = "PASSED"
        ctx.execution_trace.append(trace_entry)
        return True


# =====================================================================
# 4. PAYMENT DECISION ENGINE COORDINATOR & ATOMIC PERSISTENCE
# =====================================================================

class PaymentDecisionEngine:
    def __init__(self):
        self.pipeline: List[BaseFilter] = [
            IdempotencyFilter(),
            RateAndVelocityFilter(),
            CatalogTruthFilter(),
            MandatePolicyFilter(),
            MerchantMCCAllowlistFilter()
        ]

    async def evaluate_intent(
        self,
        request: PaymentIntentRequest,
        db: Optional[AsyncSession] = None
    ) -> PipelineContext:
        ctx = PipelineContext(request=request, idempotency_key="", db_session=db)

        for filter_step in self.pipeline:
            should_continue = await filter_step.process(ctx)
            if not should_continue:
                break

        if db:
            await self.persist_decision(ctx)

        return ctx

    async def persist_decision(self, ctx: PipelineContext) -> Optional[PaymentDecisionModel]:
        """
        Persists a record to PaymentDecisionModel directly via SQLAlchemy AsyncSession.
        Executes safe transaction rollback on error.
        """
        if not ctx.db_session:
            return None

        db: AsyncSession = ctx.db_session
        try:
            req = ctx.request
            decision_record = PaymentDecisionModel(
                decision_id=f"DECISION_{uuid.uuid4().hex[:12].upper()}",
                user_id=req.user_id,
                mandate_id=req.mandate_id,
                session_id=req.session_id,
                idempotency_key=ctx.idempotency_key or f"idemp:{uuid.uuid4().hex}",
                item_id=req.item_id,
                item_title=req.item_title,
                claimed_price_paise=req.claimed_price_paise,
                merchant_vpa=req.merchant_vpa,
                merchant_mcc=req.merchant_mcc,
                decision=ctx.decision.value if hasattr(ctx.decision, "value") else str(ctx.decision),
                rejection_reason=ctx.rejection_reason,
                step_up_reason=ctx.step_up_reason,
                execution_trace_json=json.dumps(ctx.execution_trace),
                created_at=datetime.now(timezone.utc)
            )
            db.add(decision_record)
            await db.commit()
            return decision_record
        except Exception as e:
            if ctx.db_session:
                await ctx.db_session.rollback()
            print(f"[PDE Decision Persistence Error]: {e}")
            raise e

    async def execute_and_persist_ledger(
        self,
        ctx: PipelineContext,
        transaction_id: str,
        status_str: str = "COMPLETED"
    ):
        """
        Atomic persistence:
        - When a transaction is APPROVED, writes PaymentDecisionModel record.
        - Updates current_monthly_spend_paise on UPICircleMandateModel.
        - Inserts entry into MandateSpendLedgerModel.
        All inside a single atomic database transaction with safe rollback on error.
        """
        if not ctx.db_session:
            return

        db: AsyncSession = ctx.db_session
        try:
            req = ctx.request
            price_paise = req.claimed_price_paise

            # Write PaymentDecisionModel record for APPROVED state
            decision_record = PaymentDecisionModel(
                decision_id=f"DECISION_{uuid.uuid4().hex[:12].upper()}",
                user_id=req.user_id,
                mandate_id=req.mandate_id,
                session_id=req.session_id,
                idempotency_key=ctx.idempotency_key or f"idemp:{uuid.uuid4().hex}",
                item_id=req.item_id,
                item_title=req.item_title,
                claimed_price_paise=price_paise,
                merchant_vpa=req.merchant_vpa,
                merchant_mcc=req.merchant_mcc,
                decision=ctx.decision.value if hasattr(ctx.decision, "value") else str(ctx.decision),
                rejection_reason=ctx.rejection_reason,
                step_up_reason=ctx.step_up_reason,
                execution_trace_json=json.dumps(ctx.execution_trace),
                created_at=datetime.now(timezone.utc)
            )
            db.add(decision_record)

            if ctx.decision == DecisionStatus.APPROVED and ctx.db_mandate:
                mandate = ctx.db_mandate
                prev_spend = mandate.current_month_spend_paise or 0
                mandate.current_month_spend_paise = prev_spend + price_paise
                new_spend = mandate.current_month_spend_paise

                ledger_entry = MandateSpendLedgerModel(
                    ledger_id=f"LEDGER_{uuid.uuid4().hex[:12].upper()}",
                    mandate_id=mandate.mandate_id,
                    transaction_id=transaction_id,
                    amount_paise=price_paise,
                    entry_type="DEBIT",
                    merchant_vpa=req.merchant_vpa,
                    merchant_mcc=req.merchant_mcc,
                    previous_month_spend_paise=prev_spend,
                    new_month_spend_paise=new_spend,
                    created_at=datetime.now(timezone.utc)
                )
                db.add(ledger_entry)

            # Single atomic commit for database transaction
            await db.commit()
        except Exception as e:
            if ctx.db_session:
                await ctx.db_session.rollback()
            print(f"[PDE Atomic Persistence Error]: {e}")
            raise e



# =====================================================================
# 5. BANKING PSP CLIENT & TIMEOUT RECOVERY
# =====================================================================

class UPICirclePSPClient:
    """
    Secondary User Autonomous Execution Interface with banking PSP rails.
    """
    def __init__(self, simulate_timeout: bool = False):
        self.simulate_timeout = simulate_timeout
        self.ledger: Dict[str, Dict[str, Any]] = {}

    async def execute_autonomous_debit(
        self,
        mandate_id: str,
        amount_paise: int,
        target_vpa: str,
        idempotency_key: str
    ) -> Tuple[DecisionStatus, str, Optional[str]]:
        txn_id = f"UPI_CIRC_{uuid.uuid4().hex[:12].upper()}"

        if self.simulate_timeout:
            self.ledger[txn_id] = {
                "txn_id": txn_id,
                "mandate_id": mandate_id,
                "amount_paise": amount_paise,
                "target_vpa": target_vpa,
                "idempotency_key": idempotency_key,
                "status": DecisionStatus.IN_DOUBT,
                "created_at": time.time()
            }
            return DecisionStatus.IN_DOUBT, txn_id, "PSP Gateway Connection Timeout (Transaction Pending Verification)"

        self.ledger[txn_id] = {
            "txn_id": txn_id,
            "mandate_id": mandate_id,
            "amount_paise": amount_paise,
            "target_vpa": target_vpa,
            "idempotency_key": idempotency_key,
            "status": DecisionStatus.COMPLETED,
            "created_at": time.time()
        }

        mandate = store.mandates_db.get(mandate_id)
        if mandate:
            mandate["current_monthly_spend_paise"] += amount_paise

        user_id = mandate_id.replace("MANDATE_", "") if mandate else "USER"
        await store.record_velocity_event(f"vel:{user_id}")

        return DecisionStatus.COMPLETED, txn_id, None


pde_engine = PaymentDecisionEngine()
psp_client = UPICirclePSPClient()
