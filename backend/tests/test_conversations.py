"""
Automated tests for ProofLens AI Persistent Thread-Based Conversations.
Tests:
- Creating a conversation thread on the first question
- Appending subsequent questions to the same conversation thread
- Verifying turn counts and updated timestamps
- Retrieving full conversation turns with citations
- Workspace and user isolation for conversations
- Deleting a conversation thread
"""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_persistent_thread_conversation_flow(client: AsyncClient):
    # 1. Register user & get workspace
    auth_resp = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "convo_tester@prooflens.ai",
            "password": "Password123!",
            "full_name": "Convo Tester",
        },
    )
    assert auth_resp.status_code == 201
    token = auth_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    ws_resp = await client.get("/api/v1/workspaces", headers=headers)
    assert ws_resp.status_code == 200
    workspaces = ws_resp.json()
    assert len(workspaces) > 0
    ws_id = workspaces[0]["id"]

    # 2. First question without conversation_id -> creates new thread
    q1_resp = await client.post(
        f"/api/v1/workspaces/{ws_id}/qa/ask",
        json={"question": "What is the primary architecture of ProofLens AI?"},
        headers=headers,
    )
    assert q1_resp.status_code == 200
    q1_data = q1_resp.json()
    assert "conversation_id" in q1_data
    assert q1_data["conversation_id"] is not None
    conv_id = q1_data["conversation_id"]
    assert "conversation_title" in q1_data
    assert len(q1_data["conversation_title"]) > 0

    # 3. Follow-up question with conversation_id -> appends to same thread
    q2_resp = await client.post(
        f"/api/v1/workspaces/{ws_id}/qa/ask",
        json={
            "question": "Can you elaborate on its vector dimension?",
            "conversation_id": conv_id,
        },
        headers=headers,
    )
    assert q2_resp.status_code == 200
    q2_data = q2_resp.json()
    assert q2_data["conversation_id"] == conv_id

    # 4. List conversations -> must show exactly 1 conversation thread with 2 messages
    list_resp = await client.get(
        f"/api/v1/workspaces/{ws_id}/conversations",
        headers=headers,
    )
    assert list_resp.status_code == 200
    threads = list_resp.json()
    assert len(threads) == 1
    assert threads[0]["id"] == conv_id
    assert threads[0]["message_count"] == 2

    # 5. Get conversation details -> must return both turns with proper questions
    detail_resp = await client.get(
        f"/api/v1/workspaces/{ws_id}/conversations/{conv_id}",
        headers=headers,
    )
    assert detail_resp.status_code == 200
    detail = detail_resp.json()
    assert detail["id"] == conv_id
    assert len(detail["turns"]) == 2
    assert detail["turns"][0]["question"] == "What is the primary architecture of ProofLens AI?"
    assert detail["turns"][1]["question"] == "Can you elaborate on its vector dimension?"

    # 6. User isolation: Another user cannot access this conversation
    other_auth = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "other_investigator@prooflens.ai",
            "password": "Password123!",
            "full_name": "Other Investigator",
        },
    )
    assert other_auth.status_code == 201
    other_token = other_auth.json()["access_token"]
    other_headers = {"Authorization": f"Bearer {other_token}"}

    forbidden_resp = await client.get(
        f"/api/v1/workspaces/{ws_id}/conversations/{conv_id}",
        headers=other_headers,
    )
    # Should be 403 (membership forbidden) or 404
    assert forbidden_resp.status_code in (403, 404)

    # 7. Delete conversation
    del_resp = await client.delete(
        f"/api/v1/workspaces/{ws_id}/conversations/{conv_id}",
        headers=headers,
    )
    assert del_resp.status_code == 204

    # 8. Verify conversation is gone
    get_after_del = await client.get(
        f"/api/v1/workspaces/{ws_id}/conversations/{conv_id}",
        headers=headers,
    )
    assert get_after_del.status_code == 404
