"""Comprehensive integration tests for WebSearch API."""

import asyncio
import httpx
import pytest
from datetime import datetime

BASE_URL = "http://localhost:8000"
API_KEY = "GA_Incg4zEhpK-65G6PwL499t2kXvH2Cs-hWf6udtZU"

@pytest.mark.asyncio
async def test_health_endpoints():
    """Test health and readiness endpoints."""
    async with httpx.AsyncClient() as client:
        # Health check
        response = await client.get(f"{BASE_URL}/api/v1/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        
        # Readiness check
        response = await client.get(f"{BASE_URL}/api/v1/ready")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ready"


@pytest.mark.asyncio
async def test_authentication():
    """Test API key authentication."""
    async with httpx.AsyncClient() as client:
        # Without API key - should fail
        response = await client.get(f"{BASE_URL}/api/v1/clients")
        assert response.status_code == 401
        
        # With valid API key - should succeed
        headers = {"X-API-Key": API_KEY}
        response = await client.get(f"{BASE_URL}/api/v1/clients", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)


@pytest.mark.asyncio
async def test_search_endpoint():
    """Test search endpoint."""
    async with httpx.AsyncClient() as client:
        headers = {
            "X-API-Key": API_KEY,
            "Content-Type": "application/json"
        }
        payload = {
            "query": "artificial intelligence",
            "max_results": 5,
            "safe_search": True
        }
        
        response = await client.post(
            f"{BASE_URL}/api/v1/search",
            headers=headers,
            json=payload
        )
        assert response.status_code == 200
        data = response.json()
        
        # Verify response structure
        assert "query" in data
        assert "results" in data
        assert "total_results" in data
        assert "provider" in data
        assert "rate_limit_info" in data
        assert "quota_info" in data
        
        # Verify rate limit info
        assert data["rate_limit_info"]["limit"] == 60
        assert data["rate_limit_info"]["remaining"] <= 60
        
        # Verify quota info
        assert data["quota_info"]["daily"]["limit"] == 10000
        assert data["quota_info"]["monthly"]["limit"] == 300000


@pytest.mark.asyncio
async def test_provider_status():
    """Test search provider status endpoint."""
    async with httpx.AsyncClient() as client:
        headers = {"X-API-Key": API_KEY}
        response = await client.get(
            f"{BASE_URL}/api/v1/search/providers",
            headers=headers
        )
        assert response.status_code == 200
        data = response.json()
        
        # Should have at least Google and Bing providers
        assert len(data) >= 2
        
        # Verify provider structure
        for provider in data:
            assert "name" in provider
            assert "healthy" in provider
            assert "enabled" in provider


@pytest.mark.asyncio
async def test_admin_endpoints():
    """Test admin dashboard endpoints."""
    async with httpx.AsyncClient() as client:
        headers = {"X-API-Key": API_KEY}
        
        # Overview stats
        response = await client.get(
            f"{BASE_URL}/api/v1/admin/stats/overview",
            headers=headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "total_clients" in data
        assert "total_users" in data
        assert "searches_24h" in data
        
        # System health
        response = await client.get(
            f"{BASE_URL}/api/v1/admin/system/health",
            headers=headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "components" in data
        assert "database" in data["components"]


@pytest.mark.asyncio
async def test_client_management():
    """Test client CRUD operations."""
    async with httpx.AsyncClient() as client:
        headers = {
            "X-API-Key": API_KEY,
            "Content-Type": "application/json"
        }
        
        # List clients
        response = await client.get(f"{BASE_URL}/api/v1/clients", headers=headers)
        assert response.status_code == 200
        initial_count = len(response.json())
        
        # Create new client
        payload = {
            "client_name": "Test Client",
            "client_type": "api_key",
            "quota_per_day": 1000,
            "quota_per_month": 30000,
            "metadata": {"test": True}
        }
        response = await client.post(
            f"{BASE_URL}/api/v1/clients",
            headers=headers,
            json=payload
        )
        assert response.status_code == 201
        created_client = response.json()
        assert "client_id" in created_client
        assert "api_key" in created_client
        assert created_client["client_name"] == "Test Client"
        
        client_id = created_client["client_id"]
        
        # Get client details
        response = await client.get(
            f"{BASE_URL}/api/v1/clients/{client_id}",
            headers=headers
        )
        assert response.status_code == 200
        client_details = response.json()
        assert client_details["client_id"] == client_id
        
        # Update client
        update_payload = {
            "is_active": False,
            "quota_per_day": 500
        }
        response = await client.put(
            f"{BASE_URL}/api/v1/clients/{client_id}",
            headers=headers,
            json=update_payload
        )
        assert response.status_code == 200
        updated_client = response.json()
        assert updated_client["is_active"] == False
        assert updated_client["quota_per_day"] == 500
        
        # Delete client
        response = await client.delete(
            f"{BASE_URL}/api/v1/clients/{client_id}",
            headers=headers
        )
        assert response.status_code == 204


@pytest.mark.asyncio
async def test_rate_limiting():
    """Test rate limiting enforcement."""
    async with httpx.AsyncClient() as client:
        headers = {
            "X-API-Key": API_KEY,
            "Content-Type": "application/json"
        }
        payload = {"query": "test", "max_results": 1}
        
        # Make multiple requests rapidly
        responses = []
        for _ in range(5):
            response = await client.post(
                f"{BASE_URL}/api/v1/search",
                headers=headers,
                json=payload
            )
            responses.append(response)
        
        # All should succeed (within rate limit)
        for response in responses:
            assert response.status_code == 200
            data = response.json()
            assert "rate_limit_info" in data


if __name__ == "__main__":
    # Run tests
    print("🧪 Running WebSearch API Integration Tests...")
    print("=" * 60)
    pytest.main([__file__, "-v", "--asyncio-mode=auto"])
