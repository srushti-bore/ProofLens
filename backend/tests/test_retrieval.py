"""
Automated unit and integration tests for Phase 3:
Semantic Chunking, Gemini Embedding 2 adapter, and Authorization-Scoped Vector Retrieval.
"""

import math
import pymupdf
import pytest
from httpx import AsyncClient

from backend.app.services.chunking.text_chunker import chunk_document_pages, split_text_into_chunks
from backend.app.services.embeddings.gemini_embedder import GeminiEmbeddingProvider, embedder


def create_synthetic_pdf(pages_text: list[str]) -> bytes:
    """Helper to generate a multi-page PDF in-memory with PyMuPDF."""
    doc = pymupdf.open()
    for text in pages_text:
        page = doc.new_page(width=595, height=842)
        page.insert_text((50, 72), text, fontsize=12)
    pdf_bytes = doc.tobytes()
    doc.close()
    return pdf_bytes


def test_chunking_provenance():
    """Verify that chunking preserves page_number and sequential indexing."""
    sample_page_1 = "ProofLens AI is an evidence-first document intelligence platform. " * 50
    chunks = split_text_into_chunks(
        text=sample_page_1,
        page_number=1,
        start_chunk_idx=0,
        max_chunk_chars=600,
        overlap_chars=100,
    )
    assert len(chunks) > 1
    for idx, c in enumerate(chunks):
        assert c.page_number == 1
        assert c.chunk_index == idx
        assert len(c.content) > 0


def test_embedding_dimensions_and_normalization():
    """Verify GeminiEmbeddingProvider returns a 768-dimensional L2-normalized vector."""
    provider = GeminiEmbeddingProvider(dimension=768)
    vec = provider.embed_text("Evidence-grounded question answering")
    assert len(vec) == 768
    # L2 norm should be approximately 1.0
    norm = math.sqrt(sum(x * x for x in vec))
    assert math.isclose(norm, 1.0, rel_tol=1e-3)


@pytest.mark.asyncio
async def test_semantic_retrieval_flow(client: AsyncClient):
    """
    Test uploading a PDF, generating embeddings, and querying the semantic retrieval endpoint.
    Verifies top-k ranking and exact page provenance.
    """
    # 1. Register user
    auth_res = await client.post(
        "/api/v1/auth/register",
        json={"email": "retrieval_user@prooflens.ai", "password": "Password123!", "full_name": "Retrieval User"},
    )
    token = auth_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Get workspace
    ws_id = (await client.get("/api/v1/workspaces", headers=headers)).json()[0]["id"]

    # 3. Create PDF with distinct topics on page 1 and page 2
    page1 = (
        "Quantum computing harnesses the phenomena of superposition and entanglement. "
        "Qubits can exist in multiple states simultaneously, providing exponential speedup for factorization."
    )
    page2 = (
        "Photosynthesis in plants converts solar radiation, water, and carbon dioxide into glucose and oxygen. "
        "Chlorophyll in the chloroplasts absorbs light predominantly in the blue and red wavelengths."
    )
    pdf_bytes = create_synthetic_pdf([page1, page2])

    # 4. Upload document (triggers chunking and embedding)
    files = {"file": ("science_overview.pdf", pdf_bytes, "application/pdf")}
    upload_res = await client.post(
        f"/api/v1/workspaces/{ws_id}/documents/upload",
        headers=headers,
        files=files,
    )
    assert upload_res.status_code == 201
    doc_id = upload_res.json()["id"]

    # 5. Search for quantum computing (expecting Page 1)
    query_payload = {
        "query": "superposition and quantum qubits",
        "top_k": 3,
        "similarity_threshold": 0.0,
    }
    search_res = await client.post(
        f"/api/v1/workspaces/{ws_id}/retrieval/search",
        headers=headers,
        json=query_payload,
    )
    assert search_res.status_code == 200
    data = search_res.json()
    assert data["retrieved_count"] > 0
    top_chunk = data["chunks"][0]
    assert top_chunk["document_id"] == doc_id
    assert top_chunk["filename"] == "science_overview.pdf"
    assert top_chunk["page_number"] == 1
    assert "Quantum" in top_chunk["content"]

    # 6. Search for photosynthesis (expecting Page 2)
    photo_payload = {
        "query": "chloroplasts chlorophyll glucose oxygen",
        "top_k": 3,
        "similarity_threshold": 0.0,
    }
    photo_res = await client.post(
        f"/api/v1/workspaces/{ws_id}/retrieval/search",
        headers=headers,
        json=photo_payload,
    )
    assert photo_res.status_code == 200
    photo_data = photo_res.json()
    assert photo_data["retrieved_count"] > 0
    photo_top = photo_data["chunks"][0]
    assert photo_top["page_number"] == 2
    assert "Photosynthesis" in photo_top["content"]


@pytest.mark.asyncio
async def test_retrieval_tenant_isolation(client: AsyncClient):
    """Verify User B cannot retrieve chunks from User A's workspace."""
    # Register User A
    res_a = await client.post(
        "/api/v1/auth/register",
        json={"email": "alice_retr@prooflens.ai", "password": "Password123!"},
    )
    headers_a = {"Authorization": f"Bearer {res_a.json()['access_token']}"}
    ws_a_id = (await client.get("/api/v1/workspaces", headers=headers_a)).json()[0]["id"]

    # Register User B
    res_b = await client.post(
        "/api/v1/auth/register",
        json={"email": "bob_retr@prooflens.ai", "password": "Password123!"},
    )
    headers_b = {"Authorization": f"Bearer {res_b.json()['access_token']}"}

    # Alice uploads document
    pdf_bytes = create_synthetic_pdf(["Secret financial formula: Profit equals revenue minus total expenses."])
    await client.post(
        f"/api/v1/workspaces/{ws_a_id}/documents/upload",
        headers=headers_a,
        files={"file": ("secret_formula.pdf", pdf_bytes, "application/pdf")},
    )

    # Bob attempts to search Alice's workspace -> MUST return 403 Forbidden
    bob_search = await client.post(
        f"/api/v1/workspaces/{ws_a_id}/retrieval/search",
        headers=headers_b,
        json={"query": "financial formula revenue"},
    )
    assert bob_search.status_code == 403
