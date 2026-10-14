"""
Document storage abstraction for ProofLens AI.
Provides transparent dispatch between local filesystem storage (development/testing)
and Supabase Storage (production persistence on Render).
"""

from typing import Optional
from backend.app.core.config import settings
from backend.app.services.storage.local_storage import (
    delete_document_file as delete_local_file,
    read_document_file as read_local_file,
    save_document_file as save_local_file,
)
from backend.app.services.storage.supabase_storage import (
    delete_document_file_supabase,
    read_document_file_supabase,
    save_document_file_supabase,
)


def is_supabase_storage(storage_path: Optional[str] = None) -> bool:
    """Check if the storage backend is Supabase or path is a Supabase URI."""
    if storage_path and storage_path.startswith("supabase://"):
        return True
    return settings.STORAGE_BACKEND.lower() == "supabase"


def save_document_file(workspace_id: str, document_id: str, file_bytes: bytes) -> str:
    """
    Save document bytes to the configured storage backend.
    In development: saves to local filesystem ./storage/docs/{workspace_id}/{document_id}.pdf
    In production: saves to private Supabase Storage bucket {workspace_id}/{document_id}.pdf
    """
    if is_supabase_storage():
        return save_document_file_supabase(workspace_id, document_id, file_bytes)
    return save_local_file(workspace_id, document_id, file_bytes)


def read_document_file(storage_path: Optional[str]) -> Optional[bytes]:
    """
    Read document bytes from either Supabase Storage or local filesystem.
    """
    if not storage_path:
        return None
    if is_supabase_storage(storage_path):
        return read_document_file_supabase(storage_path)
    return read_local_file(storage_path)


def delete_document_file(storage_path: Optional[str]) -> bool:
    """
    Delete document from either Supabase Storage or local filesystem.
    """
    if not storage_path:
        return False
    if is_supabase_storage(storage_path):
        return delete_document_file_supabase(storage_path)
    return delete_local_file(storage_path)


__all__ = [
    "save_document_file",
    "read_document_file",
    "delete_document_file",
    "is_supabase_storage",
]
