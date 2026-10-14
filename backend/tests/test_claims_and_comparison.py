"""
Automated unit and integration tests for Phase 5:
4-Tier Claim Verification, Cross-Document Comparison Matrix, and Quality Analytics.
"""

import pymupdf
import pytest
from httpx import AsyncClient


def create_synthetic_pdf(pages_text: list[str]) -> bytes:
    """Helper to generate a multi-page PDF in-memory with PyMuPDF."""
    doc = pymupdf.open()
    for text in pages_text:
        page = doc.new_page(width=595, height=842)
        page.insert_text((50, 72), text, fontsize=12)
    pdf_bytes = doc.tobytes()
    doc.close()
    return pdf_bytes


@pytest.mark.asyncio
async def test_claim_verification_4_tier_taxonomy(client: AsyncClient):
    """
    Test the 4-tier Claim Verification engine:
    Supported, Contradicted, and Insufficient Evidence.
    """
    # 1. Register user
    auth_res = await client.post(
        "/api/v1/auth/register",
        json={"email": "claim_tester@prooflens.ai", "password": "Password123!", "full_name": "Claim Tester"},
    )
    token = auth_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    ws_id = (await client.get("/api/v1/workspaces", headers=headers)).json()[0]["id"]

    # 2. Upload document about space exploration
    doc_text = "Voyager 1 was launched by NASA in 1977 and entered interstellar space in 2012."
    pdf_bytes = create_synthetic_pdf([doc_text])
    await client.post(
        f"/api/v1/workspaces/{ws_id}/documents/upload",
        headers=headers,
        files={"file": ("voyager.pdf", pdf_bytes, "application/pdf")},
    )

    # 3. Test Supported Claim
    sup_res = await client.post(
        f"/api/v1/workspaces/{ws_id}/claims/verify",
        headers=headers,
        json={"claim": "Voyager 1 was launched by NASA in 1977"},
    )
    assert sup_res.status_code == 200
    sup_data = sup_res.json()
    assert sup_data["status"] == "Supported"
    assert len(sup_data["citations"]) > 0
    assert sup_data["citations"][0]["page_number"] == 1

    # 4. Test Contradicted Claim (Asserts different year)
    contra_res = await client.post(
        f"/api/v1/workspaces/{ws_id}/claims/verify",
        headers=headers,
        json={"claim": "Voyager 1 was launched by NASA in 2025"},
    )
    assert contra_res.status_code == 200
    contra_data = contra_res.json()
    assert contra_data["status"] == "Contradicted"
    assert "contradicted" in contra_data["explanation"].lower()
    assert len(contra_data["citations"]) > 0

    # 5. Test Insufficient Evidence Claim (Completely absent fact)
    absent_res = await client.post(
        f"/api/v1/workspaces/{ws_id}/claims/verify",
        headers=headers,
        json={"claim": "Voyager 1 carries a bronze statue of an ancient philosopher"},
    )
    assert absent_res.status_code == 200
    absent_data = absent_res.json()
    assert absent_data["status"] == "Insufficient Evidence"
    assert absent_data["confidence_score"] == 0.0


@pytest.mark.asyncio
async def test_cross_document_comparison_matrix(client: AsyncClient):
    """
    Test comparing statements across two distinct uploaded documents.
    Verifies side-by-side findings, agreements, differences, and scope limitations.
    """
    auth_res = await client.post(
        "/api/v1/auth/register",
        json={"email": "comp_tester@prooflens.ai", "password": "Password123!"},
    )
    token = auth_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    ws_id = (await client.get("/api/v1/workspaces", headers=headers)).json()[0]["id"]

    # 1. Upload Doc 1: Mission Alpha
    pdf1 = create_synthetic_pdf(["Mission Alpha discovered extensive water ice on the south pole of Europa in 2020."])
    doc1_res = await client.post(
        f"/api/v1/workspaces/{ws_id}/documents/upload",
        headers=headers,
        files={"file": ("mission_alpha.pdf", pdf1, "application/pdf")},
    )
    doc1_id = doc1_res.json()["id"]

    # 2. Upload Doc 2: Mission Beta
    pdf2 = create_synthetic_pdf(["Mission Beta measured the Europa ice crust thickness to be approximately 20 kilometers."])
    doc2_res = await client.post(
        f"/api/v1/workspaces/{ws_id}/documents/upload",
        headers=headers,
        files={"file": ("mission_beta.pdf", pdf2, "application/pdf")},
    )
    doc2_id = doc2_res.json()["id"]

    # 3. Request comparison across both documents
    compare_payload = {
        "topic": "Europa water ice discoveries",
        "document_ids": [doc1_id, doc2_id],
    }
    comp_res = await client.post(
        f"/api/v1/workspaces/{ws_id}/comparison/compare",
        headers=headers,
        json=compare_payload,
    )
    assert comp_res.status_code == 200
    comp_data = comp_res.json()
    assert len(comp_data["findings_per_document"]) == 2
    assert len(comp_data["agreements"]) > 0
    assert len(comp_data["differences"]) > 0
    assert len(comp_data["scope_limitations"]) > 0
    assert "Europa" in comp_data["synthesis_summary"]

    # 4. Error check: Comparison requires at least 2 documents
    single_doc_payload = {
        "topic": "Europa water ice",
        "document_ids": [doc1_id],
    }
    bad_res = await client.post(
        f"/api/v1/workspaces/{ws_id}/comparison/compare",
        headers=headers,
        json=single_doc_payload,
    )
    assert bad_res.status_code == 422 or bad_res.status_code == 400


@pytest.mark.asyncio
async def test_workspace_analytics_endpoint(client: AsyncClient):
    """Verify that quality and evaluation analytics calculate accurately."""
    auth_res = await client.post(
        "/api/v1/auth/register",
        json={"email": "analytics_user@prooflens.ai", "password": "Password123!"},
    )
    token = auth_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    ws_id = (await client.get("/api/v1/workspaces", headers=headers)).json()[0]["id"]

    # Upload 1 document
    pdf = create_synthetic_pdf(["Quantum cryptography uses photon polarization."])
    await client.post(
        f"/api/v1/workspaces/{ws_id}/documents/upload",
        headers=headers,
        files={"file": ("quantum.pdf", pdf, "application/pdf")},
    )

    # Ask 1 question
    await client.post(
        f"/api/v1/workspaces/{ws_id}/qa/ask",
        headers=headers,
        json={"question": "What does quantum cryptography use?"},
    )

    # Fetch analytics
    analytics_res = await client.get(
        f"/api/v1/workspaces/{ws_id}/analytics",
        headers=headers,
    )
    assert analytics_res.status_code == 200
    adata = analytics_res.json()
    assert adata["total_documents"] >= 1
    assert adata["total_pages"] >= 1
    assert adata["total_chunks"] >= 1
    assert adata["total_queries"] >= 1
    assert adata["supported_answers_count"] >= 1
    assert adata["citation_validity_rate"] == 1.0


@pytest.mark.asyncio
async def test_claims_tenant_isolation(client: AsyncClient):
    """Verify User B cannot verify claims or compare documents in User A's workspace."""
    res_a = await client.post(
        "/api/v1/auth/register",
        json={"email": "alice_claims@prooflens.ai", "password": "Password123!"},
    )
    headers_a = {"Authorization": f"Bearer {res_a.json()['access_token']}"}
    ws_a_id = (await client.get("/api/v1/workspaces", headers=headers_a)).json()[0]["id"]

    res_b = await client.post(
        "/api/v1/auth/register",
        json={"email": "bob_claims@prooflens.ai", "password": "Password123!"},
    )
    headers_b = {"Authorization": f"Bearer {res_b.json()['access_token']}"}

    # Bob tries to verify a claim in Alice's workspace -> MUST return 403 Forbidden
    bob_verify = await client.post(
        f"/api/v1/workspaces/{ws_a_id}/claims/verify",
        headers=headers_b,
        json={"claim": "Alice's revenue increased by 50%"},
    )
    assert bob_verify.status_code == 403
