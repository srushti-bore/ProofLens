"""
Workspace management routes.
Enforces multi-user workspace boundaries and member roles.
"""

from typing import List
from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from backend.app.api.deps import CurrentUserDep, CurrentWorkspaceDep, DBDep
from backend.app.models.workspace import Workspace, WorkspaceMember
from backend.app.schemas.workspace import (
    WorkspaceCreate,
    WorkspaceDetailResponse,
    WorkspaceResponse,
)

router = APIRouter(prefix="/workspaces", tags=["Workspaces"])


@router.get("", response_model=List[WorkspaceResponse])
async def list_user_workspaces(current_user: CurrentUserDep, db: DBDep) -> List[WorkspaceResponse]:
    """List all workspaces the authenticated user owns or belongs to."""
    stmt = (
        select(Workspace, WorkspaceMember.role)
        .join(WorkspaceMember, Workspace.id == WorkspaceMember.workspace_id)
        .where(WorkspaceMember.user_id == current_user.id)
        .order_by(Workspace.created_at.desc())
    )
    result = await db.execute(stmt)
    rows = result.all()

    workspaces = []
    for ws, role in rows:
        item = WorkspaceResponse(
            id=ws.id,
            name=ws.name,
            description=ws.description,
            owner_id=ws.owner_id,
            created_at=ws.created_at,
            role=role,
        )
        workspaces.append(item)
    return workspaces


@router.post("", response_model=WorkspaceResponse, status_code=status.HTTP_201_CREATED)
async def create_workspace(
    ws_in: WorkspaceCreate,
    current_user: CurrentUserDep,
    db: DBDep,
) -> WorkspaceResponse:
    """Create a new workspace with the authenticated user as owner."""
    workspace = Workspace(
        name=ws_in.name,
        description=ws_in.description,
        owner_id=current_user.id,
    )
    db.add(workspace)
    await db.flush()

    membership = WorkspaceMember(
        workspace_id=workspace.id,
        user_id=current_user.id,
        role="owner",
    )
    db.add(membership)
    await db.commit()
    await db.refresh(workspace)

    return WorkspaceResponse(
        id=workspace.id,
        name=workspace.name,
        description=workspace.description,
        owner_id=workspace.owner_id,
        created_at=workspace.created_at,
        role="owner",
    )


@router.get("/{workspace_id}", response_model=WorkspaceDetailResponse)
async def get_workspace(
    workspace: CurrentWorkspaceDep,
    db: DBDep,
) -> WorkspaceDetailResponse:
    """Retrieve workspace details and members list."""
    stmt = (
        select(Workspace)
        .options(selectinload(Workspace.members))
        .where(Workspace.id == workspace.id)
    )
    result = await db.execute(stmt)
    full_ws = result.scalar_one()

    return WorkspaceDetailResponse(
        id=full_ws.id,
        name=full_ws.name,
        description=full_ws.description,
        owner_id=full_ws.owner_id,
        created_at=full_ws.created_at,
        members=[m for m in full_ws.members],
    )


@router.delete("/{workspace_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_workspace(
    workspace: CurrentWorkspaceDep,
    current_user: CurrentUserDep,
    db: DBDep,
) -> None:
    """Delete a workspace. Only the workspace owner has permission to delete."""
    if workspace.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the workspace owner can delete this workspace",
        )
    await db.delete(workspace)
    await db.commit()
