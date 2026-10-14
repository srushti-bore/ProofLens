"""
Local file storage service for PDF documents.
Provides clean storage abstraction isolated by workspace and document ID.
"""

import os
from pathlib import Path
from typing import Optional

from backend.app.core.config import settings


def get_document_storage_path(workspace_id: str, document_id: str) -> Path:
    """Derive local file path for a stored document."""
    base_dir = Path(settings.STORAGE_DIR) / workspace_id
    base_dir.mkdir(parents=True, exist_ok=True)
    return base_dir / f"{document_id}.pdf"


def save_document_file(workspace_id: str, document_id: str, file_bytes: bytes) -> str:
    """Save document bytes to the local filesystem and return the path."""
    dest_path = get_document_storage_path(workspace_id, document_id)
    with open(dest_path, "wb") as f:
        f.write(file_bytes)
    return str(dest_path)


def delete_document_file(storage_path: Optional[str]) -> bool:
    """Delete a document from storage if it exists."""
    if not storage_path:
        return False
    path = Path(storage_path)
    if path.exists() and path.is_file():
        try:
            path.unlink()
            return True
        except OSError:
            return False
    return False


def read_document_file(storage_path: str) -> Optional[bytes]:
    """Read document bytes from storage."""
    path = Path(storage_path)
    if path.exists() and path.is_file():
        with open(path, "rb") as f:
            return f.read()
    return None
