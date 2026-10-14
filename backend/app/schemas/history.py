"""
Pydantic schemas for Investigation History, Audit Trail, and Report Export.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict


class HistoryItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    item_type: str  # 'qa' or 'claim'
    title: str  # query text or claim text
    status: str
    confidence_score: float
    citations_count: int
    created_at: datetime
    summary: str
    details: Dict[str, Any]


class HistoryListResponse(BaseModel):
    workspace_id: str
    total_items: int
    items: List[HistoryItemResponse]


class ReportExportResponse(BaseModel):
    workspace_id: str
    workspace_name: str
    generated_at: datetime
    format: str
    markdown_content: str
