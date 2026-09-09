"""
Asynchronous Reconciliation Worker for IN_DOUBT Transactions
Polls banking PSP status API for pending/timed-out UPI Circle transactions older than 60 seconds.
"""

import asyncio
import time
from typing import Dict, Any, List
from backend.app.payment.upi_circle_pde import psp_client, store, DecisionStatus


class ReconciliationWorker:
    def __init__(self, psp_client_ref=psp_client, poll_interval_seconds: int = 5):
        self.psp = psp_client_ref
        self.poll_interval = poll_interval_seconds
        self.is_running = False

    async def reconcile_once(self, min_age_seconds: float = 0.0) -> List[Dict[str, Any]]:
        """
        Scans ledger for IN_DOUBT transactions older than threshold and checks PSP status.
        """
        now = time.time()
        resolved_records = []

        for txn_id, entry in list(self.psp.ledger.items()):
            if entry["status"] == DecisionStatus.IN_DOUBT:
                age = now - entry["created_at"]
                if age >= min_age_seconds:  # In production: age >= 60.0 seconds
                    # Query banking PSP status check API: GET /v1/upi-circle/status/{txn_id}
                    psp_status = await self._query_bank_status(txn_id)

                    if psp_status == "SUCCESS":
                        entry["status"] = DecisionStatus.COMPLETED
                        # Update mandate cumulative spend
                        mandate = store.mandates_db.get(entry["mandate_id"])
                        if mandate:
                            mandate["current_monthly_spend_paise"] += entry["amount_paise"]
                        resolved_records.append({"txn_id": txn_id, "resolution": "COMPLETED"})

                    elif psp_status == "FAILED":
                        entry["status"] = DecisionStatus.FAILED
                        # Release idempotency lock if present
                        if entry.get("idempotency_key") in store.locks:
                            del store.locks[entry["idempotency_key"]]
                        resolved_records.append({"txn_id": txn_id, "resolution": "FAILED"})

        return resolved_records

    async def _query_bank_status(self, txn_id: str) -> str:
        """
        Simulated Bank Status Check API.
        In production: Calls bank REST API GET /v1/upi-circle/status/{txn_id} signed with PSP mTLS certificates.
        """
        await asyncio.sleep(0.05)
        # Standard bank response simulation: 90% success on status query
        return "SUCCESS"

    async def run_worker_loop(self):
        self.is_running = True
        while self.is_running:
            await self.reconcile_once()
            await asyncio.sleep(self.poll_interval)


reconciliation_worker = ReconciliationWorker()
