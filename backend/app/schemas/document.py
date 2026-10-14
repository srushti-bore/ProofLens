"""
Pydantic schemas for Document and DocumentPage representations.
"""

from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field


class DocumentPageResponse(BaseModel):
    id: str
    document_id: str
    page_number: int
    text_content: str
    char_count: int
    created_at: datetime

    model_config = {"from_attributes": True}


class DocumentResponse(BaseModel):
    id: str
    workspace_id: str
    filename: str
    file_size: int
    file_hash: Optional[str] = None
    mime_type: str
    status: str
    error_message: Optional[str] = None
    page_count: int
    created_at: datetime

    model_config = {"from_attributes": True}


class DocumentDetailResponse(DocumentResponse):
    pages: List[DocumentPageResponse] = []
