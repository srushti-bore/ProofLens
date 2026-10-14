"""
Unit tests for ProofLens AI document storage abstraction.
Tests both local filesystem and Supabase Storage integrations.
"""

import pytest
from unittest.mock import MagicMock, patch
from backend.app.services.storage import (
    delete_document_file,
    is_supabase_storage,
    read_document_file,
    save_document_file,
)
from backend.app.services.storage.supabase_storage import (
    _parse_storage_uri,
    delete_document_file_supabase,
    read_document_file_supabase,
    save_document_file_supabase,
)


def test_is_supabase_storage_detection():
    # Detects based on URI prefix
    assert is_supabase_storage("supabase://my-bucket/ws1/doc1.pdf") is True
    assert is_supabase_storage("storage/docs/ws1/doc1.pdf") is False
    assert is_supabase_storage(None) is False


def test_parse_storage_uri():
    bucket, obj_path = _parse_storage_uri("supabase://prooflens-docs/ws-123/doc-456.pdf")
    assert bucket == "prooflens-docs"
    assert obj_path == "ws-123/doc-456.pdf"


def test_local_storage_lifecycle(tmp_path):
    with patch("backend.app.services.storage.local_storage.settings.STORAGE_DIR", str(tmp_path)):
        # 1. Save
        file_bytes = b"%PDF-1.4 sample pdf content"
        path = save_document_file("test-ws", "doc-test-1", file_bytes)
        assert path.endswith("doc-test-1.pdf")

        # 2. Read
        read_bytes = read_document_file(path)
        assert read_bytes == file_bytes

        # 3. Delete
        assert delete_document_file(path) is True
        assert read_document_file(path) is None


@patch("backend.app.services.storage.supabase_storage.settings.SUPABASE_URL", "https://mockproject.supabase.co")
@patch("backend.app.services.storage.supabase_storage.settings.SUPABASE_SERVICE_ROLE_KEY", "mock-service-key-123")
@patch("backend.app.services.storage.supabase_storage.settings.SUPABASE_STORAGE_BUCKET", "prooflens-documents")
def test_supabase_storage_lifecycle_mocked():
    with patch("httpx.Client") as mock_client_cls:
        mock_client = MagicMock()
        mock_client_cls.return_value.__enter__.return_value = mock_client

        # Mock Upload
        mock_upload_resp = MagicMock()
        mock_upload_resp.status_code = 200
        mock_client.post.return_value = mock_upload_resp

        uri = save_document_file_supabase("ws-100", "doc-200", b"test pdf")
        assert uri == "supabase://prooflens-documents/ws-100/doc-200.pdf"
        assert mock_client.post.called

        # Mock Read
        mock_read_resp = MagicMock()
        mock_read_resp.status_code = 200
        mock_read_resp.content = b"cloud stored pdf content"
        mock_client.get.return_value = mock_read_resp

        content = read_document_file_supabase(uri)
        assert content == b"cloud stored pdf content"

        # Mock Delete
        mock_del_resp = MagicMock()
        mock_del_resp.status_code = 200
        mock_client.delete.return_value = mock_del_resp

        assert delete_document_file_supabase(uri) is True
