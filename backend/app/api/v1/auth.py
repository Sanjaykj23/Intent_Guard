import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from backend.app.core.database import get_db
from backend.app.models.db_models import UserModel, PaymentPolicyModel, PaymentTokenMetadataModel
from backend.app.schemas.intent_schemas import UserRegistration
from backend.app.payment.razorpay_vault import razorpay_vault

router = APIRouter(prefix="/auth", tags=["Auth"])

@router.post("/register")
async def register_user(req: UserRegistration, db: AsyncSession = Depends(get_db)):
    # Check existing
    result = await db.execute(select(UserModel).where(UserModel.email == req.email))
    if result.scalars().first():
        raise HTTPException(status_code=400, detail="Email already registered")

    user_id = f"USER_{uuid.uuid4().hex[:8]}"
    new_user = UserModel(
        id=user_id,
        name=req.name,
        email=req.email,
        password_hash=req.password # In production, bcrypt/argon2
    )
    db.add(new_user)

    # Create Default IntentGuard Policy
    policy = PaymentPolicyModel(
        policy_id=f"POL_{uuid.uuid4().hex[:8]}",
        user_id=user_id,
        daily_limit_paise=500000, # ₹5,000
        transaction_limit_paise=100000, # ₹1,000
        auto_approval_threshold_paise=20000, # ₹200
        allowed_categories_json='["apparel", "electronics", "food", "recharge"]'
    )
    db.add(policy)

    # Store Razorpay Token Hash in Payment Vault
    mandate_data = razorpay_vault.generate_mock_mandate(req.email)
    token_meta = PaymentTokenMetadataModel(
        id=f"TOK_{uuid.uuid4().hex[:8]}",
        user_id=user_id,
        razorpay_customer_id=mandate_data["razorpay_customer_id"],
        razorpay_mandate_token_ref=mandate_data["razorpay_mandate_token_ref"],
        token_hash_sha256=mandate_data["token_hash_sha256"],
        status="ACTIVE"
    )
    db.add(token_meta)

    await db.commit()

    return {
        "success": True,
        "message": "User registered and Razorpay mandate token hashed successfully",
        "user_id": user_id,
        "name": req.name,
        "email": req.email,
        "razorpay_token_hash": mandate_data["token_hash_sha256"]
    }

@router.post("/login")
async def login_user(email: str, password: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(UserModel).where(UserModel.email == email))
    user = result.scalars().first()

    if not user or user.password_hash != password:
        raise HTTPException(status_code=401, detail="Invalid email or password")

    return {
        "success": True,
        "user_id": user.id,
        "name": user.name,
        "email": user.email,
        "token": f"TOKEN_{uuid.uuid4().hex[:16]}"
    }
