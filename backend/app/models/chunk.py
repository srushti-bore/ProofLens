"""
SQLAlchemy database model for DocumentChunk with cross-dialect vector storage.
Supports native pgvector Vector(768) on PostgreSQL and JSON fallback on SQLite.
"""

import uuid
from datetime import datetime, timezone
from typing import List, Optional
from pgvector.sqlalchemy import Vector
from sqlalchemy import JSON, DateTime, ForeignKey, Integer, String, Text, TypeDecorator
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.core.database import Base


class VectorColumn(TypeDecorator):
    """
    Cross-dialect vector type:
    - On PostgreSQL: compiles to pgvector Vector(dim)
    - On SQLite (testing): compiles to JSON storing a list of floats
    """
    impl = Text
    cache_ok = True
    comparator_factory = Vector.comparator_factory

    def __init__(self, dim: int = 768, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.dim = dim

    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql":
            return dialect.type_descriptor(Vector(self.dim))
        return dialect.type_descriptor(JSON())

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        if dialect.name == "postgresql":
            return value
        return list(value)

    def process_result_value(self, value, dialect):
        if value is None:
            return None
        return list(value)


class DocumentChunk(Base):
    __tablename__ = "document_chunks"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        index=True,
    )
    document_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("documents.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    workspace_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("workspaces.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    page_number: Mapped[int] = mapped_column(Integer, nullable=False, index=True)  # 1-indexed
    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False)  # 0-indexed within doc
    content: Mapped[str] = mapped_column(Text, nullable=False)
    embedding: Mapped[List[float]] = mapped_column(VectorColumn(dim=768), nullable=False)
    char_count: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    document: Mapped["Document"] = relationship("Document", back_populates="chunks")
