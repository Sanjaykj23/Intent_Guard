import uuid
from typing import List, Dict, Any

class Chunker:
    def __init__(self, chunk_size: int = 500, overlap: int = 100):
        self.chunk_size = chunk_size
        self.overlap = overlap

    def chunk_document(self, doc: Dict[str, Any]) -> List[Dict[str, Any]]:
        text = doc.get("content", "")
        doc_id = doc.get("document_id", "DOC_UNKNOWN")
        merchant_id = doc.get("merchant_id", "GENERAL")
        doc_type = doc.get("document_type", "general")
        source = doc.get("source", "unknown")

        words = text.split()
        chunks = []
        
        if len(words) <= self.chunk_size:
            chunk_id = f"chk_{doc_id}_{uuid.uuid4().hex[:6]}"
            chunks.append({
                "chunk_id": chunk_id,
                "document_id": doc_id,
                "merchant_id": merchant_id,
                "document_type": doc_type,
                "content": text,
                "source": source
            })
            return chunks

        i = 0
        step = self.chunk_size - self.overlap
        while i < len(words):
            chunk_words = words[i:i + self.chunk_size]
            chunk_text = " ".join(chunk_words)
            chunk_id = f"chk_{doc_id}_{uuid.uuid4().hex[:6]}"
            chunks.append({
                "chunk_id": chunk_id,
                "document_id": doc_id,
                "merchant_id": merchant_id,
                "document_type": doc_type,
                "content": chunk_text,
                "source": source
            })
            i += step

        return chunks

chunker = Chunker()
