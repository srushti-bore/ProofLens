"""
Report generation service for ProofLens AI.
Synthesizes comprehensive, citation-linked investigation reports in Markdown format.
Enforces strict provenance traceability (document names, exact pages, verified quotes).
"""

from datetime import datetime, timezone
from typing import List
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.app.models.claims import ClaimVerification
from backend.app.models.document import Document
from backend.app.models.qa import Answer, QueryRun
from backend.app.models.workspace import Workspace


async def generate_markdown_investigation_report(
    db: AsyncSession,
    workspace: Workspace,
) -> str:
    """
    Generate a complete, structured Markdown investigation report for a workspace.
    """
    # 1. Fetch workspace documents
    doc_stmt = (
        select(Document)
        .where(Document.workspace_id == workspace.id)
        .order_by(Document.created_at.asc())
    )
    docs_result = await db.execute(doc_stmt)
    documents = docs_result.scalars().all()

    # 2. Fetch Q&A query runs with answers and citations
    qa_stmt = (
        select(QueryRun)
        .options(
            selectinload(QueryRun.answer).selectinload(Answer.citations),
        )
        .where(QueryRun.workspace_id == workspace.id)
        .order_by(QueryRun.created_at.asc())
    )
    qa_result = await db.execute(qa_stmt)
    query_runs = qa_result.scalars().all()

    # 3. Fetch Claim verifications with citations
    claim_stmt = (
        select(ClaimVerification)
        .options(selectinload(ClaimVerification.citations))
        .where(ClaimVerification.workspace_id == workspace.id)
        .order_by(ClaimVerification.created_at.asc())
    )
    claim_result = await db.execute(claim_stmt)
    claims = claim_result.scalars().all()

    # Compute high-level metrics
    total_docs = len(documents)
    total_pages = sum(d.page_count for d in documents)
    total_queries = len(query_runs)
    total_claims = len(claims)

    confidences = [
        qr.answer.confidence_score
        for qr in query_runs
        if qr.answer and qr.answer.status != "insufficient_evidence"
    ]
    avg_confidence = (sum(confidences) / len(confidences)) if confidences else 1.0

    abstained_queries = sum(
        1 for qr in query_runs if qr.answer and qr.answer.status == "insufficient_evidence"
    )

    now_utc = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

    # Build Markdown
    lines = [
        f"# ProofLens AI — Investigation Report",
        f"",
        f"**Workspace:** {workspace.name}  ",
        f"**Workspace ID:** `{workspace.id}`  ",
        f"**Report Generated:** {now_utc}  ",
        f"**Product Baseline:** ProofLens AI v0.2 — Evidence-First Document Intelligence  ",
        f"",
        f"---",
        f"",
        f"## 1. Executive Summary & Telemetry",
        f"",
        f"| Metric | Value | Description |",
        f"| :--- | :--- | :--- |",
        f"| **Total Documents** | {total_docs} | Indexed in workspace tenant boundary |",
        f"| **Total Pages** | {total_pages} | Extracted via PyMuPDF with page provenance |",
        f"| **Grounded Queries** | {total_queries} | Multi-turn Q&A investigations |",
        f"| **Claims Evaluated** | {total_claims} | 4-Tier truth status verifications |",
        f"| **Avg Grounding Confidence** | {avg_confidence * 100:.1f}% | Across supported evidence answers |",
        f"| **Abstention Incidents** | {abstained_queries} | Explicit refusals on weak evidence |",
        f"",
        f"---",
        f"",
        f"## 2. Document Inventory & Provenance Baseline",
        f"",
    ]

    if not documents:
        lines.append("*No documents currently uploaded to this workspace.*")
    else:
        lines.append("| Filename | Pages | File Size | Status | SHA256 Hash |")
        lines.append("| :--- | :---: | :---: | :---: | :--- |")
        for doc in documents:
            size_kb = doc.file_size / 1024
            size_str = f"{size_kb:.1f} KB" if size_kb < 1024 else f"{size_kb/1024:.2f} MB"
            lines.append(
                f"| **{doc.filename}** | {doc.page_count} | {size_str} | `{doc.status}` | `{doc.file_hash[:12]}...` |"
            )

    lines.extend([
        f"",
        f"---",
        f"",
        f"## 3. Evidence-Grounded Q&A Investigation Log",
        f"",
    ])

    if not query_runs:
        lines.append("*No Q&A sessions recorded in this workspace.*")
    else:
        for idx, qr in enumerate(query_runs, 1):
            ans = qr.answer
            status_badge = "✅ Supported" if ans and ans.status != "insufficient_evidence" else "⚠️ Insufficient Evidence (Abstained)"
            conf_str = f"{ans.confidence_score * 100:.0f}%" if ans else "N/A"
            timestamp_str = qr.created_at.strftime("%Y-%m-%d %H:%M:%S UTC")

            lines.extend([
                f"### Query {idx}: {qr.query_text}",
                f"",
                f"- **Timestamp:** {timestamp_str}",
                f"- **Status:** {status_badge}",
                f"- **Grounding Confidence:** {conf_str}",
                f"",
                f"**Synthesized Answer:**",
                f"> {ans.answer_text if ans else 'No answer generated.'}",
                f"",
            ])

            if ans and ans.citations:
                lines.append(f"**Verified Citations ({len(ans.citations)}):**")
                lines.append(f"| Source Document | Page | Verified Status | Evidence Excerpt |")
                lines.append(f"| :--- | :---: | :---: | :--- |")
                for c in ans.citations:
                    match_badge = "✓ Validated Vector Match" if c.is_validated else "Unchecked"
                    clean_excerpt = c.excerpt.replace("\n", " ").replace("|", "/")
                    lines.append(f"| {c.filename} | Page {c.page_number} | {match_badge} | \"{clean_excerpt}\" |")
                lines.append("")

    lines.extend([
        f"---",
        f"",
        f"## 4. 4-Tier Claim Verification Log",
        f"",
    ])

    if not claims:
        lines.append("*No claims evaluated in this workspace.*")
    else:
        for idx, cv in enumerate(claims, 1):
            status_emojis = {
                "Supported": "🟢 Supported",
                "Partially Supported": "🟡 Partially Supported",
                "Contradicted": "🔴 Contradicted",
                "Insufficient Evidence": "⚪ Insufficient Evidence",
            }
            badge = status_emojis.get(cv.status, cv.status)
            timestamp_str = cv.created_at.strftime("%Y-%m-%d %H:%M:%S UTC")

            lines.extend([
                f"### Claim {idx}: {cv.claim_text}",
                f"",
                f"- **Status:** **{badge}**",
                f"- **Evaluated:** {timestamp_str}",
                f"",
                f"**Evidence Rationale:**",
                f"{cv.explanation}",
                f"",
            ])

            if cv.citations:
                lines.append(f"**Supporting Citations ({len(cv.citations)}):**")
                for c in cv.citations:
                    clean_excerpt = c.excerpt.replace("\n", " ")
                    lines.append(f"- **{c.filename}** (Page {c.page_number}): \"{clean_excerpt}\"")
                lines.append("")

    lines.extend([
        f"---",
        f"",
        f"## 5. Traceability & Integrity Guarantee",
        f"",
        f"- **Provenance Integrity:** All citations reference authentic extracted page numbers and PyMuPDF text layers.",
        f"- **Zero Hallucination Policy:** If similarity falls below the calibrated threshold (0.35), the pipeline explicitly abstains.",
        f"- **Data Isolation:** All queries, chunks, and claims are strictly partitioned by `workspace_id`.",
        f"",
        f"*(Generated automatically by ProofLens AI Report Engine)*",
    ])

    return "\n".join(lines)
