"""
Unit and integration tests for ProofLens AI Phase 7:
1. Investigation audit trail / history retrieval.
2. Citation-linked Markdown report generation and download export.
3. Multi-tenant workspace isolation on history and reports.
"""

import pytest
from httpx import AsyncClient

from backend.tests.test_documents import create_synthetic_pdf


@pytest.mark.asyncio
async def test_investigation_history_and_report_export(client: AsyncClient):
    """
    Test recording Q&A and claim verifications, retrieving investigation history,
    and generating citation-linked Markdown investigation reports.
    """
    # 1. Register user and fetch workspace
    auth_res = await client.post(
        "/api/v1/auth/register",
        json={"email": "report_user@prooflens.ai", "password": "Password123!", "full_name": "Report Tester"},
    )
    assert auth_res.status_code == 201
    token = auth_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    ws_res = await client.get("/api/v1/workspaces", headers=headers)
    ws_id = ws_res.json()[0]["id"]

    # 2. Upload document
    pdf = create_synthetic_pdf([
        "ProofLens AI architecture utilizes gemini-embedding-2 for 768-dimensional document retrieval."
    ])
    doc_res = await client.post(
        f"/api/v1/workspaces/{ws_id}/documents/upload",
        headers=headers,
        files={"file": ("architecture_spec.pdf", pdf, "application/pdf")},
    )
    assert doc_res.status_code == 201

    # 3. Perform a Q&A query (generates history event)
    qa_res = await client.post(
        f"/api/v1/workspaces/{ws_id}/qa/ask",
        headers=headers,
        json={"question": "What embedding model is used in the ProofLens architecture?"},
    )
    assert qa_res.status_code == 200

    # 4. Perform a claim verification (generates history event)
    claim_res = await client.post(
        f"/api/v1/workspaces/{ws_id}/claims/verify",
        headers=headers,
        json={"claim": "ProofLens AI uses gemini-embedding-2 for document retrieval."},
    )
    assert claim_res.status_code == 200

    # 5. Fetch Investigation History
    hist_res = await client.get(f"/api/v1/workspaces/{ws_id}/history", headers=headers)
    assert hist_res.status_code == 200
    hist_data = hist_res.json()
    assert hist_data["workspace_id"] == ws_id
    assert hist_data["total_items"] >= 2
    item_types = [e["item_type"] for e in hist_data["items"]]
    assert "qa" in item_types
    assert "claim" in item_types

    # 6. Export Markdown Investigation Report
    rep_res = await client.get(f"/api/v1/workspaces/{ws_id}/reports/export", headers=headers)
    assert rep_res.status_code == 200
    rep_data = rep_res.json()
    assert "markdown_content" in rep_data
    md_content = rep_data["markdown_content"]

    # Verify structural sections in generated Markdown
    assert "# ProofLens AI — Investigation Report" in md_content
    assert "## 1. Executive Summary & Telemetry" in md_content
    assert "## 2. Document Inventory & Provenance Baseline" in md_content
    assert "## 3. Evidence-Grounded Q&A Investigation Log" in md_content
    assert "## 4. 4-Tier Claim Verification Log" in md_content
    assert "## 5. Traceability & Integrity Guarantee" in md_content
    assert "architecture_spec.pdf" in md_content

    # 7. Test Download Export (Content-Disposition attachment)
    dl_res = await client.get(f"/api/v1/workspaces/{ws_id}/reports/export?download=true", headers=headers)
    assert dl_res.status_code == 200
    assert "text/markdown" in dl_res.headers.get("content-type", "")
    assert "attachment" in dl_res.headers.get("content-disposition", "")


@pytest.mark.asyncio
async def test_history_and_report_tenant_isolation(client: AsyncClient):
    """
    Verify that User B cannot access User A's investigation history or export their reports.
    """
    # User A
    user_a = await client.post(
        "/api/v1/auth/register",
        json={"email": "usera_hist@prooflens.ai", "password": "Password123!"},
    )
    token_a = user_a.json()["access_token"]
    ws_a_id = (await client.get("/api/v1/workspaces", headers={"Authorization": f"Bearer {token_a}"})).json()[0]["id"]

    # User B
    user_b = await client.post(
        "/api/v1/auth/register",
        json={"email": "userb_hist@prooflens.ai", "password": "Password123!"},
    )
    token_b = user_b.json()["access_token"]
    headers_b = {"Authorization": f"Bearer {token_b}"}

    # User B attempts to access User A's history -> 403 Forbidden
    res_hist = await client.get(f"/api/v1/workspaces/{ws_a_id}/history", headers=headers_b)
    assert res_hist.status_code == 403

    # User B attempts to export User A's report -> 403 Forbidden
    res_rep = await client.get(f"/api/v1/workspaces/{ws_a_id}/reports/export", headers=headers_b)
    assert res_rep.status_code == 403


@pytest.mark.asyncio
async def test_history_search_query_filtering(client: AsyncClient):
    """Verify that history search accurately filters by search query term."""
    auth_res = await client.post(
        "/api/v1/auth/register",
        json={"email": "search_user@prooflens.ai", "password": "Password123!"},
    )
    token = auth_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    ws_id = (await client.get("/api/v1/workspaces", headers=headers)).json()[0]["id"]

    pdf = create_synthetic_pdf(["Voyager 1 was launched on September 5, 1977."])
    await client.post(
        f"/api/v1/workspaces/{ws_id}/documents/upload",
        headers=headers,
        files={"file": ("voyager.pdf", pdf, "application/pdf")},
    )

    await client.post(
        f"/api/v1/workspaces/{ws_id}/qa/ask",
        headers=headers,
        json={"question": "When was Voyager 1 launched?"},
    )
    await client.post(
        f"/api/v1/workspaces/{ws_id}/qa/ask",
        headers=headers,
        json={"question": "What is the speed of light in vacuum?"},
    )

    # Search for 'Voyager' -> should return 1 item
    res_search = await client.get(f"/api/v1/workspaces/{ws_id}/history?query=Voyager", headers=headers)
    assert res_search.status_code == 200
    items = res_search.json()["items"]
    assert len(items) >= 1
    assert any("voyager" in item["title"].lower() for item in items)

    # Search for nonexistent term -> should return 0 items
    res_empty = await client.get(f"/api/v1/workspaces/{ws_id}/history?query=NonexistentTerm123", headers=headers)
    assert res_empty.status_code == 200
    assert len(res_empty.json()["items"]) == 0
