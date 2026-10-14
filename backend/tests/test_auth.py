"""
Automated tests for User Authentication, Workspace Creation, and Tenant Isolation.
Verifies that User B cannot access User A's private workspace.
"""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_register_and_login_flow(client: AsyncClient):
    """Test user registration followed by token authentication."""
    # 1. Register a new user
    register_payload = {
        "email": "testuser@prooflens.ai",
        "password": "SecurePassword123!",
        "full_name": "Test User",
    }
    reg_response = await client.post("/api/v1/auth/register", json=register_payload)
    assert reg_response.status_code == 201
    reg_data = reg_response.json()
    assert "access_token" in reg_data
    assert reg_data["user"]["email"] == "testuser@prooflens.ai"
    token = reg_data["access_token"]

    # 2. Duplicate registration should be rejected
    dup_response = await client.post("/api/v1/auth/register", json=register_payload)
    assert dup_response.status_code == 400

    # 3. Login with credentials
    login_payload = {
        "email": "testuser@prooflens.ai",
        "password": "SecurePassword123!",
    }
    login_response = await client.post("/api/v1/auth/login/json", json=login_payload)
    assert login_response.status_code == 200
    login_data = login_response.json()
    assert "access_token" in login_data

    # 4. Login with invalid password should fail
    bad_login = {
        "email": "testuser@prooflens.ai",
        "password": "WrongPassword!",
    }
    bad_response = await client.post("/api/v1/auth/login/json", json=bad_login)
    assert bad_response.status_code == 401

    # 5. Access profile with token
    headers = {"Authorization": f"Bearer {token}"}
    profile_response = await client.get("/api/v1/auth/me", headers=headers)
    assert profile_response.status_code == 200
    profile_data = profile_response.json()
    assert profile_data["email"] == "testuser@prooflens.ai"


@pytest.mark.asyncio
async def test_workspace_creation_and_isolation(client: AsyncClient):
    """
    Test workspace creation and verify strict multi-user tenant isolation:
    User B must be rejected with 403 Forbidden when attempting to access User A's workspace.
    """
    # 1. Register User A
    user_a_res = await client.post(
        "/api/v1/auth/register",
        json={"email": "alice@prooflens.ai", "password": "Password1234!", "full_name": "Alice"},
    )
    token_a = user_a_res.json()["access_token"]
    headers_a = {"Authorization": f"Bearer {token_a}"}

    # 2. Register User B
    user_b_res = await client.post(
        "/api/v1/auth/register",
        json={"email": "bob@prooflens.ai", "password": "Password1234!", "full_name": "Bob"},
    )
    token_b = user_b_res.json()["access_token"]
    headers_b = {"Authorization": f"Bearer {token_b}"}

    # 3. User A creates a confidential workspace
    ws_res = await client.post(
        "/api/v1/workspaces",
        headers=headers_a,
        json={"name": "Alice Confidential Workspace", "description": "Private legal analysis"},
    )
    assert ws_res.status_code == 201
    ws_id = ws_res.json()["id"]

    # 4. User A can view their own workspace
    alice_get = await client.get(f"/api/v1/workspaces/{ws_id}", headers=headers_a)
    assert alice_get.status_code == 200
    assert alice_get.json()["name"] == "Alice Confidential Workspace"

    # 5. SECURITY CHECK: User B attempts to access User A's workspace
    bob_get = await client.get(f"/api/v1/workspaces/{ws_id}", headers=headers_b)
    assert bob_get.status_code == 403
    assert "access" in bob_get.json()["detail"].lower()
