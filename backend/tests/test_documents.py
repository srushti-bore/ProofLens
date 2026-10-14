"""
Automated unit and integration tests for Document Ingestion and Page-Level Provenance.
Uses in-memory PyMuPDF documents to test upload, validation, extraction, and tenant isolation.
"""

import io
import pymupdf
import pytest
from httpx import AsyncClient


def create_synthetic_pdf(pages_text: list[str]) -> bytes:
    """Helper to generate a multi-page PDF in-memory with PyMuPDF."""
    doc = pymupdf.open()
    for text in pages_text:
        page = doc.new_page(width=595, height=842)  # Standard A4 size
        # Insert text at position (50, 72)
        page.insert_text((50, 72), text, fontsize=12)
    pdf_bytes = doc.tobytes()
    doc.close()
    return pdf_bytes


@pytest.mark.asyncio
async def test_upload_and_extract_pdf_pages(client: AsyncClient):
    """Verify end-to-end PDF upload, PyMuPDF page extraction, and provenance metadata."""
    # 1. Register user and get token
    auth_res = await client.post(
        "/api/v1/auth/register",
        json={"email": "docuser@prooflens.ai", "password": "Password123!", "full_name": "Doc User"},
    )
    token = auth_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Get default workspace
    ws_res = await client.get("/api/v1/workspaces", headers=headers)
    ws_id = ws_res.json()[0]["id"]

    # 3. Create a 2-page synthetic PDF with known text
    page1_text = "Page 1: Artificial intelligence enables evidence-first document intelligence."
    page2_text = "Page 2: ProofLens guarantees citation traceability and page provenance."
    pdf_bytes = create_synthetic_pdf([page1_text, page2_text])

    # 4. Upload PDF
    files = {"file": ("test_report.pdf", pdf_bytes, "application/pdf")}
    upload_res = await client.post(
        f"/api/v1/workspaces/{ws_id}/documents/upload",
        headers=headers,
        files=files,
    )
    assert upload_res.status_code == 201
    doc_data = upload_res.json()
    assert doc_data["filename"] == "test_report.pdf"
    assert doc_data["status"] == "completed"
    assert doc_data["page_count"] == 2
    doc_id = doc_data["id"]

    # 5. Retrieve document details
    detail_res = await client.get(
        f"/api/v1/workspaces/{ws_id}/documents/{doc_id}",
        headers=headers,
    )
    assert detail_res.status_code == 200
    detail_data = detail_res.json()
    assert len(detail_data["pages"]) == 2

    # 6. Retrieve extracted pages and verify exact text provenance
    pages_res = await client.get(
        f"/api/v1/workspaces/{ws_id}/documents/{doc_id}/pages",
        headers=headers,
    )
    assert pages_res.status_code == 200
    pages = pages_res.json()
    assert len(pages) == 2
    assert pages[0]["page_number"] == 1
    assert "Artificial intelligence" in pages[0]["text_content"]
    assert pages[1]["page_number"] == 2
    assert "ProofLens guarantees" in pages[1]["text_content"]


@pytest.mark.asyncio
async def test_upload_validation_errors(client: AsyncClient):
    """Test validation rejection for non-PDFs and corrupt files."""
    auth_res = await client.post(
        "/api/v1/auth/register",
        json={"email": "valuser@prooflens.ai", "password": "Password123!"},
    )
    token = auth_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    ws_res = await client.get("/api/v1/workspaces", headers=headers)
    ws_id = ws_res.json()[0]["id"]

    # 1. Non-PDF extension
    text_files = {"file": ("notes.txt", b"plain text", "text/plain")}
    res1 = await client.post(
        f"/api/v1/workspaces/{ws_id}/documents/upload",
        headers=headers,
        files=text_files,
    )
    assert res1.status_code == 400
    assert "Only PDF" in res1.json()["detail"]

    # 2. Fake PDF (invalid header bytes)
    fake_pdf = {"file": ("fake.pdf", b"NOT_A_REAL_PDF_HEADER", "application/pdf")}
    res2 = await client.post(
        f"/api/v1/workspaces/{ws_id}/documents/upload",
        headers=headers,
        files=fake_pdf,
    )
    assert res2.status_code == 400
    assert "invalid file header" in res2.json()["detail"].lower()

    # 3. Empty PDF
    empty_file = {"file": ("empty.pdf", b"", "application/pdf")}
    res3 = await client.post(
        f"/api/v1/workspaces/{ws_id}/documents/upload",
        headers=headers,
        files=empty_file,
    )
    assert res3.status_code == 400
    assert "empty" in res3.json()["detail"].lower()


@pytest.mark.asyncio
async def test_scanned_pdf_rejection(client: AsyncClient):
    """Verify that an empty / scanned image-only PDF without text is flagged with an error."""
    auth_res = await client.post(
        "/api/v1/auth/register",
        json={"email": "scanuser@prooflens.ai", "password": "Password123!"},
    )
    token = auth_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    ws_res = await client.get("/api/v1/workspaces", headers=headers)
    ws_id = ws_res.json()[0]["id"]

    # Create PDF with blank pages (no text content)
    doc = pymupdf.open()
    doc.new_page(width=595, height=842)
    blank_bytes = doc.tobytes()
    doc.close()

    files = {"file": ("scanned_doc.pdf", blank_bytes, "application/pdf")}
    res = await client.post(
        f"/api/v1/workspaces/{ws_id}/documents/upload",
        headers=headers,
        files=files,
    )
    assert res.status_code == 422
    assert "scanned" in res.json()["detail"].lower()


@pytest.mark.asyncio
async def test_document_tenant_isolation_and_delete(client: AsyncClient):
    """Verify User B cannot access User A's document, and cascade delete removes all pages."""
    # Register User A and User B
    res_a = await client.post(
        "/api/v1/auth/register",
        json={"email": "alice_docs@prooflens.ai", "password": "Password123!"},
    )
    token_a = res_a.json()["access_token"]
    headers_a = {"Authorization": f"Bearer {token_a}"}

    res_b = await client.post(
        "/api/v1/auth/register",
        json={"email": "bob_docs@prooflens.ai", "password": "Password123!"},
    )
    token_b = res_b.json()["access_token"]
    headers_b = {"Authorization": f"Bearer {token_b}"}

    ws_a_id = (await client.get("/api/v1/workspaces", headers=headers_a)).json()[0]["id"]

    # Alice uploads document
    pdf_bytes = create_synthetic_pdf(["Confidential financial report for Alice only."])
    files = {"file": ("confidential.pdf", pdf_bytes, "application/pdf")}
    upload_res = await client.post(
        f"/api/v1/workspaces/{ws_a_id}/documents/upload",
        headers=headers_a,
        files=files,
    )
    assert upload_res.status_code == 201
    doc_id = upload_res.json()["id"]

    # SECURITY CHECK: Bob tries to list Alice's documents
    bob_list = await client.get(
        f"/api/v1/workspaces/{ws_a_id}/documents",
        headers=headers_b,
    )
    assert bob_list.status_code == 403

    # SECURITY CHECK: Bob tries to get Alice's document details
    bob_doc = await client.get(
        f"/api/v1/workspaces/{ws_a_id}/documents/{doc_id}",
        headers=headers_b,
    )
    assert bob_doc.status_code == 403

    # Alice deletes her document
    del_res = await client.delete(
        f"/api/v1/workspaces/{ws_a_id}/documents/{doc_id}",
        headers=headers_a,
    )
    assert del_res.status_code == 204

    # Document should no longer exist
    check_res = await client.get(
        f"/api/v1/workspaces/{ws_a_id}/documents/{doc_id}",
        headers=headers_a,
    )
    assert check_res.status_code == 404
