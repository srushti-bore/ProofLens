"""
Automated unit and integration tests for Phase 4:
Grounded Question Answering, Citation Integrity Validation, and Explicit Abstention (Insufficient Evidence).
"""

import pymupdf
import pytest
from httpx import AsyncClient

from backend.app.services.citation.citation_validator import validate_citations
from backend.app.services.retrieval.retrieval_service import RetrievedChunk


def create_synthetic_pdf(pages_text: list[str]) -> bytes:
    """Helper to generate a multi-page PDF in-memory with PyMuPDF."""
    doc = pymupdf.open()
    for text in pages_text:
        page = doc.new_page(width=595, height=842)
        page.insert_text((50, 72), text, fontsize=12)
    pdf_bytes = doc.tobytes()
    doc.close()
    return pdf_bytes


def test_citation_validator_detects_hallucinations():
    """Verify that the citation validator rejects hallucinated chunk IDs."""
    real_chunk = RetrievedChunk(
        chunk_id="chunk-real-123",
        document_id="doc-abc",
        filename="apollo_mission.pdf",
        page_number=1,
        chunk_index=0,
        content="President Kennedy announced the Apollo program in 1961.",
        similarity_score=0.88,
    )

    # 1. Valid citation matching real chunk
    valid_raw = [
        {
            "chunk_id": "chunk-real-123",
            "document_id": "doc-abc",
            "page_number": 1,
            "excerpt": "announced the Apollo program in 1961",
        }
    ]
    val_result = validate_citations(valid_raw, [real_chunk])
    assert len(val_result) == 1
    assert val_result[0].chunk_id == "chunk-real-123"
    assert val_result[0].is_validated is True

    # 2. Hallucinated chunk ID should be rejected
    fake_raw = [
        {
            "chunk_id": "chunk-hallucinated-999",
            "document_id": "fake-doc",
            "page_number": 99,
            "excerpt": "invented quote",
        }
    ]
    fake_result = validate_citations(fake_raw, [real_chunk])
    # Fallback derives citation from real chunk, rejecting the fake chunk ID
    assert len(fake_result) == 1
    assert fake_result[0].chunk_id == "chunk-real-123"


@pytest.mark.asyncio
async def test_grounded_qa_and_citation_verification(client: AsyncClient):
    """
    Test grounded Q&A over an uploaded PDF:
    Verifies that claims cite exact page numbers and citations are persisted.
    """
    # 1. Register user
    auth_res = await client.post(
        "/api/v1/auth/register",
        json={"email": "qa_user@prooflens.ai", "password": "Password123!", "full_name": "QA User"},
    )
    token = auth_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Get workspace
    ws_id = (await client.get("/api/v1/workspaces", headers=headers)).json()[0]["id"]

    # 3. Create PDF with distinct facts
    page1 = "Project Apollo was initiated in 1961 by President John F. Kennedy with the goal of lunar landing."
    page2 = "The Saturn V rocket stood 111 meters tall and produced 34.5 million newtons of thrust."
    pdf_bytes = create_synthetic_pdf([page1, page2])

    # 4. Upload document
    upload_res = await client.post(
        f"/api/v1/workspaces/{ws_id}/documents/upload",
        headers=headers,
        files={"file": ("apollo_spec.pdf", pdf_bytes, "application/pdf")},
    )
    assert upload_res.status_code == 201

    # 5. Ask grounded question about Page 1
    qa_payload = {
        "question": "When was Project Apollo initiated by Kennedy?",
        "top_k": 3,
    }
    qa_res = await client.post(
        f"/api/v1/workspaces/{ws_id}/qa/ask",
        headers=headers,
        json=qa_payload,
    )
    assert qa_res.status_code == 200
    qa_data = qa_res.json()
    assert qa_data["status"] == "supported"
    assert "1961" in qa_data["answer"]
    assert len(qa_data["citations"]) > 0
    top_cit = qa_data["citations"][0]
    assert top_cit["filename"] == "apollo_spec.pdf"
    assert top_cit["page_number"] == 1
    assert top_cit["is_validated"] is True

    # 6. Ask grounded question about Page 2
    saturn_payload = {
        "question": "What was the height and thrust of the Saturn V rocket?",
        "top_k": 3,
    }
    saturn_res = await client.post(
        f"/api/v1/workspaces/{ws_id}/qa/ask",
        headers=headers,
        json=saturn_payload,
    )
    assert saturn_res.status_code == 200
    saturn_data = saturn_res.json()
    assert saturn_data["status"] == "supported"
    assert len(saturn_data["citations"]) > 0
    saturn_cit = saturn_data["citations"][0]
    assert saturn_cit["page_number"] == 2
    assert saturn_cit["is_validated"] is True


@pytest.mark.asyncio
async def test_explicit_abstention_on_unsupported_question(client: AsyncClient):
    """
    Test that questions whose answers are absent from the document collection
    trigger an explicit insufficient-evidence response instead of fabricating an answer.
    """
    # 1. Register user
    auth_res = await client.post(
        "/api/v1/auth/register",
        json={"email": "abstain_user@prooflens.ai", "password": "Password123!"},
    )
    token = auth_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    ws_id = (await client.get("/api/v1/workspaces", headers=headers)).json()[0]["id"]

    # 2. Upload document about chemistry
    pdf_bytes = create_synthetic_pdf(["Organic chemistry studies carbon compounds and molecular structures."])
    await client.post(
        f"/api/v1/workspaces/{ws_id}/documents/upload",
        headers=headers,
        files={"file": ("chemistry.pdf", pdf_bytes, "application/pdf")},
    )

    # 3. Ask question completely absent from the document (Medieval history)
    unsupported_payload = {
        "question": "What ingredients were required for medieval Byzantine bread making?",
        "top_k": 3,
    }
    res = await client.post(
        f"/api/v1/workspaces/{ws_id}/qa/ask",
        headers=headers,
        json=unsupported_payload,
    )
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "insufficient_evidence"
    assert data["confidence_score"] == 0.0
    assert "insufficient" in data["answer"].lower()
    # Citations must be empty on abstention
    assert len(data["citations"]) == 0


@pytest.mark.asyncio
async def test_qa_tenant_isolation(client: AsyncClient):
    """Verify User B cannot query User A's workspace."""
    res_a = await client.post(
        "/api/v1/auth/register",
        json={"email": "alice_qa@prooflens.ai", "password": "Password123!"},
    )
    headers_a = {"Authorization": f"Bearer {res_a.json()['access_token']}"}
    ws_a_id = (await client.get("/api/v1/workspaces", headers=headers_a)).json()[0]["id"]

    res_b = await client.post(
        "/api/v1/auth/register",
        json={"email": "bob_qa@prooflens.ai", "password": "Password123!"},
    )
    headers_b = {"Authorization": f"Bearer {res_b.json()['access_token']}"}

    # Bob tries to ask a question in Alice's workspace -> MUST return 403 Forbidden
    bob_qa = await client.post(
        f"/api/v1/workspaces/{ws_a_id}/qa/ask",
        headers=headers_b,
        json={"question": "What is Alice's financial summary?"},
    )
    assert bob_qa.status_code == 403


@pytest.mark.asyncio
async def test_case_a_answerable_identity_question(client: AsyncClient):
    """
    Case A — Answerable identity question:
    Document explicitly contains person's name in text. System identifies the person and cites Page 1.
    """
    auth_res = await client.post(
        "/api/v1/auth/register",
        json={"email": "case_a_user@prooflens.ai", "password": "Password123!"},
    )
    headers = {"Authorization": f"Bearer {auth_res.json()['access_token']}"}
    ws_id = (await client.get("/api/v1/workspaces", headers=headers)).json()[0]["id"]

    page1 = "SAYALI V. INGOLE\ningolesayali283@gmail.com | 7020304303\nBachelor of Engineering in Information Technology"
    pdf_bytes = create_synthetic_pdf([page1])

    upload_res = await client.post(
        f"/api/v1/workspaces/{ws_id}/documents/upload",
        headers=headers,
        files={"file": ("Sayali_Resume.pdf", pdf_bytes, "application/pdf")},
    )
    assert upload_res.status_code == 201

    qa_res = await client.post(
        f"/api/v1/workspaces/{ws_id}/qa/ask",
        headers=headers,
        json={"question": "whose resume is this?"},
    )
    assert qa_res.status_code == 200
    data = qa_res.json()
    assert data["status"] == "supported"
    assert "sayali" in data["answer"].lower()
    assert len(data["citations"]) > 0
    assert data["citations"][0]["page_number"] == 1
    assert data["citations"][0]["is_validated"] is True


@pytest.mark.asyncio
async def test_case_b_filename_only_evidence_does_not_identify_owner(client: AsyncClient):
    """
    Case B — Filename-only evidence:
    The filename contains a person's name ('Jane_Doe_Resume.pdf'), but document text does NOT contain
    any person identity. The system must NOT treat the filename alone as verified proof and must abstain.
    """
    auth_res = await client.post(
        "/api/v1/auth/register",
        json={"email": "case_b_user@prooflens.ai", "password": "Password123!"},
    )
    headers = {"Authorization": f"Bearer {auth_res.json()['access_token']}"}
    ws_id = (await client.get("/api/v1/workspaces", headers=headers)).json()[0]["id"]

    page1 = "QUARTERLY EARNINGS REPORT Q3 2024\nRevenue increased by 14% year-over-year across enterprise software divisions."
    pdf_bytes = create_synthetic_pdf([page1])

    upload_res = await client.post(
        f"/api/v1/workspaces/{ws_id}/documents/upload",
        headers=headers,
        files={"file": ("Jane_Doe_Resume.pdf", pdf_bytes, "application/pdf")},
    )
    assert upload_res.status_code == 201

    qa_res = await client.post(
        f"/api/v1/workspaces/{ws_id}/qa/ask",
        headers=headers,
        json={"question": "whose resume is this?"},
    )
    assert qa_res.status_code == 200
    data = qa_res.json()
    assert data["status"] == "insufficient_evidence"
    assert len(data["citations"]) == 0
    assert "jane" not in data["answer"].lower()


def test_case_d_retrieval_failure_handling():
    """
    Case D — Retrieval failure:
    When retrieval returns 0 candidate chunks, the synthesis engine must explicitly abstain
    and explain that no relevant passages were retrieved rather than fabricating an answer.
    """
    from backend.app.services.generation.gemini_generator import qa_generator

    ans = qa_generator.generate_grounded_answer("When was the constitution signed?", [])
    assert ans.status == "insufficient_evidence"
    assert ans.confidence_score == 0.0
    assert len(ans.raw_citations) == 0
    assert "no relevant passages were retrieved" in ans.answer_text.lower()

