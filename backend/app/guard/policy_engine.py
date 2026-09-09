from backend.app.schemas.intent_schemas import PolicyCheckResult, UserPolicySchema

class IntentGuardPolicyEngine:
    @staticmethod
    def evaluate_transaction(
        policy: UserPolicySchema,
        amount_paise: int,
        category: str,
        daily_spent_paise: int = 0
    ) -> PolicyCheckResult:
        """
        Deterministic security policy check.
        Decides WHETHER an action or payment is allowed.
        """
        cat = (category or "apparel").lower()
        allowed_cats = [c.lower() for c in policy.allowed_categories]

        # Gate 1: Category Check
        if cat not in allowed_cats:
            return PolicyCheckResult(
                allowed=False,
                status_code="BLOCKED_CATEGORY_RESTRICTED",
                risk_level="HIGH",
                auto_approved=False,
                reason=f"Category '{category}' is not included in your allowed spending policy categories.",
                daily_spent_paise=daily_spent_paise,
                daily_limit_paise=policy.daily_limit_paise,
                transaction_limit_paise=policy.transaction_limit_paise
            )

        # Gate 2: Per-Transaction Ceiling
        if amount_paise > policy.transaction_limit_paise:
            return PolicyCheckResult(
                allowed=False,
                status_code="BLOCKED_TRANSACTION_LIMIT_EXCEEDED",
                risk_level="HIGH",
                auto_approved=False,
                reason=f"Amount ₹{amount_paise / 100:,.2f} exceeds maximum per-transaction policy limit of ₹{policy.transaction_limit_paise / 100:,.2f}.",
                daily_spent_paise=daily_spent_paise,
                daily_limit_paise=policy.daily_limit_paise,
                transaction_limit_paise=policy.transaction_limit_paise
            )

        # Gate 3: Daily Limit
        if (daily_spent_paise + amount_paise) > policy.daily_limit_paise:
            return PolicyCheckResult(
                allowed=False,
                status_code="BLOCKED_DAILY_BUDGET_EXCEEDED",
                risk_level="HIGH",
                auto_approved=False,
                reason=f"Transaction would push today's total spending to ₹{(daily_spent_paise + amount_paise) / 100:,.2f}, exceeding daily budget limit of ₹{policy.daily_limit_paise / 100:,.2f}.",
                daily_spent_paise=daily_spent_paise,
                daily_limit_paise=policy.daily_limit_paise,
                transaction_limit_paise=policy.transaction_limit_paise
            )

        # Gate 4: Risk Level & Human-in-the-loop Determination
        auto_approved = (amount_paise <= policy.auto_approval_threshold_paise)
        risk_level = "LOW" if auto_approved else ("MEDIUM" if amount_paise <= 100000 else "HIGH")

        reason = "Transaction meets policy limits and is pre-authorized for autonomous execution." if auto_approved else "Transaction within policy limits but requires explicit human confirmation."

        return PolicyCheckResult(
            allowed=True,
            status_code="ALLOWED",
            risk_level=risk_level,
            auto_approved=auto_approved,
            reason=reason,
            daily_spent_paise=daily_spent_paise,
            daily_limit_paise=policy.daily_limit_paise,
            transaction_limit_paise=policy.transaction_limit_paise
        )

policy_engine = IntentGuardPolicyEngine()
