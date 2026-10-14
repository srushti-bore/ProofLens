"""
Investigation History, Audit Trail, and Report Export API routes.
Enables review of previous Q&A and claim verification sessions, and citation-linked export.
"""

from datetime import datetime, timezone
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query, Response, status
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from backend.app.api.deps import CurrentWorkspaceDep, DBDep
from backend.app.models.claims import ClaimVerification
from backend.app.models.qa import Answer, QueryRun
from backend.app.schemas.history import (
    HistoryItemResponse,
    HistoryListResponse,
    ReportExportResponse,
)
from backend.app.services.reports.report_generator import generate_markdown_investigation_report

router = APIRouter(prefix="/workspaces/{workspace_id}", tags=["Investigation History & Reports"])


@router.get("/history", response_model=HistoryListResponse)
async def get_workspace_history(
    workspace: CurrentWorkspaceDep,
    db: DBDep,
    limit: int = Query(50, ge=1, le=200),
    query: Optional[str] = Query(None, description="Search term for question, answer, claim, or explanation"),
) -> HistoryListResponse:
    """
    Retrieve chronological investigation history (Q&A sessions and Claim verifications).
    Strictly isolated to current workspace. Supports optional server-side search query.
    """
    qa_conditions = [QueryRun.workspace_id == workspace.id]
    if query and query.strip():
        search_term = f"%{query.strip()}%"
        qa_conditions.append(
            (QueryRun.query_text.ilike(search_term)) | (Answer.answer_text.ilike(search_term))
        )

    # 1. Fetch Q&A query runs
    qa_stmt = (
        select(QueryRun)
        .outerjoin(Answer, QueryRun.id == Answer.query_run_id)
        .options(selectinload(QueryRun.answer).selectinload(Answer.citations))
        .where(*qa_conditions)
        .order_by(QueryRun.created_at.desc())
        .limit(limit)
    )
    qa_runs = (await db.execute(qa_stmt)).scalars().all()

    # 2. Fetch Claim verifications
    claim_conditions = [ClaimVerification.workspace_id == workspace.id]
    if query and query.strip():
        search_term = f"%{query.strip()}%"
        claim_conditions.append(
            (ClaimVerification.claim_text.ilike(search_term)) | (ClaimVerification.explanation.ilike(search_term))
        )
    claim_stmt = (
        select(ClaimVerification)
        .options(selectinload(ClaimVerification.citations))
        .where(*claim_conditions)
        .order_by(ClaimVerification.created_at.desc())
        .limit(limit)
    )
    claims = (await db.execute(claim_stmt)).scalars().all()

    items: List[HistoryItemResponse] = []

    # Map Q&A runs
    for qr in qa_runs:
        ans = qr.answer
        citations_list = [
            {
                "id": c.id,
                "chunk_id": c.chunk_id,
                "document_id": c.document_id,
                "document_name": c.filename,
                "filename": c.filename,
                "page_number": c.page_number,
                "excerpt": c.excerpt,
                "is_validated": c.is_validated,
            }
            for c in (ans.citations if ans else [])
        ]
        items.append(
            HistoryItemResponse(
                id=qr.id,
                item_type="qa",
                title=qr.query_text,
                status=ans.status if ans else "pending",
                confidence_score=ans.confidence_score if ans else 0.0,
                citations_count=len(citations_list),
                created_at=qr.created_at,
                summary=ans.answer_text if ans else "No answer generated.",
                details={
                    "answer": ans.answer_text if ans else "",
                    "citations": citations_list,
                },
            )
        )

    # Map Claim verifications
    for cv in claims:
        citations_list = [
            {
                "id": c.id,
                "chunk_id": c.chunk_id,
                "document_id": c.document_id,
                "document_name": c.filename,
                "filename": c.filename,
                "page_number": c.page_number,
                "excerpt": c.excerpt,
            }
            for c in cv.citations
        ]
        items.append(
            HistoryItemResponse(
                id=cv.id,
                item_type="claim",
                title=cv.claim_text,
                status=cv.status,
                confidence_score=cv.confidence_score,
                citations_count=len(citations_list),
                created_at=cv.created_at,
                summary=cv.explanation,
                details={
                    "explanation": cv.explanation,
                    "citations": citations_list,
                },
            )
        )

    # Sort merged list by created_at descending (safely normalize naive vs aware)
    def _to_utc(dt):
        if dt is None:
            return datetime.min.replace(tzinfo=timezone.utc)
        if dt.tzinfo is None:
            return dt.replace(tzinfo=timezone.utc)
        return dt

    items.sort(key=lambda x: _to_utc(x.created_at), reverse=True)

    return HistoryListResponse(
        workspace_id=workspace.id,
        total_items=len(items),
        items=items[:limit],
    )


@router.get("/reports/export")
async def export_workspace_report(
    workspace: CurrentWorkspaceDep,
    db: DBDep,
    download: bool = Query(False, description="Whether to trigger file download"),
):
    """
    Export comprehensive investigation summary report in Markdown format.
    Guarantees page-level traceability and source links.
    """
    report_md = await generate_markdown_investigation_report(db, workspace)

    if download:
        filename = f"prooflens_investigation_report_{workspace.name.lower().replace(' ', '_')}.md"
        return Response(
            content=report_md,
            media_type="text/markdown",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        )

    return ReportExportResponse(
        workspace_id=workspace.id,
        workspace_name=workspace.name,
        generated_at=datetime.now(timezone.utc),
        format="markdown",
        markdown_content=report_md,
    )
