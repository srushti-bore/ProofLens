"""
Pydantic schemas for Question Answering, Grounded Synthesis, and Verified Citations.
"""

from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field, model_validator


class AskQuestionRequest(BaseModel):
    question: str = Field(min_length=1, description="Natural language question to ask over documents")
    top_k: Optional[int] = Field(default=5, ge=1, le=20, description="Number of evidence chunks to retrieve")
    similarity_threshold: Optional[float] = Field(default=None, ge=0.0, le=1.0, description="Optional minimum similarity score")
    document_ids: Optional[List[str]] = Field(default=None, description="Optional document IDs to scope search")

    @model_validator(mode="before")
    @classmethod
    def accept_query_as_question(cls, data):
        if isinstance(data, dict):
            if "query" in data and "question" not in data:
                data["question"] = data["query"]
        return data


class CitationResponse(BaseModel):
    id: str
    chunk_id: str
    document_id: str
    filename: str
    document_name: Optional[str] = None
    page_number: int
    excerpt: str
    is_validated: bool

    @model_validator(mode="after")
    def sync_document_name(self):
        if not self.document_name:
            self.document_name = self.filename
        return self

    model_config = {"from_attributes": True}


class EvidenceExcerptResponse(BaseModel):
    chunk_id: str
    document_id: str
    filename: str
    page_number: int
    content: str
    similarity_score: float


class AnswerResponse(BaseModel):
    query_id: str
    question: str
    answer: str
    status: str  # supported, partially_supported, insufficient_evidence
    confidence_score: float
    retrieved_chunks_count: int
    citations: List[CitationResponse] = []
    evidence_excerpts: List[EvidenceExcerptResponse] = []
    created_at: datetime
