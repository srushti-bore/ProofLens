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


@pytest.mark.asyncio
async def test_case_insensitive_email_and_independent_accounts(client: AsyncClient):
    """
    Test case-insensitivity and whitespace normalization in registration and login.
    Verify that independent accounts maintain distinct workspaces and identities.
    """
    # 1. User A registers with mixed-case and whitespace
    res_a = await client.post(
        "/api/v1/auth/register",
        json={"email": "  Dr.Evelyn.Vance@ProofLens.AI  ", "password": "Password123!", "full_name": "Dr. Evelyn Vance"},
    )
    assert res_a.status_code == 201
    token_a = res_a.json()["access_token"]
    user_a = res_a.json()["user"]
    assert user_a["email"] == "dr.evelyn.vance@prooflens.ai"

    # 2. Duplicate registration with lowercase must be rejected
    dup_res = await client.post(
        "/api/v1/auth/register",
        json={"email": "dr.evelyn.vance@prooflens.ai", "password": "Password123!"},
    )
    assert dup_res.status_code == 400

    # 3. User A logs in with all-lowercase and whitespace
    login_a = await client.post(
        "/api/v1/auth/login",
        json={"email": "dr.evelyn.vance@prooflens.ai ", "password": "Password123!"},
    )
    assert login_a.status_code == 200
    assert "access_token" in login_a.json()

    # 4. User B registers independently
    res_b = await client.post(
        "/api/v1/auth/register",
        json={"email": "Jackson.Reed@ProofLens.AI", "password": "Password123!", "full_name": "Jackson Reed"},
    )
    assert res_b.status_code == 201
    token_b = res_b.json()["access_token"]
    user_b = res_b.json()["user"]
    assert user_b["email"] == "jackson.reed@prooflens.ai"

    # 5. User B logs in with lowercase
    login_b = await client.post(
        "/api/v1/auth/login",
        json={"email": "jackson.reed@prooflens.ai", "password": "Password123!"},
    )
    assert login_b.status_code == 200

    # 6. Verify distinct workspaces
    headers_a = {"Authorization": f"Bearer {token_a}"}
    headers_b = {"Authorization": f"Bearer {token_b}"}
    ws_a_list = (await client.get("/api/v1/workspaces", headers=headers_a)).json()
    ws_b_list = (await client.get("/api/v1/workspaces", headers=headers_b)).json()

    assert len(ws_a_list) >= 1
    assert len(ws_b_list) >= 1
    ws_a_id = ws_a_list[0]["id"]
    ws_b_id = ws_b_list[0]["id"]
    assert ws_a_id != ws_b_id

    # 7. Cross-workspace isolation
    assert (await client.get(f"/api/v1/workspaces/{ws_a_id}", headers=headers_b)).status_code == 403
    assert (await client.get(f"/api/v1/workspaces/{ws_b_id}", headers=headers_a)).status_code == 403
