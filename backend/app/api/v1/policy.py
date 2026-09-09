from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from backend.app.core.database import get_db
from backend.app.models.db_models import PaymentPolicyModel
from backend.app.schemas.intent_schemas import UserPolicySchema

router = APIRouter(prefix="/policy", tags=["Policy Engine"])

@router.get("/{user_id}")
async def get_user_policy(user_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(PaymentPolicyModel).where(PaymentPolicyModel.user_id == user_id))
    policy = result.scalars().first()
    
    if not policy:
        return {
            "user_id": user_id,
            "daily_limit_paise": 500000,
            "transaction_limit_paise": 100000,
            "auto_approval_threshold_paise": 20000,
            "allowed_categories": ["apparel", "electronics", "food", "recharge"],
            "policy_version": 1
        }

    return {
        "user_id": policy.user_id,
        "daily_limit_paise": policy.daily_limit_paise,
        "transaction_limit_paise": policy.transaction_limit_paise,
        "auto_approval_threshold_paise": policy.auto_approval_threshold_paise,
        "allowed_categories": eval(policy.allowed_categories_json),
        "policy_version": policy.policy_version
    }

@router.put("/update")
async def update_user_policy(req: UserPolicySchema, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(PaymentPolicyModel).where(PaymentPolicyModel.user_id == req.user_id))
    policy = result.scalars().first()

    if not policy:
        policy = PaymentPolicyModel(
            policy_id=f"POL_{req.user_id}",
            user_id=req.user_id,
            daily_limit_paise=req.daily_limit_paise,
            transaction_limit_paise=req.transaction_limit_paise,
            auto_approval_threshold_paise=req.auto_approval_threshold_paise,
            allowed_categories_json=str(req.allowed_categories),
            policy_version=1
        )
        db.add(policy)
    else:
        policy.daily_limit_paise = req.daily_limit_paise
        policy.transaction_limit_paise = req.transaction_limit_paise
        policy.auto_approval_threshold_paise = req.auto_approval_threshold_paise
        policy.allowed_categories_json = str(req.allowed_categories)
        policy.policy_version += 1

    await db.commit()
    return {"success": True, "message": "Spending policy updated successfully", "policy_version": policy.policy_version}
