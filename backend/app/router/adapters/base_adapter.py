from typing import List, Dict, Any
from backend.app.schemas.intent_schemas import UCPActionCandidate

class BaseActionAdapter:
    """
    Universal ACM (Agent Commerce Model) Base Adapter Interface.
    Enforces 7-stage commerce lifecycle: DISCOVER -> SEARCH -> QUOTE -> LOCK -> ORDER -> PAY -> AUDIT.
    """
    async def acm_discover(self, intent_slots: Dict[str, Any]) -> List[UCPActionCandidate]:
        raise NotImplementedError

    async def acm_quote_lock(self, candidate: UCPActionCandidate) -> UCPActionCandidate:
        raise NotImplementedError

    async def acm_execute_pay(self, candidate: UCPActionCandidate, token_hash: str) -> Dict[str, Any]:
        raise NotImplementedError
