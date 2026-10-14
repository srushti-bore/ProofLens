"""
Pydantic schemas for Claim Verification, Cross-Document Comparison, and Quality Analytics.
"""

from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field, model_validator


class ClaimCitationResponse(BaseModel):
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


class ClaimVerifyRequest(BaseModel):
    claim: str = Field(min_length=1, description="Factual claim or hypothesis to verify")
    document_ids: Optional[List[str]] = Field(default=None, description="Optional document IDs to scope verification")


class ClaimVerifyResponse(BaseModel):
    claim_id: str
    claim: str
    status: str  # Supported, Partially Supported, Contradicted, Insufficient Evidence
    explanation: str
    confidence_score: float
    citations: List[ClaimCitationResponse] = []
    created_at: datetime


class CompareRequest(BaseModel):
    topic: str = Field(min_length=1, description="Subject or question to compare across documents")
    document_ids: List[str] = Field(
        min_length=2,
        description="List of at least two document IDs to compare",
    )


class DocumentFinding(BaseModel):
    document_id: str
    filename: str
    document_name: Optional[str] = None
    summary: str
    findings: Optional[str] = None
    citations: List[ClaimCitationResponse] = []
    page_citations: Optional[List[int]] = None

    @model_validator(mode="after")
    def sync_finding_fields(self):
        if not self.document_name:
            self.document_name = self.filename
        if not self.findings:
            self.findings = self.summary
        if self.page_citations is None:
            self.page_citations = [c.page_number for c in self.citations]
        return self


class CompareResponse(BaseModel):
    topic: str
    findings_per_document: List[DocumentFinding] = []
    findings: Optional[List[DocumentFinding]] = None
    agreements: List[str] = []
    consensus: Optional[List[str]] = None
    differences: List[str] = []
    divergences: Optional[List[str]] = None
    scope_limitations: List[str] = []
    scope_mismatches: Optional[List[str]] = None
    synthesis_summary: str

    @model_validator(mode="after")
    def sync_comparison_aliases(self):
        if self.findings is None:
            self.findings = self.findings_per_document
        if self.consensus is None:
            self.consensus = self.agreements
        if self.divergences is None:
            self.divergences = self.differences
        if self.scope_mismatches is None:
            self.scope_mismatches = self.scope_limitations
        return self


class WorkspaceAnalyticsResponse(BaseModel):
    total_documents: int
    total_pages: int
    total_chunks: int
    total_queries: int
    supported_answers_count: int
    insufficient_evidence_count: int
    supported_rate: float
    abstention_rate: float
    total_citations: int
    citation_validity_rate: float
