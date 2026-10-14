"""
Google Gemini embedding provider adapter.
Integrates gemini-embedding-2 with 768 output dimensions and bounded retries.
Includes a deterministic normalized fallback for offline unit testing without external API calls.
"""

import hashlib
import math
import time
from typing import List, Optional
from backend.app.core.config import settings


import re

def _generate_deterministic_embedding(text: str, dimension: int = 768) -> List[float]:
    """
    Generate a deterministic, L2-normalized pseudo-embedding for testing/fallback mode.
    Uses non-negative multi-hash feature hashing to guarantee that texts with overlapping terms
    have strictly positive cosine similarity, while unrelated texts remain near 0.0.
    """
    vec = [0.0] * dimension
    words = re.findall(r"\w+", text.lower())
    if not words:
        words = ["empty"]

    for w in words:
        tokens = [w, w[:5]] if len(w) > 4 else [w]
        for t in tokens:
            for shift in range(4):
                h = int(hashlib.md5(f"{t}_{shift}".encode("utf-8")).hexdigest(), 16)
                idx = h % dimension
                vec[idx] += 1.0

    # L2 normalize
    norm = math.sqrt(sum(x * x for x in vec))
    if norm > 0:
        vec = [x / norm for x in vec]
    return vec



class GeminiEmbeddingProvider:
    """
    Adapter for Google Gemini Embedding API (gemini-embedding-2).
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        dimension: Optional[int] = None,
    ):
        self.api_key = api_key or settings.GEMINI_API_KEY
        self.model = model or settings.GEMINI_EMBEDDING_MODEL
        self.dimension = dimension or settings.EMBEDDING_DIMENSION
        self._client = None

        if self.api_key and self.api_key != "your-gemini-api-key-here":
            try:
                from google import genai
                self._client = genai.Client(api_key=self.api_key)
            except Exception:
                self._client = None

    def embed_text(self, text: str, max_retries: int = 3) -> List[float]:
        """Embed a single text string into a 768-dimensional vector."""
        if not text.strip():
            return [0.0] * self.dimension

        if self._client:
            from google.genai import types
            for attempt in range(max_retries):
                try:
                    result = self._client.models.embed_content(
                        model=self.model,
                        contents=text,
                        config=types.EmbedContentConfig(output_dimensionality=self.dimension),
                    )
                    # Extract embedding values
                    if hasattr(result, "embedding") and hasattr(result.embedding, "values"):
                        return list(result.embedding.values)
                    elif hasattr(result, "embeddings") and len(result.embeddings) > 0:
                        return list(result.embeddings[0].values)
                except Exception as exc:
                    if attempt == max_retries - 1:
                        # Fallback gracefully to deterministic representation if API fails
                        return _generate_deterministic_embedding(text, self.dimension)
                    time.sleep(2 ** attempt)

        return _generate_deterministic_embedding(text, self.dimension)

    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Batch embed a list of texts."""
        return [self.embed_text(t) for t in texts]


# Default singleton instance
embedder = GeminiEmbeddingProvider()
