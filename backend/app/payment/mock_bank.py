"""
Mock Primary Bank Account Simulation for Hackathon Prototype
Simulates a user's primary bank account with demo funds.
DOES NOT connect to any real bank, NPCI, or real monetary system.
"""

from typing import Dict, Any, Tuple
import threading

class MockBankAccount:
    """
    Simulated Primary Bank Account storing fake demo funds.
    Provides atomic balance retrieval, debits, credits, and insufficient balance detection.
    """
    def __init__(self, initial_balance_paise: int = 2500000): # Default ₹25,000
        self._lock = threading.Lock()
        self._accounts: Dict[str, Dict[str, Any]] = {
            "USER_DEFAULT_001": {
                "user_id": "USER_DEFAULT_001",
                "bank_name": "Demo Bank of India",
                "account_reference": "MOCK_ACC_99018274",
                "balance_paise": initial_balance_paise,
                "currency": "INR"
            }
        }
        self.default_balance_paise = initial_balance_paise

    def get_account(self, user_id: str) -> Dict[str, Any]:
        with self._lock:
            if user_id not in self._accounts:
                self._accounts[user_id] = {
                    "user_id": user_id,
                    "bank_name": "Demo Bank of India",
                    "account_reference": f"MOCK_ACC_{abs(hash(user_id)) % 100000000:08d}",
                    "balance_paise": self.default_balance_paise,
                    "currency": "INR"
                }
            acc = self._accounts[user_id]
            return {
                "user_id": acc["user_id"],
                "bank_name": acc["bank_name"],
                "account_reference": acc["account_reference"],
                "balance_paise": acc["balance_paise"],
                "balance_rupees": acc["balance_paise"] / 100.0,
                "currency": acc["currency"]
            }

    def get_balance_paise(self, user_id: str) -> int:
        return self.get_account(user_id)["balance_paise"]

    def debit_account(self, user_id: str, amount_paise: int, merchant_vpa: str) -> Tuple[bool, str]:
        with self._lock:
            acc = self._accounts.get(user_id)
            if not acc:
                acc = {
                    "user_id": user_id,
                    "bank_name": "Demo Bank of India",
                    "account_reference": f"MOCK_ACC_{abs(hash(user_id)) % 100000000:08d}",
                    "balance_paise": self.default_balance_paise,
                    "currency": "INR"
                }
                self._accounts[user_id] = acc

            if amount_paise <= 0:
                return False, "INVALID_AMOUNT: Amount must be positive"

            if acc["balance_paise"] < amount_paise:
                return False, f"INSUFFICIENT_FUNDS: Bank balance (₹{acc['balance_paise']/100:.2f}) is lower than requested debit (₹{amount_paise/100:.2f})"

            acc["balance_paise"] -= amount_paise
            return True, f"SUCCESS: Debited ₹{amount_paise/100:.2f} from {acc['account_reference']}. New Balance: ₹{acc['balance_paise']/100:.2f}"

    def credit_merchant(self, merchant_vpa: str, amount_paise: int):
        # Simulated merchant settlement logging
        pass

    def reset_account(self, user_id: str, balance_paise: int = 2500000):
        with self._lock:
            if user_id in self._accounts:
                self._accounts[user_id]["balance_paise"] = balance_paise
            else:
                self._accounts[user_id] = {
                    "user_id": user_id,
                    "bank_name": "Demo Bank of India",
                    "account_reference": f"MOCK_ACC_{abs(hash(user_id)) % 100000000:08d}",
                    "balance_paise": balance_paise,
                    "currency": "INR"
                }

mock_bank = MockBankAccount()
