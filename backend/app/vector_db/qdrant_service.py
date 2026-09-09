import time
from typing import List, Dict, Any
from backend.app.rag.embedding_service import embedding_service
from backend.app.rag.document_loader import document_loader
from backend.app.rag.chunker import chunker

class QdrantVectorDBService:
    def __init__(self):
        # Multi-collection vector store
        self.collections: Dict[str, List[Dict[str, Any]]] = {
            "merchant_policies": [],
            "platform_knowledge": [],
            "service_knowledge": [],
            "user_preferences": [],
            "live_search_cache": []
        }
        self.initialize_knowledge_base()

    def initialize_knowledge_base(self):
        """Pre-populates vector collections with chunked merchant policies and platform documentation."""
        docs = document_loader.load_all_documents()
        for doc in docs:
            chunks = chunker.chunk_document(doc)
            for chunk in chunks:
                vector = embedding_service.get_embedding(chunk["content"])
                item = {
                    "id": chunk["chunk_id"],
                    "vector": vector,
                    "payload": chunk,
                    "created_at": time.time()
                }
                col = "merchant_policies" if "policy" in chunk["document_type"] else "service_knowledge"
                self.collections[col].append(item)

    def upsert(self, collection_name: str, id_: str, text: str, payload: Dict[str, Any], ttl_seconds: int = None):
        vector = embedding_service.get_embedding(text)
        item = {
            "id": id_,
            "vector": vector,
            "payload": payload,
            "created_at": time.time(),
            "ttl": ttl_seconds
        }
        if collection_name not in self.collections:
            self.collections[collection_name] = []
        self.collections[collection_name].append(item)

    def search_similar(self, collection_name: str, query_text: str, top_k: int = 3) -> List[Dict[str, Any]]:
        self._purge_expired_cache()
        query_vector = embedding_service.get_embedding(query_text)
        items = self.collections.get(collection_name, [])

        results = []
        for item in items:
            sim = embedding_service.cosine_similarity(query_vector, item["vector"])
            results.append({
                "id": item["id"],
                "score": round(sim, 4),
                "payload": item["payload"]
            })

        # Sort descending by similarity score
        results.sort(key=lambda x: x["score"], reverse=True)
        return results[:top_k]

    def _purge_expired_cache(self):
        now = time.time()
        cache = self.collections.get("live_search_cache", [])
        valid_cache = []
        for item in cache:
            ttl = item.get("ttl")
            if ttl and (now - item["created_at"]) > ttl:
                continue # expired
            valid_cache.append(item)
        self.collections["live_search_cache"] = valid_cache

qdrant_service = QdrantVectorDBService()
