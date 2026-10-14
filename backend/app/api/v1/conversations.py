"""
Persistent Conversation Threads API routes for ProofLens AI.
Enables multi-turn continuous investigations under single conversation threads.
"""

from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query, Response, status
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.orm import selectinload

from backend.app.api.deps import CurrentUserDep, CurrentWorkspaceDep, DBDep
from backend.app.models.qa import Answer, Citation, Conversation, QueryRun
from backend.app.schemas.qa import (
    CitationResponse,
    ConversationDetailResponse,
    ConversationSummaryResponse,
    ConversationTurnResponse,
)

router = APIRouter(prefix="/workspaces/{workspace_id}/conversations", tags=["Conversations"])


class UpdateConversationRequest(BaseModel):
    title: str = Field(min_length=1, max_length=255)


@router.get("", response_model=List[ConversationSummaryResponse])
async def list_conversations(
    workspace: CurrentWorkspaceDep,
    current_user: CurrentUserDep,
    db: DBDep,
    query: Optional[str] = Query(None, description="Optional search filter for conversation title or text"),
    limit: int = Query(50, ge=1, le=100),
) -> List[ConversationSummaryResponse]:
    """
    List persistent conversation threads for the current user in this workspace.
    Sorted by updated_at descending.
    """
    conditions = [
        Conversation.workspace_id == workspace.id,
        Conversation.user_id == current_user.id,
    ]

    if query and query.strip():
        search_term = f"%{query.strip()}%"
        # Search conversation title or any of its query runs
        subq = (
            select(QueryRun.conversation_id)
            .where(
                QueryRun.conversation_id == Conversation.id,
                QueryRun.query_text.ilike(search_term),
            )
            .exists()
        )
        conditions.append((Conversation.title.ilike(search_term)) | subq)

    stmt = (
        select(Conversation)
        .options(
            selectinload(Conversation.query_runs).selectinload(QueryRun.answer)
        )
        .where(*conditions)
        .order_by(Conversation.updated_at.desc())
        .limit(limit)
    )
    convs = (await db.execute(stmt)).scalars().all()

    results: List[ConversationSummaryResponse] = []
    for c in convs:
        message_count = len(c.query_runs)
        last_preview = None
        if c.query_runs:
            last_run = c.query_runs[-1]
            if last_run.answer and last_run.answer.answer_text:
                last_preview = last_run.answer.answer_text[:120]
            else:
                last_preview = last_run.query_text[:120]

        results.append(
            ConversationSummaryResponse(
                id=c.id,
                workspace_id=c.workspace_id,
                title=c.title,
                created_at=c.created_at,
                updated_at=c.updated_at,
                message_count=message_count,
                last_message_preview=last_preview,
            )
        )

    return results


@router.get("/{conversation_id}", response_model=ConversationDetailResponse)
async def get_conversation(
    workspace: CurrentWorkspaceDep,
    current_user: CurrentUserDep,
    conversation_id: str,
    db: DBDep,
) -> ConversationDetailResponse:
    """
    Retrieve full multi-turn conversation detail with all questions, answers, and verified citations.
    """
    stmt = (
        select(Conversation)
        .options(
            selectinload(Conversation.query_runs)
            .selectinload(QueryRun.answer)
            .selectinload(Answer.citations)
        )
        .where(
            Conversation.id == conversation_id,
            Conversation.workspace_id == workspace.id,
            Conversation.user_id == current_user.id,
        )
    )
    conv = (await db.execute(stmt)).scalar_one_or_none()
    if not conv:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found or access denied.",
        )

    turns: List[ConversationTurnResponse] = []
    for qr in conv.query_runs:
        ans = qr.answer
        citations_list = [
            CitationResponse(
                id=cit.id,
                chunk_id=cit.chunk_id,
                document_id=cit.document_id,
                filename=cit.filename,
                document_name=cit.filename,
                page_number=cit.page_number,
                excerpt=cit.excerpt,
                is_validated=cit.is_validated,
            )
            for cit in (ans.citations if ans else [])
        ]

        turns.append(
            ConversationTurnResponse(
                query_id=qr.id,
                question=qr.query_text,
                answer=ans.answer_text if ans else "No answer recorded.",
                status=ans.status if ans else "supported",
                confidence_score=ans.confidence_score if ans else 0.0,
                retrieved_chunks_count=ans.retrieved_chunks_count if ans else 0,
                citations=citations_list,
                created_at=qr.created_at,
            )
        )

    return ConversationDetailResponse(
        id=conv.id,
        workspace_id=conv.workspace_id,
        title=conv.title,
        created_at=conv.created_at,
        updated_at=conv.updated_at,
        turns=turns,
    )


@router.delete("/{conversation_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_conversation(
    workspace: CurrentWorkspaceDep,
    current_user: CurrentUserDep,
    conversation_id: str,
    db: DBDep,
):
    """
    Delete a conversation thread and all its query runs, answers, and citations.
    """
    stmt = select(Conversation).where(
        Conversation.id == conversation_id,
        Conversation.workspace_id == workspace.id,
        Conversation.user_id == current_user.id,
    )
    conv = (await db.execute(stmt)).scalar_one_or_none()
    if not conv:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found or access denied.",
        )

    await db.delete(conv)
    await db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.patch("/{conversation_id}", response_model=ConversationSummaryResponse)
async def update_conversation(
    workspace: CurrentWorkspaceDep,
    current_user: CurrentUserDep,
    conversation_id: str,
    request: UpdateConversationRequest,
    db: DBDep,
) -> ConversationSummaryResponse:
    """
    Update a conversation's title.
    """
    stmt = (
        select(Conversation)
        .options(selectinload(Conversation.query_runs))
        .where(
            Conversation.id == conversation_id,
            Conversation.workspace_id == workspace.id,
            Conversation.user_id == current_user.id,
        )
    )
    conv = (await db.execute(stmt)).scalar_one_or_none()
    if not conv:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found or access denied.",
        )

    conv.title = request.title.strip()
    await db.commit()
    await db.refresh(conv)

    return ConversationSummaryResponse(
        id=conv.id,
        workspace_id=conv.workspace_id,
        title=conv.title,
        created_at=conv.created_at,
        updated_at=conv.updated_at,
        message_count=len(conv.query_runs),
    )
