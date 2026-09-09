from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from backend.app.core.database import get_db
from backend.app.models.db_models import AuditLogModel

router = APIRouter(prefix="/audit", tags=["Audit Ledger"])

@router.get("/logs")
async def get_audit_ledger_logs(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(AuditLogModel).order_by(AuditLogModel.id.asc()))
    logs = result.scalars().all()

    items = []
    for log in logs:
        items.append({
            "id": log.id,
            "event_id": log.event_id,
            "event_type": log.event_type,
            "payload": log.payload_json,
            "previous_hash": log.previous_hash,
            "current_hash": log.current_hash,
            "timestamp": log.timestamp.isoformat()
        })

    return {
        "success": True,
        "total_events": len(items),
        "logs": items
    }
