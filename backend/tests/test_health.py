"""
Automated unit tests for the health check endpoint.
"""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_health_endpoint(client: AsyncClient):
    """Verify that the health check endpoint returns 200 and expected payload."""
    response = await client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] in ["ok", "degraded"]
    assert data["app_name"] == "ProofLens AI"
    assert data["version"] == "0.2.0"
    assert "database" in data
