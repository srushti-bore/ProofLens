"""
Comprehensive internal services and API integration test suite for ProofLens AI.
Tests internal service units and exercises every REST API v1 endpoint end-to-end
with strict status code checks, schema validation, and multi-tenant isolation.
"""

import io
import pymupdf
import pytest
from httpx import AsyncClient

from backend.app.services.chunking.text_chunker import chunk_document_pages
from backend.app.services.citation.citation_validator import validate_citations
from backend.app.services.embeddings.gemini_embedder import embedder
from backend.app.services.ingestion.pdf_extractor import extract_pdf_pages, validate_pdf_file
from backend.app.services.retrieval.retrieval_service import RetrievedChunk


def create_synthetic_pdf(pages_text: list[str]) -> bytes:
    """Helper to generate a multi-page PDF in-memory with PyMuPDF wrapping."""
    doc = pymupdf.open()
    for text in pages_text:
        page = doc.new_page(width=595, height=842)
        rect = pymupdf.Rect(50, 50, 545, 800)
        page.insert_textbox(rect, text, fontsize=12)
    pdf_bytes = doc.tobytes()
    doc.close()
    return pdf_bytes


# =====================================================================
# 1. Internal Services Unit Testing
# =====================================================================

def test_internal_pdf_validation_and_extraction():
    """Verify internal PDF validation logic and PyMuPDF text extraction."""
    # 1. Valid PDF
    sample_text = "Internal Testing: ProofLens AI document intelligence."
    pdf_bytes = create_synthetic_pdf([sample_text, "Page 2: Page-level provenance."])
    is_valid, err = validate_pdf_file("test.pdf", pdf_bytes, max_size_mb=15)
    assert is_valid is True
    assert err is None

    # 2. Extract pages
    extracted = extract_pdf_pages(pdf_bytes)
    assert extracted.success is True
    assert extracted.page_count == 2
    assert len(extracted.pages) == 2
    assert extracted.pages[0].page_number == 1
    assert "Internal Testing" in extracted.pages[0].text_content
    assert extracted.pages[1].page_number == 2
    assert "Page-level provenance" in extracted.pages[1].text_content

    # 3. Invalid extension
    is_valid, err = validate_pdf_file("test.docx", pdf_bytes, max_size_mb=15)
    assert is_valid is False
    assert "PDF" in err

    # 4. Corrupt header bytes
    is_valid, err = validate_pdf_file("corrupt.pdf", b"NOT_PDF_HEADER_DATA", max_size_mb=15)
    assert is_valid is False
    assert "header" in err.lower()

    # 5. Oversized PDF check
    is_valid, err = validate_pdf_file("huge.pdf", b"%PDF-1.4 " + (b"0" * 1000), max_size_mb=0.0005)
    assert is_valid is False
    assert "exceeds" in err.lower()


def test_internal_text_chunker_boundaries():
    """Verify text chunker sliding window, overlap, and page mapping."""
    sample_text = (
        "ProofLens is an evidence-first document intelligence platform. "
        "It provides grounded answers with direct citations.\n\n"
        "Every claim is verified against primary source documents. "
        "No hallucinated statements or invented citations are allowed.\n\n"
        "The system enforces strict workspace multi-tenant data isolation."
    )

    pdf_bytes = create_synthetic_pdf([sample_text])
    extracted = extract_pdf_pages(pdf_bytes)
    chunks = chunk_document_pages(extracted.pages, max_chunk_chars=120, overlap_chars=20)

    assert len(chunks) >= 2
    for chunk in chunks:
        assert chunk.page_number == 1
        assert len(chunk.content) > 0
        assert chunk.char_count == len(chunk.content)


def test_internal_gemini_embedder_vector_properties():
    """Verify embedding generation yields 768-dimensional float vectors."""
    vectors = embedder.embed_batch(["ProofLens AI", "FastAPI and PostgreSQL"])
    assert len(vectors) == 2
    for vec in vectors:
        assert len(vec) == 768
        assert all(isinstance(val, float) for val in vec)


def test_internal_citation_validator_heuristics():
    """Verify citation validator accepts genuine passages and strictly respects empty citations on abstention."""
    chunk = RetrievedChunk(
        chunk_id="chunk-alpha-001",
        document_id="doc-xyz",
        filename="manual.pdf",
        page_number=3,
        chunk_index=0,
        content="System architecture requires PostgreSQL 18 with pgvector extension enabled.",
        similarity_score=0.92,
    )

    # Genuine citation
    valid_cits = validate_citations(
        raw_citations=[{
            "chunk_id": "chunk-alpha-001",
            "document_id": "doc-xyz",
            "page_number": 3,
            "excerpt": "PostgreSQL 18 with pgvector extension",
        }],
        retrieved_chunks=[chunk],
    )
    assert len(valid_cits) == 1
    assert valid_cits[0].is_validated is True
    assert valid_cits[0].page_number == 3

    # Explicit abstention: empty raw_citations MUST result in 0 validated citations
    empty_cits = validate_citations(
        raw_citations=[],
        retrieved_chunks=[chunk],
    )
    assert len(empty_cits) == 0


# =====================================================================
# 2. End-to-End API Integration Testing
# =====================================================================

@pytest.mark.asyncio
async def test_api_health_endpoint(client: AsyncClient):
    """Verify GET /api/v1/health returns healthy status."""
    res = await client.get("/api/v1/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "ok"
    assert data["database"] == "connected"


@pytest.mark.asyncio
async def test_api_auth_complete_lifecycle(client: AsyncClient):
    """Verify registration, login, profile me, and error handling."""
    # 1. Register User
    reg_res = await client.post(
        "/api/v1/auth/register",
        json={"email": "lifecycle_user@prooflens.ai", "password": "SecurePassword123!", "full_name": "Lifecycle User"},
    )
    assert reg_res.status_code == 201
    auth_data = reg_res.json()
    assert "access_token" in auth_data
    token = auth_data["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Duplicate registration rejected
    dup_res = await client.post(
        "/api/v1/auth/register",
        json={"email": "lifecycle_user@prooflens.ai", "password": "SecurePassword123!"},
    )
    assert dup_res.status_code == 400
    assert "already exists" in dup_res.json()["detail"].lower()

    # 3. Login with correct credentials
    login_res = await client.post(
        "/api/v1/auth/login",
        json={"email": "lifecycle_user@prooflens.ai", "password": "SecurePassword123!"},
    )
    assert login_res.status_code == 200
    assert "access_token" in login_res.json()

    # 4. Login with invalid password
    bad_login = await client.post(
        "/api/v1/auth/login",
        json={"email": "lifecycle_user@prooflens.ai", "password": "WrongPassword!"},
    )
    assert bad_login.status_code == 401

    # 5. Get current user profile (/auth/me)
    me_res = await client.get("/api/v1/auth/me", headers=headers)
    assert me_res.status_code == 200
    me_data = me_res.json()
    assert me_data["email"] == "lifecycle_user@prooflens.ai"
    assert me_data["full_name"] == "Lifecycle User"

    # 6. Unauthenticated /auth/me rejected
    unauth_res = await client.get("/api/v1/auth/me")
    assert unauth_res.status_code in [401, 403]


@pytest.mark.asyncio
async def test_api_workspaces_crud_and_boundary_checks(client: AsyncClient):
    """Verify listing workspaces, creating custom workspace, and detail queries."""
    # 1. Register
    reg_res = await client.post(
        "/api/v1/auth/register",
        json={"email": "ws_manager@prooflens.ai", "password": "Password123!"},
    )
    headers = {"Authorization": f"Bearer {reg_res.json()['access_token']}"}

    # 2. List workspaces - should contain default workspace created on register
    list_res = await client.get("/api/v1/workspaces", headers=headers)
    assert list_res.status_code == 200
    workspaces = list_res.json()
    assert len(workspaces) >= 1
    default_ws_id = workspaces[0]["id"]

    # 3. Create custom workspace
    create_res = await client.post(
        "/api/v1/workspaces",
        headers=headers,
        json={"name": "Audit Workspace Q4", "description": "Financial compliance"},
    )
    assert create_res.status_code == 201
    custom_ws = create_res.json()
    assert custom_ws["name"] == "Audit Workspace Q4"
    custom_ws_id = custom_ws["id"]

    # 4. Get workspace details
    detail_res = await client.get(f"/api/v1/workspaces/{custom_ws_id}", headers=headers)
    assert detail_res.status_code == 200
    detail_data = detail_res.json()
    assert detail_data["id"] == custom_ws_id
    assert len(detail_data["members"]) >= 1

    # 5. Delete custom workspace
    del_res = await client.delete(f"/api/v1/workspaces/{custom_ws_id}", headers=headers)
    assert del_res.status_code == 204

    # 6. Verify deleted workspace is not found
    get_del = await client.get(f"/api/v1/workspaces/{custom_ws_id}", headers=headers)
    assert get_del.status_code in [403, 404]


@pytest.mark.asyncio
async def test_api_full_document_and_qa_pipeline(client: AsyncClient):
    """
    Complete end-to-end flow:
    Upload document -> Search chunks -> Ask grounded question -> Ask abstention question ->
    Verify claim -> Compare documents -> Search history -> Export report -> Check analytics.
    """
    # 1. Setup User and Workspace
    res_user = await client.post(
        "/api/v1/auth/register",
        json={"email": "e2e_analyst@prooflens.ai", "password": "Password123!", "full_name": "E2E Analyst"},
    )
    headers = {"Authorization": f"Bearer {res_user.json()['access_token']}"}
    ws_id = (await client.get("/api/v1/workspaces", headers=headers)).json()[0]["id"]

    # 2. Upload Document A (Apollo Mission)
    doc_a_text = (
        "The Apollo 11 mission landed astronauts Neil Armstrong and Buzz Aldrin on the Moon "
        "on July 20, 1969. Michael Collins remained in lunar orbit in the command module."
    )
    pdf_a_bytes = create_synthetic_pdf([doc_a_text])
    upload_a = await client.post(
        f"/api/v1/workspaces/{ws_id}/documents/upload",
        headers=headers,
        files={"file": ("apollo11.pdf", pdf_a_bytes, "application/pdf")},
    )
    assert upload_a.status_code == 201
    doc_a = upload_a.json()
    doc_a_id = doc_a["id"]
    assert doc_a["page_count"] == 1
    assert doc_a["status"] == "completed"

    # 3. Upload Document B (Artemis Program)
    doc_b_text = (
        "The Artemis program is NASA's effort to return humans to the Moon by the late 2020s. "
        "Artemis II will send four astronauts on a flyby around the Moon."
    )
    pdf_b_bytes = create_synthetic_pdf([doc_b_text])
    upload_b = await client.post(
        f"/api/v1/workspaces/{ws_id}/documents/upload",
        headers=headers,
        files={"file": ("artemis.pdf", pdf_b_bytes, "application/pdf")},
    )
    assert upload_b.status_code == 201
    doc_b_id = upload_b.json()["id"]

    # 4. List Documents
    doc_list_res = await client.get(f"/api/v1/workspaces/{ws_id}/documents", headers=headers)
    assert doc_list_res.status_code == 200
    docs = doc_list_res.json()
    assert len(docs) == 2

    # 5. Serve document file
    dl_res = await client.get(f"/api/v1/workspaces/{ws_id}/documents/{doc_a_id}/file", headers=headers)
    assert dl_res.status_code == 200
    assert len(dl_res.content) > 0

    # 6. Test Vector Retrieval directly (/retrieval/search)
    retrieval_res = await client.post(
        f"/api/v1/workspaces/{ws_id}/retrieval/search",
        headers=headers,
        json={"query": "Who stayed in lunar orbit?", "top_k": 3},
    )
    assert retrieval_res.status_code == 200
    retrieved_chunks = retrieval_res.json()["chunks"]
    assert len(retrieved_chunks) >= 1
    assert any("Collins" in r["content"] for r in retrieved_chunks)

    # 7. Ask Grounded Question (/qa/ask)
    qa_res = await client.post(
        f"/api/v1/workspaces/{ws_id}/qa/ask",
        headers=headers,
        json={"question": "When did Apollo 11 land on the Moon?"},
    )
    assert qa_res.status_code == 200
    qa_data = qa_res.json()
    assert qa_data["status"] == "supported"
    assert "1969" in qa_data["answer"]
    assert len(qa_data["citations"]) > 0
    assert qa_data["citations"][0]["page_number"] == 1

    # 8. Ask Unsupported Question (Explicit Abstention)
    abstain_res = await client.post(
        f"/api/v1/workspaces/{ws_id}/qa/ask",
        headers=headers,
        json={"question": "What is the average temperature on Neptune's moon Triton?"},
    )
    assert abstain_res.status_code == 200
    abs_data = abstain_res.json()
    assert abs_data["status"] == "insufficient_evidence"
    assert abs_data["confidence_score"] == 0.0
    assert abs_data["citations"] == []
    assert "insufficient" in abs_data["answer"].lower()

    # 9. Claim Verification: Supported
    claim_sup = await client.post(
        f"/api/v1/workspaces/{ws_id}/claims/verify",
        headers=headers,
        json={"claim": "Neil Armstrong landed on the Moon in 1969."},
    )
    assert claim_sup.status_code == 200
    assert claim_sup.json()["status"] == "Supported"

    # 10. Claim Verification: Contradicted
    claim_contra = await client.post(
        f"/api/v1/workspaces/{ws_id}/claims/verify",
        headers=headers,
        json={"claim": "Apollo 11 landed on Mars in the year 2050."},
    )
    assert claim_contra.status_code == 200
    assert claim_contra.json()["status"] in ["Contradicted", "Insufficient Evidence"]

    # 11. Cross-Document Comparison (/comparison/compare)
    comp_res = await client.post(
        f"/api/v1/workspaces/{ws_id}/comparison/compare",
        headers=headers,
        json={"topic": "Lunar missions and astronauts", "document_ids": [doc_a_id, doc_b_id]},
    )
    assert comp_res.status_code == 200
    comp_data = comp_res.json()
    assert len(comp_data["findings_per_document"]) == 2
    assert "Moon" in comp_data["synthesis_summary"] or len(comp_data["agreements"]) > 0

    # 12. Investigation History & Search Query
    hist_all = await client.get(f"/api/v1/workspaces/{ws_id}/history", headers=headers)
    assert hist_all.status_code == 200
    all_items = hist_all.json()["items"]
    assert len(all_items) >= 2  # QA query + claim verifications

    # Search query filtering
    hist_search = await client.get(f"/api/v1/workspaces/{ws_id}/history?query=Apollo", headers=headers)
    assert hist_search.status_code == 200
    search_items = hist_search.json()["items"]
    assert len(search_items) >= 1
    assert any("apollo" in it["title"].lower() for it in search_items)

    # Empty search query
    hist_empty = await client.get(f"/api/v1/workspaces/{ws_id}/history?query=NonExistentSubjectXYZ", headers=headers)
    assert hist_empty.status_code == 200
    assert len(hist_empty.json()["items"]) == 0

    # 13. Reports Export (/reports/export)
    report_res = await client.get(f"/api/v1/workspaces/{ws_id}/reports/export", headers=headers)
    assert report_res.status_code == 200
    report_data = report_res.json()
    assert report_data["format"] == "markdown"
    assert "Investigation Report" in report_data["markdown_content"]
    assert "Apollo" in report_data["markdown_content"]

    # 14. Quality Analytics (/analytics)
    analytics_res = await client.get(f"/api/v1/workspaces/{ws_id}/analytics", headers=headers)
    assert analytics_res.status_code == 200
    adata = analytics_res.json()
    assert adata["total_documents"] == 2
    assert adata["total_pages"] == 2
    assert adata["total_chunks"] >= 2
    assert adata["total_queries"] >= 2
    assert adata["citation_validity_rate"] == 1.0


@pytest.mark.asyncio
async def test_api_strict_multi_tenant_isolation_all_routes(client: AsyncClient):
    """
    Exhaustive cross-tenant security test:
    User B must be strictly forbidden (403) from accessing ANY of User A's resources.
    """
    # 1. Register User A
    res_a = await client.post(
        "/api/v1/auth/register",
        json={"email": "tenant_a@prooflens.ai", "password": "Password123!"},
    )
    headers_a = {"Authorization": f"Bearer {res_a.json()['access_token']}"}
    ws_a_id = (await client.get("/api/v1/workspaces", headers=headers_a)).json()[0]["id"]

    # Upload Doc in User A workspace
    pdf_bytes = create_synthetic_pdf(["Secret financial balance sheet for Organization A."])
    up_a = await client.post(
        f"/api/v1/workspaces/{ws_a_id}/documents/upload",
        headers=headers_a,
        files={"file": ("secret_a.pdf", pdf_bytes, "application/pdf")},
    )
    doc_a_id = up_a.json()["id"]

    # 2. Register User B
    res_b = await client.post(
        "/api/v1/auth/register",
        json={"email": "tenant_b@prooflens.ai", "password": "Password123!"},
    )
    headers_b = {"Authorization": f"Bearer {res_b.json()['access_token']}"}

    # 3. User B attempts unauthorized access across ALL endpoints:
    
    # Workspace Detail
    assert (await client.get(f"/api/v1/workspaces/{ws_a_id}", headers=headers_b)).status_code == 403

    # Document Upload
    assert (await client.post(
        f"/api/v1/workspaces/{ws_a_id}/documents/upload",
        headers=headers_b,
        files={"file": ("intruder.pdf", pdf_bytes, "application/pdf")},
    )).status_code == 403

    # Document List
    assert (await client.get(f"/api/v1/workspaces/{ws_a_id}/documents", headers=headers_b)).status_code == 403

    # Document Detail
    assert (await client.get(f"/api/v1/workspaces/{ws_a_id}/documents/{doc_a_id}", headers=headers_b)).status_code == 403

    # Document Pages
    assert (await client.get(f"/api/v1/workspaces/{ws_a_id}/documents/{doc_a_id}/pages", headers=headers_b)).status_code == 403

    # Document File
    assert (await client.get(f"/api/v1/workspaces/{ws_a_id}/documents/{doc_a_id}/file", headers=headers_b)).status_code == 403

    # Document Deletion
    assert (await client.delete(f"/api/v1/workspaces/{ws_a_id}/documents/{doc_a_id}", headers=headers_b)).status_code == 403

    # Retrieval / Search
    assert (await client.post(
        f"/api/v1/workspaces/{ws_a_id}/retrieval/search",
        headers=headers_b,
        json={"query": "balance sheet"},
    )).status_code == 403

    # QA / Ask
    assert (await client.post(
        f"/api/v1/workspaces/{ws_a_id}/qa/ask",
        headers=headers_b,
        json={"question": "What is Organization A's balance?"},
    )).status_code == 403

    # Claim Verification
    assert (await client.post(
        f"/api/v1/workspaces/{ws_a_id}/claims/verify",
        headers=headers_b,
        json={"claim": "Organization A has 10 million in revenue."},
    )).status_code == 403

    # Document Comparison
    assert (await client.post(
        f"/api/v1/workspaces/{ws_a_id}/comparison/compare",
        headers=headers_b,
        json={"topic": "revenue", "document_ids": [doc_a_id, doc_a_id]},
    )).status_code == 403

    # History
    assert (await client.get(f"/api/v1/workspaces/{ws_a_id}/history", headers=headers_b)).status_code == 403

    # Reports Export
    assert (await client.get(f"/api/v1/workspaces/{ws_a_id}/reports/export", headers=headers_b)).status_code == 403

    # Analytics
    assert (await client.get(f"/api/v1/workspaces/{ws_a_id}/analytics", headers=headers_b)).status_code == 403
