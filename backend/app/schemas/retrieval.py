"""
Pydantic schemas for semantic retrieval and vector search.
"""

from typing import List, Optional
from pydantic import BaseModel, Field


class QueryRequest(BaseModel):
    query: str = Field(min_length=1, description="Natural language search query")
    top_k: Optional[int] = Field(default=5, ge=1, le=50, description="Maximum number of candidate chunks to retrieve")
    similarity_threshold: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="Minimum cosine similarity score required",
    )
    document_ids: Optional[List[str]] = Field(
        default=None,
        description="Optional list of document IDs to scope the retrieval search",
    )


class RetrievedChunkResponse(BaseModel):
    chunk_id: str
    document_id: str
    filename: str
    page_number: int
    chunk_index: int
    content: str
    similarity_score: float


class RetrievalResponse(BaseModel):
    query: str
    retrieved_count: int
    chunks: List[RetrievedChunkResponse] = []
