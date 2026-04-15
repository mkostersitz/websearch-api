"""Quick smoke test to verify API functionality."""

import asyncio
import httpx
from datetime import datetime


async def run_smoke_tests():
    """Run basic smoke tests against the API."""
    
    base_url = "http://localhost:8000"
    
    print("🧪 WebSearch API - Smoke Tests")
    print("=" * 60)
    print(f"Testing API at: {base_url}")
    print(f"Started at: {datetime.utcnow().isoformat()}\n")
    
    results = []
    
    async with httpx.AsyncClient() as client:
        # Test 1: Health Check
        try:
            print("1️⃣  Testing health endpoint...")
            response = await client.get(f"{base_url}/api/v1/health", timeout=5.0)
            if response.status_code == 200:
                print("   ✅ Health check passed")
                results.append(("Health Check", True))
            else:
                print(f"   ❌ Health check failed: {response.status_code}")
                results.append(("Health Check", False))
        except Exception as e:
            print(f"   ❌ Health check error: {e}")
            results.append(("Health Check", False))
        
        # Test 2: Readiness Check
        try:
            print("\n2️⃣  Testing readiness endpoint...")
            response = await client.get(f"{base_url}/api/v1/ready", timeout=10.0)
            if response.status_code == 200:
                data = response.json()
                print(f"   ✅ Readiness check passed - Status: {data['status']}")
                print(f"   📊 Checks: {data['checks']}")
                results.append(("Readiness Check", True))
            else:
                print(f"   ❌ Readiness check failed: {response.status_code}")
                results.append(("Readiness Check", False))
        except Exception as e:
            print(f"   ❌ Readiness check error: {e}")
            results.append(("Readiness Check", False))
        
        # Test 3: OpenAPI Docs
        try:
            print("\n3️⃣  Testing OpenAPI documentation...")
            response = await client.get(f"{base_url}/docs", timeout=5.0)
            if response.status_code == 200:
                print("   ✅ OpenAPI docs accessible")
                results.append(("OpenAPI Docs", True))
            else:
                print(f"   ❌ OpenAPI docs failed: {response.status_code}")
                results.append(("OpenAPI Docs", False))
        except Exception as e:
            print(f"   ❌ OpenAPI docs error: {e}")
            results.append(("OpenAPI Docs", False))
        
        # Test 4: Search endpoint (without auth - should fail)
        try:
            print("\n4️⃣  Testing search endpoint without auth (should fail)...")
            response = await client.post(
                f"{base_url}/api/v1/search",
                json={"query": "test", "max_results": 5},
                timeout=5.0
            )
            if response.status_code == 401:
                print("   ✅ Auth protection working (401 Unauthorized)")
                results.append(("Auth Protection", True))
            else:
                print(f"   ⚠️  Unexpected status: {response.status_code}")
                results.append(("Auth Protection", False))
        except Exception as e:
            print(f"   ❌ Search test error: {e}")
            results.append(("Auth Protection", False))
    
    # Summary
    print("\n" + "=" * 60)
    print("📋 Test Summary")
    print("=" * 60)
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    for test_name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} - {test_name}")
    
    print(f"\n📊 Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All smoke tests passed!")
        return 0
    else:
        print("⚠️  Some tests failed. Check API status.")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(run_smoke_tests())
    exit(exit_code)
