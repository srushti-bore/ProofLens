"""
Semantic retrieval API routes.
Enforces workspace boundaries and vector similarity candidate filtering.
"""

from fastapi import APIRouter

from backend.app.api.deps import CurrentWorkspaceDep, DBDep
from backend.app.schemas.retrieval import (
    QueryRequest,
    RetrievalResponse,
    RetrievedChunkResponse,
)
from backend.app.services.retrieval.retrieval_service import search_workspace_chunks

router = APIRouter(prefix="/workspaces/{workspace_id}/retrieval", tags=["Retrieval"])


@router.post("/search", response_model=RetrievalResponse)
async def search_workspace_documents(
    workspace: CurrentWorkspaceDep,
    query_in: QueryRequest,
    db: DBDep,
) -> RetrievalResponse:
    """
    Search workspace documents using semantic vector similarity.
    Retrieves top-k relevant chunks exceeding the similarity threshold.
    """
    chunks = await search_workspace_chunks(
        db=db,
        workspace_id=workspace.id,
        query=query_in.query,
        top_k=query_in.top_k or 5,
        similarity_threshold=query_in.similarity_threshold,
        allowed_doc_ids=query_in.document_ids,
    )

    chunk_responses = [
        RetrievedChunkResponse(
            chunk_id=c.chunk_id,
            document_id=c.document_id,
            filename=c.filename,
            page_number=c.page_number,
            chunk_index=c.chunk_index,
            content=c.content,
            similarity_score=c.similarity_score,
        )
        for c in chunks
    ]

    return RetrievalResponse(
        query=query_in.query,
        retrieved_count=len(chunk_responses),
        chunks=chunk_responses,
    )
