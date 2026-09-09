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
    # 1. Fetch locked quote
    q_res = await db.execute(select(QuoteModel).where(QuoteModel.quote_id == req.quote_id))
    quote = q_res.scalars().first()

    if not quote:
        raise HTTPException(status_code=404, detail="Quote lock not found or expired")

    if quote.expires_at < datetime.datetime.utcnow():
        raise HTTPException(status_code=400, detail="Quote expired. Please request a fresh quote.")

    # 2. Fetch User Payment Mandate Token Hash
    t_res = await db.execute(select(PaymentTokenMetadataModel).where(PaymentTokenMetadataModel.user_id == req.user_id))
    token_meta = t_res.scalars().first()

    token_hash = token_meta.token_hash_sha256 if token_meta else "TOKEN_HASH_SIMULATED_9921"
    tx_id = f"TXN_{uuid.uuid4().hex[:10].upper()}"

    # 3. Create Audit Entry for Payment Execution
    last_audit = await db.execute(select(AuditLogModel).order_by(AuditLogModel.id.desc()).limit(1))
    last_row = last_audit.scalars().first()
    prev_hash = last_row.current_hash if last_row else GENESIS_HASH

    tx_payload = {
        "transaction_id": tx_id,
        "quote_id": req.quote_id,
        "product_name": quote.product_name,
        "amount_paise": req.amount_paise,
        "status": "AUTHORIZED_AND_EXECUTED",
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
        "status": "AUTHORIZED_AND_EXECUTED",
        "amountPaidPaise": req.amount_paise,
        "formattedAmount": f"₹{req.amount_paise / 100:,.2f}",
        "product_name": quote.product_name,
        "merchant": quote.merchant_name,
        "product_url": quote.product_url,
        "razorpay_token_hash": token_hash,
        "audit_hash": curr_hash,
        "timestamp": datetime.datetime.utcnow().isoformat()
    }
