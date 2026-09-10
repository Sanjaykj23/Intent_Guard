"""
API Router for Simulated UPI Circle Delegation & Payment Decision Engine
Implements all required REST endpoints for hackathon demo.
"""

from typing import Optional, Dict, Any
import uuid
from fastapi import APIRouter, Depends, HTTPException, Query, Header
from pydantic import BaseModel, Field

from backend.app.payment.upi_circle_provider import mock_upi_circle_provider
from backend.app.payment.mock_bank import mock_bank
from backend.app.payment.merchant_registry import merchant_registry
from backend.app.payment.upi_circle_pde import pde_engine, PaymentIntentRequest, DecisionStatus

router = APIRouter(tags=["Simulated UPI Circle"])

# =====================================================================
# REQUEST & RESPONSE SCHEMAS
# =====================================================================

class CreateDelegationSchema(BaseModel):
    user_id: Optional[str] = "USER_DEFAULT_001"
    monthly_limit: Optional[int] = 15000 # In Rupees
    transaction_limit: Optional[int] = 5000 # In Rupees
    secondary_profile_id: Optional[str] = "AI_AGENT_001"

class PaymentDecisionInputSchema(BaseModel):
    user_id: Optional[str] = "USER_DEFAULT_001"
    amount: float = Field(description="Transaction amount in INR Rupees")
    currency: str = "INR"
    category: str = "GROCERY"
    merchant: Optional[str] = "Demo Grocery Store"
    intent: Optional[str] = "PURCHASE"
    item_title: Optional[str] = None
    item_id: Optional[str] = None

class InitiatePaymentSchema(BaseModel):
    transaction_id: str
    user_id: Optional[str] = "USER_DEFAULT_001"
    action: Optional[str] = "APPROVE" # "APPROVE" or "REJECT"

# =====================================================================
# DELEGATION ENDPOINTS
# =====================================================================

@router.post("/upi-circle/delegation")
@router.post("/v1/upi-circle/delegation")
async def create_delegation(req: CreateDelegationSchema):
    user_id = req.user_id or "USER_DEFAULT_001"
    monthly_paise = int(req.monthly_limit * 100) if req.monthly_limit else 1500000
    txn_paise = int(req.transaction_limit * 100) if req.transaction_limit else 500000

    delegation = await mock_upi_circle_provider.create_delegation(
        primary_user_id=user_id,
        monthly_limit_paise=monthly_paise,
        transaction_limit_paise=txn_paise,
        secondary_profile_id=req.secondary_profile_id or "AI_AGENT_001"
    )

    return {
        "success": True,
        "delegation_id": delegation["delegation_id"],
        "status": delegation["status"],
        "monthly_limit": delegation["monthly_limit"],
        "transaction_limit": delegation["transaction_limit"],
        "spent_this_month": delegation["spent_this_month"],
        "remaining_this_month": delegation["remaining_this_month"],
        "currency": delegation["currency"]
    }

@router.get("/upi-circle/delegation")
@router.get("/v1/upi-circle/delegation")
async def get_delegation(user_id: str = Query("USER_DEFAULT_001")):
    delegation = await mock_upi_circle_provider.get_delegation(user_id)
    if not delegation or delegation.get("status") != "ACTIVE":
        return {
            "has_delegation": False,
            "status": "DISCONNECTED",
            "message": "No active UPI Circle delegation found",
            "monthly_limit": 15000,
            "transaction_limit": 5000,
            "spent_this_month": 0,
            "remaining": 15000
        }
    return {
        "has_delegation": True,
        "delegation_id": delegation["delegation_id"],
        "primary_user_id": delegation["primary_user_id"],
        "secondary_profile_id": delegation["secondary_profile_id"],
        "status": "ACTIVE",
        "monthly_limit": delegation["monthly_limit"],
        "transaction_limit": delegation["transaction_limit"],
        "spent_this_month": delegation["spent_this_month"],
        "remaining": delegation["remaining_this_month"],
        "currency": delegation["currency"],
        "allowed_categories": delegation.get("allowed_categories", []),
        "blocked_categories": delegation.get("blocked_categories", [])
    }

@router.delete("/upi-circle/delegation")
@router.get("/upi-circle/delegation/revoke")
@router.delete("/v1/upi-circle/delegation")
async def revoke_delegation(user_id: str = Query("USER_DEFAULT_001")):
    success = await mock_upi_circle_provider.revoke_delegation(user_id)
    return {
        "success": success,
        "message": "UPI Circle delegation revoked successfully" if success else "Delegation not found"
    }


# =====================================================================
# PAYMENT DECISION ENGINE & INITIATION ENDPOINTS
# =====================================================================

PENDING_DECISIONS: Dict[str, Dict[str, Any]] = {}

@router.post("/payment/decision")
@router.post("/v1/payment/decision")
async def evaluate_payment_decision(req: PaymentDecisionInputSchema):
    user_id = req.user_id or "USER_DEFAULT_001"
    amount_paise = int(round(req.amount * 100))
    
    # Resolve merchant
    m_info = merchant_registry.resolve_merchant(req.merchant or "Demo Merchant", req.category)

    pde_req = PaymentIntentRequest(
        user_id=user_id,
        session_id=str(uuid.uuid4()),
        mandate_id=f"DEL_{user_id}",
        item_id=req.item_id or f"ITEM_{uuid.uuid4().hex[:6]}",
        item_title=req.item_title or f"Purchase at {m_info['name']}",
        claimed_price_paise=amount_paise,
        merchant_vpa=m_info["vpa"],
        merchant_mcc=m_info["mcc"],
        merchant=m_info["name"],
        category=req.category,
        currency=req.currency,
        intent=req.intent
    )

    ctx = await pde_engine.evaluate_intent(pde_req)

    txn_id = f"TXN_{uuid.uuid4().hex[:8].upper()}"

    decision_val = ctx.decision.value if hasattr(ctx.decision, "value") else str(ctx.decision)
    
    # Map decision value to standard 3 states: APPROVED, DENIED, REQUIRES_USER_APPROVAL
    if decision_val in ["APPROVED"]:
        final_decision = "APPROVED"
    elif decision_val in ["REQUIRES_USER_APPROVAL", "ESCALATED_TO_PIN"]:
        final_decision = "REQUIRES_USER_APPROVAL"
    else:
        final_decision = "DENIED"

    # Store pending decision for accurate payment initiation
    PENDING_DECISIONS[txn_id] = {
        "user_id": user_id,
        "amount_paise": amount_paise,
        "amount": req.amount,
        "category": req.category,
        "merchant": m_info["name"],
        "merchant_vpa": m_info["vpa"]
    }

    resp = {
        "decision": final_decision,
        "transaction_id": txn_id,
        "user_id": user_id,
        "amount": req.amount,
        "currency": req.currency,
        "category": req.category,
        "merchant": m_info["name"],
        "merchant_vpa": m_info["vpa"],
        "reason": ctx.rejection_reason or ctx.step_up_reason or "Payment satisfies delegated payment policy",
        "reason_code": ctx.reason_code,
        "risk_score": ctx.risk_score,
        "risk_level": ctx.risk_level,
        "checks": ctx.checks
    }

    if final_decision == "DENIED":
        resp["requested_amount"] = req.amount
        resp["allowed_amount"] = 5000.0

    return resp


@router.post("/payment/initiate")
@router.post("/v1/payment/initiate")
async def initiate_payment(req: InitiatePaymentSchema):
    user_id = req.user_id or "USER_DEFAULT_001"
    
    if req.action == "REJECT":
        PENDING_DECISIONS.pop(req.transaction_id, None)
        return {
            "status": "CANCELLED",
            "transaction_id": req.transaction_id,
            "message": "Payment rejected by user"
        }

    pending = PENDING_DECISIONS.pop(req.transaction_id, None)
    if pending:
        user_id = pending.get("user_id", user_id)
        amount_paise = pending.get("amount_paise", 35000)
        merchant_vpa = pending.get("merchant_vpa", "merchant@demo")
        category = pending.get("category", "SHOPPING")
        merchant_name = pending.get("merchant", "Demo Merchant")
    else:
        amount_paise = 35000
        merchant_vpa = "merchant@demo"
        category = "SHOPPING"
        merchant_name = "Demo Merchant"

    # Execute payment via mock provider
    delegation = await mock_upi_circle_provider.get_delegation(user_id)
    if not delegation:
        raise HTTPException(status_code=400, detail="No active UPI Circle delegation found")

    res = await mock_upi_circle_provider.initiate_payment(
        delegation_id=delegation["delegation_id"],
        amount_paise=amount_paise,
        merchant_vpa=merchant_vpa,
        category=category,
        transaction_id=req.transaction_id,
        merchant_name=merchant_name
    )

    return res


@router.get("/payment/history")
@router.get("/v1/payment/history")
async def get_payment_history(user_id: str = Query("USER_DEFAULT_001")):
    txns = list(mock_upi_circle_provider._transactions.values())
    return {
        "success": True,
        "count": len(txns),
        "transactions": txns
    }


@router.get("/payment/{transaction_id}")
@router.get("/v1/payment/{transaction_id}")
async def get_payment_status(transaction_id: str):
    res = await mock_upi_circle_provider.get_payment_status(transaction_id)
    return res


@router.get("/wallet/balance")
@router.get("/v1/wallet/balance")
async def get_wallet_balance(user_id: str = Query("USER_DEFAULT_001")):
    acc = mock_bank.get_account(user_id)
    return {
        "success": True,
        "user_id": user_id,
        "bank_name": acc["bank_name"],
        "account_reference": acc["account_reference"],
        "balance": acc["balance_rupees"],
        "balance_paise": acc["balance_paise"],
        "currency": acc["currency"]
    }


# =====================================================================
# HACKATHON DEMO RESET ENDPOINT
# =====================================================================

@router.post("/demo/reset")
@router.post("/v1/demo/reset")
async def reset_demo_data(user_id: str = Query("USER_DEFAULT_001")):
    """
    Hackathon Demo Development-Only Reset Endpoint.
    Resets bank balance to ₹25,000, monthly spending to ₹0, and delegation status to ACTIVE.
    """
    mock_bank.reset_account(user_id, balance_paise=2500000) # Reset to ₹25,000
    mock_upi_circle_provider.reset_provider()
    
    return {
        "success": True,
        "message": "Demo data reset successfully!",
        "mock_bank_balance": 25000.0,
        "monthly_limit": 15000.0,
        "spent_this_month": 0.0,
        "delegation_status": "ACTIVE"
    }
