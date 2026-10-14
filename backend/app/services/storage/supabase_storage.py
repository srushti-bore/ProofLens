"""
Supabase Storage provider for ProofLens AI.
Persists uploaded PDFs into a private Supabase Storage bucket, ensuring
permanent storage across backend restarts and container redeployments on Render.
"""

from typing import Optional
import httpx

from backend.app.core.config import settings


def _get_headers() -> dict:
    """Build authorization headers for Supabase Storage REST API."""
    key = settings.SUPABASE_SERVICE_ROLE_KEY or ""
    return {
        "Authorization": f"Bearer {key}",
        "apikey": key,
    }


def _parse_storage_uri(storage_path: str) -> tuple[str, str]:
    """Parse a storage URI or path into (bucket, object_path)."""
    if storage_path.startswith("supabase://"):
        stripped = storage_path.replace("supabase://", "", 1)
        parts = stripped.split("/", 1)
        bucket = parts[0]
        object_path = parts[1] if len(parts) > 1 else ""
        return bucket, object_path
    return settings.SUPABASE_STORAGE_BUCKET, storage_path


def save_document_file_supabase(workspace_id: str, document_id: str, file_bytes: bytes) -> str:
    """
    Upload document bytes to Supabase Storage under the workspace-isolated path:
    {workspace_id}/{document_id}.pdf
    Returns the canonical storage URI: supabase://{bucket}/{workspace_id}/{document_id}.pdf
    """
    if not settings.SUPABASE_URL or not settings.SUPABASE_SERVICE_ROLE_KEY:
        raise RuntimeError(
            "Supabase Storage credentials missing. Configure SUPABASE_URL and "
            "SUPABASE_SERVICE_ROLE_KEY in environment variables."
        )

    base_url = settings.SUPABASE_URL.rstrip("/")
    bucket = settings.SUPABASE_STORAGE_BUCKET
    object_path = f"{workspace_id}/{document_id}.pdf"
    endpoint = f"{base_url}/storage/v1/object/{bucket}/{object_path}"

    headers = {
        **_get_headers(),
        "Content-Type": "application/pdf",
        "x-upsert": "true",
    }

    with httpx.Client(timeout=30.0) as client:
        response = client.post(endpoint, headers=headers, content=file_bytes)
        if response.status_code not in (200, 201):
            raise RuntimeError(
                f"Failed to upload document to Supabase Storage [{response.status_code}]: {response.text}"
            )

    return f"supabase://{bucket}/{object_path}"


def read_document_file_supabase(storage_path: str) -> Optional[bytes]:
    """
    Download document bytes from Supabase Storage using authenticated service role access.
    """
    if not settings.SUPABASE_URL or not settings.SUPABASE_SERVICE_ROLE_KEY or not storage_path:
        return None

    base_url = settings.SUPABASE_URL.rstrip("/")
    bucket, object_path = _parse_storage_uri(storage_path)
    endpoint = f"{base_url}/storage/v1/object/authenticated/{bucket}/{object_path}"

    headers = _get_headers()

    try:
        with httpx.Client(timeout=30.0) as client:
            response = client.get(endpoint, headers=headers)
            if response.status_code == 200:
                return response.content
    except Exception:
        return None

    return None


def delete_document_file_supabase(storage_path: Optional[str]) -> bool:
    """
    Delete a document file from Supabase Storage.
    """
    if not settings.SUPABASE_URL or not settings.SUPABASE_SERVICE_ROLE_KEY or not storage_path:
        return False

    base_url = settings.SUPABASE_URL.rstrip("/")
    bucket, object_path = _parse_storage_uri(storage_path)
    endpoint = f"{base_url}/storage/v1/object/{bucket}/{object_path}"

    headers = _get_headers()

    try:
        with httpx.Client(timeout=15.0) as client:
            response = client.delete(endpoint, headers=headers)
            return response.status_code in (200, 204)
    except Exception:
        return False
