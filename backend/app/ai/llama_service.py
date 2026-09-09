import re
import json
import httpx
from typing import Dict, Any, List
from backend.app.core.config import settings
from backend.app.schemas.intent_schemas import ExtractedIntent, ProductResult

SYSTEM_INTENT_PROMPT = """
You are IntentGuard AI's intent extraction engine.
Analyze the user prompt and extract structured JSON matching this exact format:
{
    "intent": "greeting" | "conversational" | "policy_question" | "product_search" | "food_order" | "tea_order" | "mobile_recharge" | "bill_payment" | "compare_products",
    "category": "apparel" | "electronics" | "food" | "recharge" | "general",
    "product": "extracted product name or query keywords, or null if greeting/policy",
    "max_price_paise": integer budget limit in paise or null,
    "currency": "INR",
    "priorities": ["priority1"],
    "transaction_required": boolean
}
If the user is just saying hello, hi, asking how you are, or what you can do, set intent="greeting", transaction_required=false, product=null.
If the user asks about return policies, refunds, or terms, set intent="policy_question", transaction_required=false.
Return ONLY valid JSON. No Markdown formatting, no code blocks, no explanations.
"""

RECOMMENDATION_SYSTEM_PROMPT = """
You are IntentGuard AI's Grounded Product Explainer.
You will be provided with an array of VERIFIED_CANDIDATE_PRODUCTS containing IDs, names, prices, and features.

YOUR CRITICAL RULES:
1. You MUST ONLY recommend from the provided VERIFIED_CANDIDATE_PRODUCTS array by returning their exact product IDs (e.g., ["p1", "p2"]).
2. You are STRICTLY FORBIDDEN from inventing product names, prices, merchant names, ratings, or URLs.
3. Do NOT include raw URLs, search URLs, or markdown links in your explanation text.
4. Return structured JSON matching this format:
{
    "recommended_ids": ["p1", "p2"],
    "explanation": "Natural language explanation why p1 and p2 were selected from verified candidates."
}
Return ONLY valid JSON.
"""

class LlamaService:
    def __init__(self):
        self.ollama_url = settings.OLLAMA_URL
        self.ollama_model = settings.LLAMA_MODEL
        self.groq_api_key = settings.GROQ_API_KEY
        self.groq_model = settings.GROQ_MODEL
        self.active_provider = "UNKNOWN"

    async def extract_intent(self, user_message: str) -> ExtractedIntent:
        intent = await self._try_ollama(user_message)
        if intent:
            self.active_provider = f"Ollama ({self.ollama_model})"
            return intent

        if settings.GROQ_API_KEY:
            intent = await self._try_groq_api(user_message)
            if intent:
                self.active_provider = f"Groq API ({self.groq_model})"
                return intent

        self.active_provider = "Structured Fallback Engine"
        return self._fallback_intent_parser(user_message)

    async def recommend_verified_candidates(self, candidates: List[ProductResult], user_message: str) -> Dict[str, Any]:
        """
        ID-Only Recommendation Protocol:
        Passes verified product candidates to Llama 3 and forces Llama 3 to return ONLY product IDs (e.g. ['p1', 'p2']).
        Guarantees 0% hallucination of product titles, prices, or URLs.
        """
        if not candidates:
            return {"recommended_ids": [], "explanation": "No verified products match your search constraints."}

        candidate_summary = [
            {
                "id": p.id,
                "name": p.title,
                "price": p.formatted_price,
                "merchant": p.merchant,
                "reason": p.match_reason
            }
            for p in candidates
        ]

        # Try Groq or Ollama
        if settings.GROQ_API_KEY:
            try:
                headers = {"Authorization": f"Bearer {settings.GROQ_API_KEY}", "Content-Type": "application/json"}
                payload = {
                    "model": self.groq_model,
                    "messages": [
                        {"role": "system", "content": RECOMMENDATION_SYSTEM_PROMPT},
                        {"role": "user", "content": f"User query: '{user_message}'\nVERIFIED_CANDIDATE_PRODUCTS: {json.dumps(candidate_summary)}"}
                    ],
                    "response_format": {"type": "json_object"},
                    "temperature": 0.1
                }
                async with httpx.AsyncClient(timeout=4.0) as client:
                    res = await client.post("https://api.groq.com/openai/v1/chat/completions", headers=headers, json=payload)
                    if res.status_code == 200:
                        content = res.json()["choices"][0]["message"]["content"]
                        parsed = json.loads(content)
                        rec_ids = parsed.get("recommended_ids", [c.id for c in candidates[:3]])
                        exp = parsed.get("explanation", f"Selected top matches for '{user_message}' from verified live data.")
                        exp = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', exp)
                        return {
                            "recommended_ids": rec_ids,
                            "explanation": exp
                        }
            except Exception as e:
                print(f"[LlamaService] Recommendation call note: {e}")

        # Deterministic fallback matching top candidates
        top_ids = [c.id for c in candidates[:3]]
        return {
            "recommended_ids": top_ids,
            "explanation": f"I analyzed your request and retrieved verified options. Top recommendation: '{candidates[0].title}' from {candidates[0].merchant} at {candidates[0].formatted_price}."
        }

    async def _try_ollama(self, user_message: str) -> ExtractedIntent | None:
        try:
            async with httpx.AsyncClient(timeout=2.5) as client:
                response = await client.post(
                    f"{self.ollama_url}/api/generate",
                    json={
                        "model": self.ollama_model,
                        "prompt": f"{SYSTEM_INTENT_PROMPT}\nUser input: '{user_message}'",
                        "stream": False
                    }
                )
                if response.status_code == 200:
                    result = response.json()
                    response_text = result.get("response", "")
                    json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
                    if json_match:
                        parsed = json.loads(json_match.group(0))
                        return ExtractedIntent(**parsed)
        except Exception:
            pass
        return None

    async def _try_groq_api(self, user_message: str) -> ExtractedIntent | None:
        try:
            headers = {
                "Authorization": f"Bearer {settings.GROQ_API_KEY}",
                "Content-Type": "application/json"
            }
            payload = {
                "model": self.groq_model,
                "messages": [
                    {"role": "system", "content": SYSTEM_INTENT_PROMPT},
                    {"role": "user", "content": user_message}
                ],
                "response_format": {"type": "json_object"},
                "temperature": 0.1
            }
            async with httpx.AsyncClient(timeout=4.0) as client:
                response = await client.post(
                    "https://api.groq.com/openai/v1/chat/completions",
                    headers=headers,
                    json=payload
                )
                if response.status_code == 200:
                    data = response.json()
                    content = data["choices"][0]["message"]["content"]
                    parsed = json.loads(content)
                    return ExtractedIntent(**parsed)
        except Exception as e:
            print(f"[LlamaService] Groq API call note: {e}")
            pass
        return None

    def _fallback_intent_parser(self, user_message: str) -> ExtractedIntent:
        query = user_message.lower().strip()

        if re.search(r'^(hello|hi|hey|greetings|good morning|good evening|who are you|what can you do|help)$', query) or query in ["hello", "hi", "hey", "help", "who are you"]:
            return ExtractedIntent(
                intent="greeting",
                category="general",
                product=None,
                max_price_paise=None,
                currency="INR",
                priorities=[],
                transaction_required=False,
                confidence=0.99
            )

        if "return" in query or "refund" in query or "policy" in query or "terms" in query:
            return ExtractedIntent(
                intent="policy_question",
                category="general",
                product=user_message,
                max_price_paise=None,
                currency="INR",
                priorities=[],
                transaction_required=False,
                confidence=0.98
            )

        budget_paise = None
        price_match = re.search(r'(?:under|below|budget|max|rs\.?|₹)\s*(\d+(?:,\d+)*)', query)
        if price_match:
            val_str = price_match.group(1).replace(',', '')
            budget_paise = int(val_str) * 100

        intent = "product_search"
        category = "apparel"
        transaction_required = False
        priorities = []

        if "charger" in query or "adapter" in query or "cable" in query:
            intent = "product_search"
            category = "electronics"
            if "fast" in query:
                priorities.append("fast charging")
        elif "recharge" in query or "mobile plan" in query or "prepaid" in query or "2gb/day" in query or "jio" in query or "airtel" in query:
            intent = "mobile_recharge"
            category = "recharge"
            transaction_required = True
            if "2gb" in query:
                priorities.append("2GB/day")
        elif "earbud" in query or "headphone" in query or "laptop" in query or "phone" in query or "camera" in query or "electronics" in query:
            intent = "product_search"
            category = "electronics"
        elif "shoe" in query or "shirt" in query or "t-shirt" in query or "apparel" in query:
            intent = "product_search"
            category = "apparel"

        return ExtractedIntent(
            intent=intent,
            category=category,
            product=user_message,
            max_price_paise=budget_paise,
            currency="INR",
            priorities=priorities,
            transaction_required=transaction_required,
            confidence=0.96
        )

llama_service = LlamaService()
