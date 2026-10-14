"""
Claim Verification, Cross-Document Comparison, and Quality Analytics API routes.
"""

from typing import List
from fastapi import APIRouter, HTTPException, status
from sqlalchemy import func, select

from backend.app.api.deps import CurrentUserDep, CurrentWorkspaceDep, DBDep
from backend.app.models.chunk import DocumentChunk
from backend.app.models.claims import ClaimCitation, ClaimVerification
from backend.app.models.document import Document, DocumentPage
from backend.app.models.qa import Answer, Citation, QueryRun
from backend.app.schemas.claims import (
    ClaimCitationResponse,
    ClaimVerifyRequest,
    ClaimVerifyResponse,
    CompareRequest,
    CompareResponse,
    DocumentFinding,
    WorkspaceAnalyticsResponse,
)
from backend.app.services.citation.citation_validator import validate_citations
from backend.app.services.claims.claim_verifier import claim_verifier
from backend.app.services.comparison.doc_comparator import compare_documents
from backend.app.services.retrieval.retrieval_service import search_workspace_chunks

router = APIRouter(prefix="/workspaces/{workspace_id}", tags=["Intelligence & Analytics"])


@router.post("/claims/verify", response_model=ClaimVerifyResponse)
async def verify_claim_endpoint(
    workspace: CurrentWorkspaceDep,
    current_user: CurrentUserDep,
    request: ClaimVerifyRequest,
    db: DBDep,
) -> ClaimVerifyResponse:
    """
    Formally evaluate a factual claim against workspace evidence.
    Returns strictly one of: Supported, Partially Supported, Contradicted, or Insufficient Evidence.
    """
    # 1. Retrieve candidate evidence chunks
    retrieved_chunks = await search_workspace_chunks(
        db=db,
        workspace_id=workspace.id,
        query=request.claim,
        top_k=5,
        allowed_doc_ids=request.document_ids,
    )

    # 2. Evaluate claim
    verification = claim_verifier.verify_claim(
        claim=request.claim,
        retrieved_chunks=retrieved_chunks,
    )

    # 3. Validate citations against actual retrieved chunks
    validated_cits = validate_citations(
        raw_citations=verification.raw_citations,
        retrieved_chunks=retrieved_chunks,
    )

    # 4. Save ClaimVerification record
    claim_record = ClaimVerification(
        workspace_id=workspace.id,
        user_id=current_user.id,
        claim_text=request.claim,
        status=verification.status,
        explanation=verification.explanation,
        confidence_score=verification.confidence_score,
    )
    db.add(claim_record)
    await db.flush()

    # 5. Save ClaimCitation records
    db_citations = []
    for vc in validated_cits:
        c_rec = ClaimCitation(
            claim_verification_id=claim_record.id,
            chunk_id=vc.chunk_id,
            document_id=vc.document_id,
            filename=vc.filename,
            page_number=vc.page_number,
            excerpt=vc.excerpt,
            is_validated=vc.is_validated,
        )
        db.add(c_rec)
        db_citations.append(c_rec)

    await db.commit()
    await db.refresh(claim_record)

    citation_responses = [
        ClaimCitationResponse(
            id=c.id,
            chunk_id=c.chunk_id,
            document_id=c.document_id,
            filename=c.filename,
            page_number=c.page_number,
            excerpt=c.excerpt,
            is_validated=c.is_validated,
        )
        for c in db_citations
    ]

    return ClaimVerifyResponse(
        claim_id=claim_record.id,
        claim=claim_record.claim_text,
        status=claim_record.status,
        explanation=claim_record.explanation,
        confidence_score=claim_record.confidence_score,
        citations=citation_responses,
        created_at=claim_record.created_at,
    )


@router.post("/comparison/compare", response_model=CompareResponse)
async def compare_documents_endpoint(
    workspace: CurrentWorkspaceDep,
    request: CompareRequest,
    db: DBDep,
) -> CompareResponse:
    """
    Cross-compare evidence across 2 or more selected documents.
    Generates findings per document, agreements, differences, and scope limitations.
    """
    if len(request.document_ids) < 2:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least two document IDs are required for cross-document comparison.",
        )

    # Verify all document IDs belong to the current workspace
    doc_stmt = select(Document.id).where(
        Document.id.in_(request.document_ids),
        Document.workspace_id == workspace.id,
    )
    existing_ids = (await db.execute(doc_stmt)).scalars().all()
    if len(existing_ids) < len(request.document_ids):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="One or more specified document IDs do not exist in this workspace.",
        )

    result = await compare_documents(
        db=db,
        workspace_id=workspace.id,
        topic=request.topic,
        document_ids=request.document_ids,
    )

    finding_responses = []
    for f in result.findings_per_document:
        finding_responses.append(
            DocumentFinding(
                document_id=f.document_id,
                filename=f.filename,
                summary=f.summary,
                citations=[
                    ClaimCitationResponse(
                        id=c.chunk_id,
                        chunk_id=c.chunk_id,
                        document_id=c.document_id,
                        filename=c.filename,
                        page_number=c.page_number,
                        excerpt=c.excerpt,
                        is_validated=c.is_validated,
                    )
                    for c in f.citations
                ],
            )
        )

    return CompareResponse(
        topic=result.topic,
        findings_per_document=finding_responses,
        agreements=result.agreements,
        differences=result.differences,
        scope_limitations=result.scope_limitations,
        synthesis_summary=result.synthesis_summary,
    )


@router.get("/analytics", response_model=WorkspaceAnalyticsResponse)
async def get_workspace_analytics(
    workspace: CurrentWorkspaceDep,
    db: DBDep,
) -> WorkspaceAnalyticsResponse:
    """
    Quality and evaluation analytics for the current workspace.
    Computes grounded answer rates, abstention rates, and citation validity metrics.
    """
    # 1. Total documents
    doc_count = (
        await db.execute(
            select(func.count(Document.id)).where(Document.workspace_id == workspace.id)
        )
    ).scalar() or 0

    # 2. Total pages
    pages_count = (
        await db.execute(
            select(func.count(DocumentPage.id))
            .join(Document, DocumentPage.document_id == Document.id)
            .where(Document.workspace_id == workspace.id)
        )
    ).scalar() or 0

    # 3. Total chunks
    chunks_count = (
        await db.execute(
            select(func.count(DocumentChunk.id)).where(DocumentChunk.workspace_id == workspace.id)
        )
    ).scalar() or 0

    # 4. Total queries
    query_count = (
        await db.execute(
            select(func.count(QueryRun.id)).where(QueryRun.workspace_id == workspace.id)
        )
    ).scalar() or 0

    # 5. Answer statuses
    answers_stmt = (
        select(Answer.status, func.count(Answer.id))
        .join(QueryRun, Answer.query_run_id == QueryRun.id)
        .where(QueryRun.workspace_id == workspace.id)
        .group_by(Answer.status)
    )
    status_counts = dict((await db.execute(answers_stmt)).all())
    supported_cnt = status_counts.get("supported", 0)
    abstain_cnt = status_counts.get("insufficient_evidence", 0)

    supported_rate = round(supported_cnt / query_count, 4) if query_count > 0 else 0.0
    abstain_rate = round(abstain_cnt / query_count, 4) if query_count > 0 else 0.0

    # 6. Citations validity
    citations_count = (
        await db.execute(
            select(func.count(Citation.id))
            .join(Answer, Citation.answer_id == Answer.id)
            .join(QueryRun, Answer.query_run_id == QueryRun.id)
            .where(QueryRun.workspace_id == workspace.id)
        )
    ).scalar() or 0

    valid_citations_count = (
        await db.execute(
            select(func.count(Citation.id))
            .join(Answer, Citation.answer_id == Answer.id)
            .join(QueryRun, Answer.query_run_id == QueryRun.id)
            .where(QueryRun.workspace_id == workspace.id, Citation.is_validated == True)
        )
    ).scalar() or 0

    validity_rate = (
        round(valid_citations_count / citations_count, 4) if citations_count > 0 else 1.0
    )

    return WorkspaceAnalyticsResponse(
        total_documents=doc_count,
        total_pages=pages_count,
        total_chunks=chunks_count,
        total_queries=query_count,
        supported_answers_count=supported_cnt,
        insufficient_evidence_count=abstain_cnt,
        supported_rate=supported_rate,
        abstention_rate=abstain_rate,
        total_citations=citations_count,
        citation_validity_rate=validity_rate,
    )
