# Simulated UPI Circle Payment Flow & Agentic Safety Architecture

> [!IMPORTANT]
> **DISCLAIMER & DEMO NOTICE**  
> This implementation simulates UPI Circle delegation behavior for demonstration purposes. It does **NOT** connect to NPCI, UPI, a bank PSP/TPAP, or a real bank. All monetary amounts represent simulated test funds.

---

## 1. Simulated UPI Circle Architecture

```
User (Primary Account Owner)
  ↓
AI Payment Agent (Delegated Authority)
  ↓
Chatbot & Natural Language Intent Extraction
  ↓
Payment Decision Engine (PDE - 14 Security Checks)
  ↓
UPICircleProvider Interface (Abstract Base Class)
  ↓
MockUPICircleProvider
  ↓
Mock Primary Bank Account (Demo Balance ₹25,000)
  ↓
Transaction Ledger (Immutable Audit Chain)
  ↓
Chatbot Payment Result & UI Receipt
```

The system demonstrates **delegated agentic commerce**, where a Primary Account Owner delegates payment authority to an AI Payment Agent within configurable NPCI regulatory guardrails.

---

## 2. Delegation Model

| Field Name | Type | Value / Default | Description |
|---|---|---|---|
| `delegation_id` | String | `DEL_001` | Unique delegation identifier |
| `primary_user_id` | String | `USER_DEFAULT_001` | Primary account owner |
| `secondary_profile_id` | String | `AI_AGENT_001` | Authorized AI agent profile |
| `status` | Enum | `ACTIVE` | Delegation lifecycle (`ACTIVE` / `INACTIVE`) |
| `monthly_limit` | Integer | ₹15,000 (`1500000` paise) | NPCI monthly cumulative limit cap |
| `transaction_limit` | Integer | ₹5,000 (`500000` paise) | NPCI per-transaction autonomous limit cap |
| `spent_this_month` | Integer | Calculated | Cumulative spend in active billing cycle |
| `remaining_this_month`| Integer | Calculated | Available spend quota remaining |
| `currency` | String | `INR` | Standard currency unit |
| `expires_at` | Timestamp | `+365 days` | Delegation expiry date |
| `allowed_categories` | Array | `["GROCERY", "FOOD", "MOBILE_RECHARGE", "TRANSPORT", "SHOPPING"]` | Category allowlist |
| `blocked_categories` | Array | `["GAMBLING", "CRYPTO", "CASH_WITHDRAWAL"]` | Security blocklist |

---

## 3. Payment Decision Engine (PDE) Decision Flow

The PDE evaluates every payment request against **14 deterministic security checks**:

1. **User Authentication**: Validates session JWT claims.
2. **Delegation Existence**: Verifies primary user delegation record exists.
3. **Delegation Active**: Confirms mandate status is `ACTIVE`.
4. **Delegation Unexpired**: Verifies `CURRENT_TIMESTAMP < expires_at`.
5. **Positive Amount**: Confirms price > 0.
6. **Currency INR**: Enforces `INR` currency constraint.
7. **Per-Transaction Limit**: Enforces amount $\le$ ₹5,000 (500,000 paise).
8. **Monthly Budget Quota**: Enforces $(\text{spent} + \text{amount}) \le$ ₹15,000.
9. **Category Allowed**: Validates category against allowlist.
10. **Category Blocked**: Verifies category is NOT in blocklist (e.g. `CRYPTO`, `GAMBLING`).
11. **Merchant Verification**: Resolves merchant VPA in registry.
12. **Mock Bank Balance**: Confirms available mock bank funds $\ge$ requested debit.
13. **Sliding Window Velocity**: Max 3 auto-purchases per 10 minutes.
14. **Transaction Splitting Protection**: Detects attempts to split a single purchase over ₹5,000 into multiple smaller transactions within 10 minutes.

### Decision States
- **`APPROVED`**: All 14 checks pass, risk score $< 0.40$. Autonomous debit executed.
- **`DENIED`**: Hard policy check failed (e.g. limit breach, blocked category, transaction splitting).
- **`REQUIRES_USER_APPROVAL`**: Risk score $\ge 0.40$ (e.g. ₹4,500 electronics purchase). Renders confirmation card with `[ Approve Payment ]` / `[ Reject Payment ]`.

---

## 4. API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/upi-circle/delegation` | Activate simulated UPI Circle delegation |
| `GET` | `/api/upi-circle/delegation` | Retrieve active delegation status & limits |
| `DELETE` | `/api/upi-circle/delegation` | Revoke delegation |
| `POST` | `/api/payment/decision` | Submit intent to Payment Decision Engine |
| `POST` | `/api/payment/initiate` | Execute or reject pending user approval transaction |
| `GET` | `/api/payment/history` | Retrieve transaction ledger history |
| `GET` | `/api/payment/{txn_id}` | Query individual transaction status |
| `GET` | `/api/wallet/balance` | Query mock bank account balance |
| `POST` | `/api/demo/reset` | Hackathon development-only environment reset |

---

## 5. Mock Bank & Provider Abstraction

### Provider Abstraction Layer (`UPICircleProvider`)
The `PaymentDecisionEngine` interacts exclusively with the abstract `UPICircleProvider` interface. The current concrete implementation is `MockUPICircleProvider`.

```python
class UPICircleProvider(ABC):
    @abstractmethod
    async def create_delegation(...)
    @abstractmethod
    async def get_delegation(...)
    @abstractmethod
    async def revoke_delegation(...)
    @abstractmethod
    async def validate_delegation(...)
    @abstractmethod
    async def initiate_payment(...)
    @abstractmethod
    async def get_payment_status(...)
```

To replace the mock provider with an authorized bank PSP/TPAP integration in production, simply implement `RealPSPUPICircleProvider(UPICircleProvider)` and replace the dependency instance. No changes to the PDE, Chatbot, or UI will be required.

### Mock Bank (`MockBankAccount`)
- **Default Balance**: ₹25,000 (2,500,000 paise)
- **Account Reference**: `MOCK_ACC_99018274`
- Performs atomic debits and insufficient balance detection.

---

## 6. How to Run the Simulator & Test Suite

### Running the Application
```bash
# Start Backend FastAPI Server
uvicorn backend.app.main:app --reload --port 8000

# Start Frontend React App
npm run dev
```

### Running Automated Test Suite
```bash
pytest backend/tests/test_simulated_upi_circle.py -v
```

---

## 7. Demo Scenarios (Step-by-Step)

1. **Successful Payment (₹350 Grocery)**
   - User types: `"Buy groceries for ₹350"`
   - Result: `APPROVED` $\rightarrow$ `SUCCESS`
   - Bank balance becomes ₹24,650; Spent becomes ₹350.

2. **Transaction Limit Denial (₹6,000)**
   - User types: `"Buy something for ₹6,000"`
   - Result: `DENIED` (`TRANSACTION_LIMIT_EXCEEDED`)
   - Reason: Requested amount exceeds delegated ₹5,000 limit.

3. **High-Risk User Approval (₹4,500 Electronics)**
   - User types: `"Buy electronics for ₹4,500"`
   - Result: `REQUIRES_USER_APPROVAL`
   - Card rendered with `[ Approve Payment ]` and `[ Reject Payment ]`. Clicking `Approve` executes payment (`SUCCESS`).

4. **Blocked Category Denial (Crypto)**
   - User types: `"Send ₹1,000 to a crypto merchant"`
   - Result: `DENIED` (`CATEGORY_BLOCKED`)

5. **Transaction Splitting Protection**
   - User types: `"Buy phone for ₹4,000"` followed immediately by `"Buy phone part 2 for ₹4,000"`
   - Result: Second intent returns `DENIED` (`POSSIBLE_TRANSACTION_SPLITTING`).
