"""
Grounded Question Answering and Citation Verification API routes.
Connects retrieval, grounded synthesis, citation validation, and audit recording.
"""

from datetime import datetime, timezone
from fastapi import APIRouter
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from backend.app.api.deps import CurrentUserDep, CurrentWorkspaceDep, DBDep
from backend.app.models.qa import Answer, Citation, Conversation, QueryRun
from backend.app.schemas.qa import (
    AnswerResponse,
    AskQuestionRequest,
    CitationResponse,
    EvidenceExcerptResponse,
)
from backend.app.services.citation.citation_validator import validate_citations
from backend.app.services.generation.gemini_generator import qa_generator
from backend.app.services.retrieval.retrieval_service import search_workspace_chunks

router = APIRouter(prefix="/workspaces/{workspace_id}/qa", tags=["Question Answering"])


@router.post("/ask", response_model=AnswerResponse)
async def ask_question(
    workspace: CurrentWorkspaceDep,
    current_user: CurrentUserDep,
    request: AskQuestionRequest,
    db: DBDep,
) -> AnswerResponse:
    """
    Ask a natural language question grounded in the workspace's uploaded documents.
    Retrieves evidence passages, generates an answer, validates citations, and appends to persistent conversation thread.
    """
    # 1. Resolve or create persistent conversation thread
    conv = None
    if request.conversation_id:
        conv_stmt = select(Conversation).where(
            Conversation.id == request.conversation_id,
            Conversation.workspace_id == workspace.id,
            Conversation.user_id == current_user.id,
        )
        conv = (await db.execute(conv_stmt)).scalar_one_or_none()

    if not conv:
        # Create new conversation thread using first query as title (max 80 chars)
        clean_title = request.question.strip()
        if len(clean_title) > 80:
            clean_title = clean_title[:77] + "..."
        conv = Conversation(
            workspace_id=workspace.id,
            user_id=current_user.id,
            title=clean_title,
        )
        db.add(conv)
        await db.flush()
    else:
        conv.updated_at = datetime.now(timezone.utc)

    # 2. Record QueryRun in database associated with conversation
    query_run = QueryRun(
        workspace_id=workspace.id,
        user_id=current_user.id,
        conversation_id=conv.id,
        query_text=request.question,
    )
    db.add(query_run)
    await db.flush()

    # 2. Retrieve candidate evidence chunks
    retrieved_chunks = await search_workspace_chunks(
        db=db,
        workspace_id=workspace.id,
        query=request.question,
        top_k=request.top_k or 5,
        similarity_threshold=request.similarity_threshold,
        allowed_doc_ids=request.document_ids,
    )

    # 3. Synthesize grounded answer or abstain
    synthesized = qa_generator.generate_grounded_answer(
        question=request.question,
        retrieved_chunks=retrieved_chunks,
    )

    # 4. Validate citation references against retrieved chunks
    validated_citations = validate_citations(
        raw_citations=synthesized.raw_citations,
        retrieved_chunks=retrieved_chunks,
    )

    # 5. Persist Answer record
    answer = Answer(
        query_run_id=query_run.id,
        answer_text=synthesized.answer_text,
        status=synthesized.status,
        confidence_score=0.0 if synthesized.status == "insufficient_evidence" else synthesized.confidence_score,
        retrieved_chunks_count=len(retrieved_chunks),
    )
    db.add(answer)
    await db.flush()

    # 6. Persist Citation records
    db_citations = []
    for vc in validated_citations:
        citation_record = Citation(
            answer_id=answer.id,
            chunk_id=vc.chunk_id,
            document_id=vc.document_id,
            filename=vc.filename,
            page_number=vc.page_number,
            excerpt=vc.excerpt,
            is_validated=vc.is_validated,
        )
        db.add(citation_record)
        db_citations.append(citation_record)

    await db.commit()
    await db.refresh(answer)

    citation_responses = [
        CitationResponse(
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

    evidence_excerpts = [
        EvidenceExcerptResponse(
            chunk_id=c.chunk_id,
            document_id=c.document_id,
            filename=c.filename,
            page_number=c.page_number,
            content=c.content,
            similarity_score=c.similarity_score,
        )
        for c in retrieved_chunks
    ]

    return AnswerResponse(
        query_id=query_run.id,
        conversation_id=conv.id,
        conversation_title=conv.title,
        question=request.question,
        answer=answer.answer_text,
        status=answer.status,
        confidence_score=answer.confidence_score,
        retrieved_chunks_count=answer.retrieved_chunks_count,
        citations=citation_responses,
        evidence_excerpts=evidence_excerpts,
        created_at=answer.created_at,
    )
