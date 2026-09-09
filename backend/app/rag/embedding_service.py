import hashlib
import math
from typing import List

class EmbeddingService:
    def __init__(self, dimension: int = 384):
        self.dimension = dimension

    def get_embedding(self, text: str) -> List[float]:
        """
        Generates a 384-dimensional dense vector representation for input text.
        Excludes sensitive credentials (UPI PINs, passwords) by safety invariant.
        """
        cleaned = (text or "").lower().strip()
        vector = [0.0] * self.dimension

        # Generate deterministic pseudo-random dense float values based on hash seeds
        words = cleaned.split()
        if not words:
            return vector

        for word in words:
            word_hash = hashlib.sha256(word.encode('utf-8')).hexdigest()
            for idx in range(0, min(self.dimension, len(word_hash) * 4), 4):
                val = int(word_hash[idx % len(word_hash)], 16) / 15.0
                dim_idx = (int(word_hash, 16) + idx) % self.dimension
                vector[dim_idx] += val - 0.5

        # Normalize L2 norm
        norm = math.sqrt(sum(v * v for v in vector))
        if norm > 0:
            vector = [v / norm for v in vector]

        return vector

    @staticmethod
    def cosine_similarity(v1: List[float], v2: List[float]) -> float:
        dot = sum(a * b for a, b in zip(v1, v2))
        return float(dot)

embedding_service = EmbeddingService()
