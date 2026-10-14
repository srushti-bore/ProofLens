"""
Dependency injection utilities for FastAPI routes.
Enforces JWT authentication and multi-user workspace authorization server-side.
"""

from typing import Annotated
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.config import settings
from backend.app.core.database import get_db
from backend.app.core.security import decode_access_token
from backend.app.models.user import User
from backend.app.models.workspace import Workspace, WorkspaceMember

oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_STR}/auth/login")

DBDep = Annotated[AsyncSession, Depends(get_db)]
TokenDep = Annotated[str, Depends(oauth2_scheme)]


async def get_current_user(token: TokenDep, db: DBDep) -> User:
    """Validate JWT token and return the authenticated user."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    payload = decode_access_token(token)
    if not payload:
        raise credentials_exception
    user_id: str = payload.get("sub")
    if not user_id:
        raise credentials_exception

    stmt = select(User).where(User.id == user_id)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    if user is None:
        raise credentials_exception
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user account",
        )
    return user


CurrentUserDep = Annotated[User, Depends(get_current_user)]


async def get_current_workspace(
    workspace_id: str,
    current_user: CurrentUserDep,
    db: DBDep,
) -> Workspace:
    """
    Enforce workspace tenant authorization.
    Verifies that the current user is either the workspace owner or an authorized member.
    """
    # Check if user is owner
    stmt = select(Workspace).where(
        Workspace.id == workspace_id,
        Workspace.owner_id == current_user.id,
    )
    result = await db.execute(stmt)
    workspace = result.scalar_one_or_none()

    if workspace:
        return workspace

    # Check if user is member
    member_stmt = select(WorkspaceMember).where(
        WorkspaceMember.workspace_id == workspace_id,
        WorkspaceMember.user_id == current_user.id,
    )
    member_result = await db.execute(member_stmt)
    member = member_result.scalar_one_or_none()

    if not member:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have access to this workspace",
        )

    # Fetch workspace
    ws_stmt = select(Workspace).where(Workspace.id == workspace_id)
    ws_result = await db.execute(ws_stmt)
    workspace = ws_result.scalar_one_or_none()

    if not workspace:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workspace not found",
        )
    return workspace


CurrentWorkspaceDep = Annotated[Workspace, Depends(get_current_workspace)]
