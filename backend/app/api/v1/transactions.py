import uuid
import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from backend.app.core.database import get_db
from backend.app.models.db_models import QuoteModel, AuditLogModel, PaymentTokenMetadataModel
from backend.app.schemas.intent_schemas import TransactionExecuteRequest
from backend.app.audit.hash_chain import hash_chain, GENESIS_HASH

router = APIRouter(prefix="/transactions", tags=["Transactions"])

@router.post("/execute")
async def execute_transaction(req: TransactionExecuteRequest, db: AsyncSession = Depends(get_db)):
    # 1. Fetch locked quote (or auto-create quote for direct checkout)
    q_res = await db.execute(select(QuoteModel).where(QuoteModel.quote_id == req.quote_id))
    quote = q_res.scalars().first()

    if not quote:
        now_utc = datetime.datetime.now(datetime.timezone.utc)
        quote = QuoteModel(
            quote_id=req.quote_id,
            user_id=req.user_id,
            merchant_name="Merchant Store",
            product_name="Verified Product Item",
            price_paise=req.amount_paise,
            product_url="https://merchant.store/item",
            expires_at=now_utc + datetime.timedelta(minutes=15)
        )
        db.add(quote)
        await db.commit()

    if quote.expires_at and quote.expires_at.tzinfo is None:
        quote.expires_at = quote.expires_at.replace(tzinfo=datetime.timezone.utc)

    if quote.expires_at and quote.expires_at < datetime.datetime.now(datetime.timezone.utc):
        raise HTTPException(status_code=400, detail="Quote expired. Please request a fresh quote.")

    # 2. Check NPCI UPI Circle Hard Cap (Amounts > ₹15,000 / 1,500,000 paise CANNOT BE EXECUTED)
    if req.amount_paise > 1500000:
        raise HTTPException(
            status_code=400,
            detail=f"Transaction Rejected: Amount ₹{req.amount_paise / 100:,.2f} exceeds NPCI UPI Circle maximum limit of ₹15,000. Autonomous delegation payment cannot be processed."
        )

    # Check NPCI UPI Circle Step-Up Threshold (Amounts > ₹5,000 / 500000 paise REQUIRE UPI PIN Step-Up)
    requires_pin = req.amount_paise > 500000
    if requires_pin and not req.upi_pin:
        raise HTTPException(
            status_code=403,
            detail="Transaction amount exceeds ₹5,000 NPCI PIN-less delegation limit. UPI PIN step-up authorization is required."
        )

    # 3. Fetch User Payment Mandate Token Hash
    tm_res = await db.execute(select(PaymentTokenMetadataModel).where(PaymentTokenMetadataModel.user_id == req.user_id))
    token_meta = tm_res.scalars().first()
    token_hash = token_meta.token_hash_sha256 if token_meta else "TOKEN_HASH_SIMULATED_9921"
    tx_id = f"TXN_{uuid.uuid4().hex[:10].upper()}"

    # Sync with Simulated UPI Circle Provider to update spend counters and debit bank
    from backend.app.payment.upi_circle_provider import mock_upi_circle_provider
    from backend.app.models.db_models import UPICircleMandateModel
    
    delegation = await mock_upi_circle_provider.get_delegation(req.user_id)
    if delegation and delegation.get("status") == "ACTIVE":
        await mock_upi_circle_provider.initiate_payment(
            delegation_id=delegation["delegation_id"],
            amount_paise=req.amount_paise,
            merchant_vpa=req.upi_vpa or "merchant@demo",
            category="SHOPPING",
            transaction_id=tx_id,
            merchant_name=quote.merchant_name or "Merchant Store"
        )

    # Sync with DB UPICircleMandateModel
    m_res = await db.execute(select(UPICircleMandateModel).where(UPICircleMandateModel.primary_user_id == req.user_id))
    db_mandate = m_res.scalars().first()
    if db_mandate:
        db_mandate.current_month_spend_paise = (db_mandate.current_month_spend_paise or 0) + req.amount_paise
        await db.commit()

    # 4. Create Audit Entry for Payment Execution
    last_audit = await db.execute(select(AuditLogModel).order_by(AuditLogModel.id.desc()).limit(1))
    last_row = last_audit.scalars().first()
    prev_hash = last_row.current_hash if last_row else GENESIS_HASH

    status_str = "AUTHORIZED_WITH_UPI_PIN" if requires_pin else "AUTHORIZED_PINLESS_DELEGATION"

    tx_payload = {
        "transaction_id": tx_id,
        "quote_id": req.quote_id,
        "product_name": quote.product_name,
        "amount_paise": req.amount_paise,
        "status": status_str,
        "upi_vpa": req.upi_vpa or "sanjay@upi",
        "step_up_authenticated": requires_pin,
        "razorpay_token_hash": token_hash
    }
    curr_hash = hash_chain.compute_hash(prev_hash, tx_payload)

    audit_entry = AuditLogModel(
        event_id=f"EVT_{uuid.uuid4().hex[:8]}",
        event_type="TRANSACTION_EXECUTED",
        payload_json=str(tx_payload),
        previous_hash=prev_hash,
        current_hash=curr_hash
    )
    db.add(audit_entry)
    await db.commit()

    return {
        "success": True,
        "transactionId": tx_id,
        "status": status_str,
        "amountPaidPaise": req.amount_paise,
        "formattedAmount": f"₹{req.amount_paise / 100:,.2f}",
        "product_name": quote.product_name,
        "merchant": quote.merchant_name,
        "product_url": quote.product_url,
        "upi_vpa": req.upi_vpa or "sanjay@upi",
        "step_up_authenticated": requires_pin,
        "razorpay_token_hash": token_hash,
        "audit_hash": curr_hash,
        "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat()
    }

