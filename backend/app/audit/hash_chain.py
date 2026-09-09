import hashlib
import json
from typing import Dict, Any

GENESIS_HASH = "0000000000000000000000000000000000000000000000000000000000000000"

class AppendOnlyHashChain:
    @staticmethod
    def compute_hash(previous_hash: str, payload: Dict[str, Any]) -> str:
        """
        Computes H_n = SHA256(H_{n-1} + Canonical Payload JSON).
        Guarantees tamper-evident audit ledger entries.
        """
        canonical_json = json.dumps(payload, sort_keys=True, separators=(',', ':'))
        combined_data = f"{previous_hash}{canonical_json}"
        return hashlib.sha256(combined_data.encode('utf-8')).hexdigest()

    @staticmethod
    def verify_chain(logs: list) -> bool:
        """
        Verifies integrity of audit log hash chain.
        Returns False if any tamper is detected.
        """
        prev_hash = GENESIS_HASH
        for log in logs:
            expected = AppendOnlyHashChain.compute_hash(prev_hash, log.payload)
            if expected != log.current_hash:
                return False
            prev_hash = log.current_hash
        return True

    @staticmethod
    def verify_link(previous_hash: str, payload: Dict[str, Any], current_hash: str) -> bool:
        expected = AppendOnlyHashChain.compute_hash(previous_hash, payload)
        return expected == current_hash

hash_chain = AppendOnlyHashChain()
