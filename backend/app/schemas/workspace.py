"""
Pydantic schemas for Workspace and WorkspaceMember.
"""

from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field


class WorkspaceCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255, description="Workspace name")
    description: Optional[str] = Field(default=None, description="Optional workspace description")


class WorkspaceMemberResponse(BaseModel):
    id: str
    workspace_id: str
    user_id: str
    role: str
    created_at: datetime

    model_config = {"from_attributes": True}


class WorkspaceResponse(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    owner_id: str
    created_at: datetime
    role: Optional[str] = None

    model_config = {"from_attributes": True}


class WorkspaceDetailResponse(WorkspaceResponse):
    members: List[WorkspaceMemberResponse] = []
