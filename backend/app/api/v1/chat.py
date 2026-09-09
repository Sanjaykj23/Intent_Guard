import uuid
import datetime
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from backend.app.core.database import get_db
from backend.app.schemas.intent_schemas import IntentRequest, UserPolicySchema, ProductResult, CanonicalIntent
from backend.app.ai.llama_service import llama_service
from backend.app.search.deterministic_parser import deterministic_parser
from backend.app.search.slot_resolver import slot_resolver
from backend.app.guard.verification_engine import verification_engine
from backend.app.search.search_router import search_router
from backend.app.guard.policy_engine import policy_engine
from backend.app.router.adapters.telecom_adapter import operator_lookup_api
from backend.app.rag.retriever import retriever
from backend.app.revenue.revenue_engine import revenue_engine
from backend.app.models.db_models import QuoteModel, AuditLogModel, PaymentPolicyModel
from backend.app.audit.hash_chain import hash_chain, GENESIS_HASH

router = APIRouter(prefix="/chat", tags=["Chat & Intent"])

@router.post("/process")
async def process_user_intent(req: IntentRequest, db: AsyncSession = Depends(get_db)):
    # 1. Llama AI Intent Extraction & Slot Filling
    raw_llm_intent = await llama_service.extract_intent(req.user_message)

    # 2. Zero-Trust Slot Resolution & Conflict Detection (Deterministic REGEX overrides untrusted LLM for money & constraints)
    canonical_intent = slot_resolver.resolve_canonical_intent(req.user_message, raw_llm_intent)

    # Enforce canonical max price on raw intent for downstream query compatibility
    if canonical_intent.max_price_paise is not None:
        raw_llm_intent.max_price_paise = canonical_intent.max_price_paise

    # 3. Pydantic & Constraint Schema Validation via Verification Engine
    validation_res = verification_engine.validate_canonical_intent(canonical_intent)
    if not validation_res["valid"]:
        return {
            "success": False,
            "reply": f"Intent validation failed: {', '.join(validation_res['errors'])}",
            "ai_provider": llama_service.active_provider,
            "intent": raw_llm_intent,
            "canonical_intent": canonical_intent,
            "products": [],
            "policy_check": None,
            "quote": None,
            "rag_context": "",
            "revenue_recommendations": None
        }

    intent_type = (raw_llm_intent.intent or "").lower()

    # 4. Handle Greeting & Conversational Intents (NO PRODUCTS)
    if intent_type in ["greeting", "conversational"]:
        return {
            "success": True,
            "reply": "Hello! I am IntentGuard AI, your safe universal transaction assistant. How can I help you today? You can ask me to search for products under a budget, order tea, recharge your mobile, or check spending policies.",
            "ai_provider": llama_service.active_provider,
            "intent": raw_llm_intent,
            "canonical_intent": canonical_intent,
            "products": [],
            "policy_check": None,
            "quote": None,
            "rag_context": "",
            "revenue_recommendations": None
        }

    # 5. Slot Filling for Recharge
    if intent_type == "mobile_recharge":
        phone_match = re.search(r'\b\d{10}\b', req.user_message)
        operator_match = re.search(r'(jio|airtel|vi|bsnl)', req.user_message, re.IGNORECASE)
        
        missing = []
        if not phone_match:
            missing.append("a 10-digit mobile number")
        
        if phone_match and not operator_match:
            # Dynamically fetch the operator using the API!
            detected_op = await operator_lookup_api.lookup(phone_match.group(0))
            if detected_op:
                req.user_message += f" {detected_op}"
                # Append to canonical intent as well so the search query includes it
                canonical_intent.product_query += f" {detected_op}"
                raw_llm_intent.product = (raw_llm_intent.product or "") + f" {detected_op}"
            else:
                missing.append("your operator (e.g. Jio, Airtel)")
        elif not phone_match and not operator_match:
            missing.append("your operator (e.g. Jio, Airtel)")
            
        if missing:
            return {
                "success": True,
                "reply": f"Please provide {' and '.join(missing)} so I can fetch the correct recharge plans.",
                "ai_provider": llama_service.active_provider,
                "intent": raw_llm_intent,
                "canonical_intent": canonical_intent,
                "products": [],
                "policy_check": None,
                "quote": None,
                "rag_context": "",
                "revenue_recommendations": None
            }

    # 5. Retrieve Policy Context via Qdrant Vector DB (RAG)
    rag_context = retriever.retrieve_policy_context(req.user_message)

    # 6. Handle Policy Question Intent (NO PRODUCTS unless shopping query)
    if intent_type == "policy_question" and not raw_llm_intent.product:
        reply_msg = f"Here is the policy information retrieved from our knowledge base:\n{rag_context}" if rag_context else "I checked our knowledge base for your policy query."
        return {
            "success": True,
            "reply": reply_msg,
            "ai_provider": llama_service.active_provider,
            "intent": raw_llm_intent,
            "canonical_intent": canonical_intent,
            "products": [],
            "policy_check": None,
            "quote": None,
            "rag_context": rag_context,
            "revenue_recommendations": None
        }

    # 7. Live Candidate Search & Tool Calling Orchestration
    raw_candidates = await search_router.route_and_search(raw_llm_intent)

    # 8. MULTI-LAYER VERIFICATION & HARD CONSTRAINT GATING (Price, Delivery Days, Verified Exact Action URLs)
    verified_candidates = verification_engine.verify_and_filter_candidates(raw_candidates, canonical_intent)

    # 9. Qdrant Vector Hybrid Reranking
    reranked_candidates = retriever.cache_and_rerank_live_products(verified_candidates, raw_llm_intent)

    # 8. Llama ID-Only Recommendation Protocol
    rec_result = await llama_service.recommend_verified_candidates(reranked_candidates, req.user_message)
    rec_ids = rec_result.get("recommended_ids", [])
    
    # Map Llama returned IDs back to authoritative verified backend candidates
    final_products: List[ProductResult] = []
    cand_map = {c.id: c for c in reranked_candidates}
    
    for r_id in rec_ids:
        if r_id in cand_map and cand_map[r_id] not in final_products:
            final_products.append(cand_map[r_id])

    # If no IDs mapped, use top reranked verified candidates
    if not final_products:
        final_products = reranked_candidates[:3]

    # 9. Retrieve User Spending Policy
    pol_result = await db.execute(select(PaymentPolicyModel).where(PaymentPolicyModel.user_id == req.user_id))
    policy_row = pol_result.scalars().first()

    if policy_row:
        user_policy = UserPolicySchema(
            user_id=req.user_id,
            daily_limit_paise=policy_row.daily_limit_paise,
            transaction_limit_paise=policy_row.transaction_limit_paise,
            auto_approval_threshold_paise=policy_row.auto_approval_threshold_paise,
            allowed_categories=eval(policy_row.allowed_categories_json),
            policy_version=policy_row.policy_version
        )
    else:
        user_policy = UserPolicySchema(user_id=req.user_id)

    # 10. Evaluate IntentGuard Security Gates for Top Recommended Verified Product
    top_product = final_products[0] if final_products else None
    policy_check = None
    quote_data = None
    revenue_recommendations = None

    if top_product:
        policy_check = policy_engine.evaluate_transaction(
            policy=user_policy,
            amount_paise=top_product.price_paise,
            category=top_product.category
        )

        # 11. Merchant Revenue Engine Growth Recommendations
        revenue_recommendations = revenue_engine.generate_growth_recommendations(top_product)

        # 12. Generate 3-Minute Quote Lock & Hash
        quote_id = f"QUOTE_{uuid.uuid4().hex[:8]}"
        expires_at = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(minutes=3)
        
        quote_payload = {
            "quote_id": quote_id,
            "user_id": req.user_id,
            "merchant_name": top_product.merchant,
            "product_name": top_product.title,
            "price_paise": top_product.price_paise,
            "product_url": top_product.product_url,
            "expires_at": expires_at.isoformat()
        }
        quote_hash = hash_chain.compute_hash(GENESIS_HASH, quote_payload)

        new_quote = QuoteModel(
            quote_id=quote_id,
            user_id=req.user_id,
            merchant_name=top_product.merchant,
            product_name=top_product.title,
            price_paise=top_product.price_paise,
            product_url=top_product.product_url,
            expires_at=expires_at,
            quote_hash=quote_hash
        )
        db.add(new_quote)

        # 13. Update Cryptographic Audit Ledger
        last_audit = await db.execute(select(AuditLogModel).order_by(AuditLogModel.id.desc()).limit(1))
        last_row = last_audit.scalars().first()
        prev_hash = last_row.current_hash if last_row else GENESIS_HASH

        audit_payload = {
            "intent": raw_llm_intent.intent,
            "product_title": top_product.title,
            "price_paise": top_product.price_paise,
            "policy_status": policy_check.status_code,
            "quote_id": quote_id
        }
        curr_hash = hash_chain.compute_hash(prev_hash, audit_payload)

        audit_entry = AuditLogModel(
            event_id=f"EVT_{uuid.uuid4().hex[:8]}",
            event_type="INTENT_PROCESSED",
            payload_json=str(audit_payload),
            previous_hash=prev_hash,
            current_hash=curr_hash
        )
        db.add(audit_entry)
        await db.commit()

        quote_data = {
            "quote_id": quote_id,
            "expires_at": expires_at.isoformat(),
            "quote_hash": quote_hash
        }

    explanation = rec_result.get("explanation", "")
    if not explanation and top_product:
        explanation = f"I analyzed verified candidates using Llama 3 and Qdrant. Top recommendation: '{top_product.title}' from {top_product.merchant} at {top_product.formatted_price}."

    return {
        "success": True,
        "reply": explanation,
        "ai_provider": llama_service.active_provider,
        "intent": raw_llm_intent,
        "canonical_intent": canonical_intent,
        "products": final_products,
        "policy_check": policy_check,
        "quote": quote_data,
        "rag_context": rag_context,
        "revenue_recommendations": revenue_recommendations
    }
