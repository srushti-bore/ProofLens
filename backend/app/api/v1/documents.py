"""
Document management and ingestion routes.
Handles PDF upload, PyMuPDF page extraction, metadata storage, and cascade deletion.
"""

import hashlib
from typing import List
from fastapi import APIRouter, File, HTTPException, UploadFile, status
from sqlalchemy import func, select
from sqlalchemy.orm import selectinload

from backend.app.api.deps import CurrentWorkspaceDep, DBDep
from backend.app.core.config import settings
from backend.app.models.chunk import DocumentChunk
from backend.app.models.document import Document, DocumentPage
from backend.app.schemas.document import (
    DocumentDetailResponse,
    DocumentPageResponse,
    DocumentResponse,
)
from backend.app.services.chunking.text_chunker import chunk_document_pages
from backend.app.services.embeddings.gemini_embedder import embedder
from backend.app.services.ingestion.pdf_extractor import extract_pdf_pages, validate_pdf_file
from backend.app.services.storage import (
    delete_document_file,
    is_supabase_storage,
    read_document_file,
    save_document_file,
)

router = APIRouter(prefix="/workspaces/{workspace_id}/documents", tags=["Documents"])


@router.post("/upload", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(
    workspace: CurrentWorkspaceDep,
    db: DBDep,
    file: UploadFile = File(..., description="PDF document file"),
) -> DocumentResponse:
    """
    Upload and ingest a PDF document.
    Validates file boundaries, extracts text page-by-page, and preserves provenance.
    """
    # 1. Check workspace document count limit
    count_stmt = select(func.count(Document.id)).where(Document.workspace_id == workspace.id)
    doc_count = (await db.execute(count_stmt)).scalar() or 0
    if doc_count >= settings.MAX_DOCUMENTS_PER_WORKSPACE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Workspace has reached the maximum limit of {settings.MAX_DOCUMENTS_PER_WORKSPACE} documents.",
        )

    # 2. Read file bytes
    file_bytes = await file.read()
    filename = file.filename or "untitled.pdf"

    # 3. Validate file format and size
    is_valid, validation_error = validate_pdf_file(
        filename=filename,
        file_bytes=file_bytes,
        max_size_mb=settings.MAX_FILE_SIZE_MB,
    )
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=validation_error,
        )

    # 4. Compute file hash
    file_hash = hashlib.sha256(file_bytes).hexdigest()

    # 5. Initialize Document record in database
    document = Document(
        workspace_id=workspace.id,
        filename=filename,
        file_size=len(file_bytes),
        file_hash=file_hash,
        mime_type="application/pdf",
        status="processing",
    )
    db.add(document)
    await db.flush()

    # 6. Save physical file to storage
    storage_path = save_document_file(
        workspace_id=workspace.id,
        document_id=document.id,
        file_bytes=file_bytes,
    )
    document.storage_path = storage_path

    # 7. Extract text and page provenance via PyMuPDF
    extraction = extract_pdf_pages(file_bytes)

    if not extraction.success:
        document.status = "failed"
        document.error_message = extraction.error_message
        await db.commit()
        await db.refresh(document)
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=f"PDF extraction failed: {extraction.error_message}",
        )

    # 8. Create page records preserving exact page_number
    for page_data in extraction.pages:
        page = DocumentPage(
            document_id=document.id,
            page_number=page_data.page_number,
            text_content=page_data.text_content,
            char_count=page_data.char_count,
        )
        db.add(page)

    # 9. Semantic chunking and vector embedding (Phase 3 pgvector pipeline)
    chunks_data = chunk_document_pages(
        extraction.pages,
        max_chunk_chars=settings.CHUNK_SIZE_TOKENS * 4,
        overlap_chars=settings.CHUNK_OVERLAP_TOKENS * 4,
    )
    if chunks_data:
        chunk_texts = [c.content for c in chunks_data]
        embeddings = embedder.embed_batch(chunk_texts)
        for c_data, emb in zip(chunks_data, embeddings):
            chunk_record = DocumentChunk(
                document_id=document.id,
                workspace_id=workspace.id,
                page_number=c_data.page_number,
                chunk_index=c_data.chunk_index,
                content=c_data.content,
                char_count=c_data.char_count,
                embedding=emb,
            )
            db.add(chunk_record)

    document.status = "completed"
    document.page_count = extraction.page_count
    await db.commit()
    await db.refresh(document)

    return DocumentResponse.model_validate(document)


@router.get("", response_model=List[DocumentResponse])
async def list_workspace_documents(
    workspace: CurrentWorkspaceDep,
    db: DBDep,
) -> List[DocumentResponse]:
    """List all documents belonging to the workspace."""
    stmt = (
        select(Document)
        .where(Document.workspace_id == workspace.id)
        .order_by(Document.created_at.desc())
    )
    result = await db.execute(stmt)
    documents = result.scalars().all()
    return [DocumentResponse.model_validate(doc) for doc in documents]


@router.get("/{document_id}", response_model=DocumentDetailResponse)
async def get_document_details(
    document_id: str,
    workspace: CurrentWorkspaceDep,
    db: DBDep,
) -> DocumentDetailResponse:
    """Retrieve document details with pages summary."""
    stmt = (
        select(Document)
        .options(selectinload(Document.pages))
        .where(
            Document.id == document_id,
            Document.workspace_id == workspace.id,
        )
    )
    result = await db.execute(stmt)
    document = result.scalar_one_or_none()

    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found in this workspace",
        )

    return DocumentDetailResponse.model_validate(document)


@router.get("/{document_id}/pages", response_model=List[DocumentPageResponse])
async def get_document_pages(
    document_id: str,
    workspace: CurrentWorkspaceDep,
    db: DBDep,
) -> List[DocumentPageResponse]:
    """Retrieve all extracted text pages for a document."""
    # Verify document belongs to workspace
    doc_stmt = select(Document.id).where(
        Document.id == document_id,
        Document.workspace_id == workspace.id,
    )
    doc_exists = (await db.execute(doc_stmt)).scalar_one_or_none()
    if not doc_exists:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found in this workspace",
        )

    stmt = (
        select(DocumentPage)
        .where(DocumentPage.document_id == document_id)
        .order_by(DocumentPage.page_number.asc())
    )
    result = await db.execute(stmt)
    pages = result.scalars().all()
    return [DocumentPageResponse.model_validate(p) for p in pages]


@router.get("/{document_id}/file")
async def get_document_file(
    document_id: str,
    workspace: CurrentWorkspaceDep,
    db: DBDep,
):
    """Serve the raw PDF file for in-browser preview or download from persistent storage."""
    import os
    from fastapi.responses import FileResponse, Response

    stmt = select(Document).where(
        Document.id == document_id,
        Document.workspace_id == workspace.id,
    )
    result = await db.execute(stmt)
    document = result.scalar_one_or_none()

    if not document or not document.storage_path:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document file not found",
        )

    # 1. Handle persistent Supabase Storage
    if is_supabase_storage(document.storage_path):
        file_bytes = read_document_file(document.storage_path)
        if not file_bytes:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document file not found in persistent cloud storage",
            )
        return Response(
            content=file_bytes,
            media_type="application/pdf",
            headers={"Content-Disposition": f'inline; filename="{document.filename}"'},
        )

    # 2. Handle local filesystem storage
    if not os.path.exists(document.storage_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document file not found on disk",
        )

    return FileResponse(
        path=document.storage_path,
        media_type="application/pdf",
        filename=document.filename,
    )


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(
    document_id: str,
    workspace: CurrentWorkspaceDep,
    db: DBDep,
) -> None:
    """
    Delete a document and cascade cleanups:
    Removes database document record, pages, and stored physical file.
    """
    stmt = select(Document).where(
        Document.id == document_id,
        Document.workspace_id == workspace.id,
    )
    result = await db.execute(stmt)
    document = result.scalar_one_or_none()

    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found in this workspace",
        )

    # Delete physical file
    delete_document_file(document.storage_path)

    # Delete database record (cascades to pages and future chunks)
    await db.delete(document)
    await db.commit()
