"""
Semantic retrieval service for ProofLens AI.
Performs authorization-scoped vector similarity search over document chunks.
Uses native pgvector on PostgreSQL and fast vector similarity in SQLite/fallback environments.
"""

import math
from dataclasses import dataclass
from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.config import settings
from backend.app.models.chunk import DocumentChunk
from backend.app.models.document import Document
from backend.app.services.embeddings.gemini_embedder import embedder


def compute_cosine_similarity(vec_a: List[float], vec_b: List[float]) -> float:
    """Compute cosine similarity between two float vectors."""
    dot = sum(a * b for a, b in zip(vec_a, vec_b))
    norm_a = math.sqrt(sum(a * a for a in vec_a))
    norm_b = math.sqrt(sum(b * b for b in vec_b))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


@dataclass
class RetrievedChunk:
    chunk_id: str
    document_id: str
    filename: str
    page_number: int
    chunk_index: int
    content: str
    similarity_score: float


async def search_workspace_chunks(
    db: AsyncSession,
    workspace_id: str,
    query: str,
    top_k: int = 5,
    similarity_threshold: Optional[float] = None,
    allowed_doc_ids: Optional[List[str]] = None,
) -> List[RetrievedChunk]:
    """
    Search workspace document chunks using vector cosine similarity.
    Enforces workspace isolation and optional document filtering.
    """
    if similarity_threshold is None:
        similarity_threshold = settings.SIMILARITY_THRESHOLD

    # 1. Generate query embedding
    query_vector = embedder.embed_text(query)

    # 2. Check database dialect
    is_postgres = db.bind.dialect.name == "postgresql" if db.bind else False

    if is_postgres:
        # Use native PostgreSQL pgvector cosine distance: embedding <=> query_vector
        distance_expr = DocumentChunk.embedding.cosine_distance(query_vector)
        stmt = (
            select(
                DocumentChunk,
                Document.filename,
                (1.0 - distance_expr).label("similarity"),
            )
            .join(Document, DocumentChunk.document_id == Document.id)
            .where(DocumentChunk.workspace_id == workspace_id)
        )
        if allowed_doc_ids:
            stmt = stmt.where(DocumentChunk.document_id.in_(allowed_doc_ids))

        stmt = stmt.order_by(distance_expr.asc()).limit(top_k * 2)
        result = await db.execute(stmt)
        rows = result.all()

        retrieved: List[RetrievedChunk] = []
        for chunk, filename, similarity in rows:
            sim = float(similarity)
            if sim >= similarity_threshold:
                retrieved.append(
                    RetrievedChunk(
                        chunk_id=chunk.id,
                        document_id=chunk.document_id,
                        filename=filename,
                        page_number=chunk.page_number,
                        chunk_index=chunk.chunk_index,
                        content=chunk.content,
                        similarity_score=round(sim, 4),
                    )
                )
                if len(retrieved) >= top_k:
                    break
        return retrieved

    else:
        # SQLite / in-memory fallback for test environments
        stmt = (
            select(DocumentChunk, Document.filename)
            .join(Document, DocumentChunk.document_id == Document.id)
            .where(DocumentChunk.workspace_id == workspace_id)
        )
        if allowed_doc_ids:
            stmt = stmt.where(DocumentChunk.document_id.in_(allowed_doc_ids))

        result = await db.execute(stmt)
        rows = result.all()

        scored: List[tuple[DocumentChunk, str, float]] = []
        for chunk, filename in rows:
            sim = compute_cosine_similarity(query_vector, chunk.embedding)
            if sim >= similarity_threshold:
                scored.append((chunk, filename, sim))

        # Sort by similarity descending
        scored.sort(key=lambda x: x[2], reverse=True)

        retrieved = []
        for chunk, filename, sim in scored[:top_k]:
            retrieved.append(
                RetrievedChunk(
                    chunk_id=chunk.id,
                    document_id=chunk.document_id,
                    filename=filename,
                    page_number=chunk.page_number,
                    chunk_index=chunk.chunk_index,
                    content=chunk.content,
                    similarity_score=round(sim, 4),
                )
            )
        return retrieved
