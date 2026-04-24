"""Script to create initial admin client for testing."""

import asyncio
import uuid
import sys
sys.path.insert(0, '/Users/mikek/repos/websearch-api')

from motor.motor_asyncio import AsyncIOMotorClient
from src.models.database import Client, ClientType, User, UserRole
from src.utils.auth import generate_api_key, hash_api_key
from datetime import datetime


async def create_admin_client():
    """Create an admin client with API key for testing."""
    
    # Connect to MongoDB
    client = AsyncIOMotorClient("mongodb://localhost:27017")
    db = client["websearch_api"]
    
    # Create admin user
    admin_user = User(
        user_id="admin-001",
        username="admin",
        email="admin@example.com",
        full_name="System Administrator",
        role=UserRole.ADMIN,
        metadata={"created_by": "bootstrap"}
    )
    
    # Check if user exists
    existing_user = await db.users.find_one({"email": admin_user.email})
    if not existing_user:
        await db.users.insert_one(admin_user.model_dump())
        print(f"✓ Created admin user: {admin_user.email}")
    else:
        print(f"✓ Admin user already exists: {admin_user.email}")
    
    # Generate API key
    api_key = generate_api_key()
    api_key_hash = hash_api_key(api_key)
    
    # Create admin client
    admin_client = Client(
        client_id="client-admin-001",
        client_name="Admin API Client",
        client_type=ClientType.API_KEY,
        owner_id=admin_user.user_id,
        role=UserRole.ADMIN,
        api_key_hash=api_key_hash,
        quota_per_day=10000,
        quota_per_month=300000,
        metadata={"created_by": "bootstrap"}
    )
    
    # Check if client exists
    existing_client = await db.clients.find_one({"client_id": admin_client.client_id})
    if not existing_client:
        await db.clients.insert_one(admin_client.model_dump())
        print(f"✓ Created admin client: {admin_client.client_id}")
        print(f"\n{'='*60}")
        print(f"🔑 ADMIN API KEY (save this securely!):")
        print(f"{'='*60}")
        print(f"\n{api_key}\n")
        print(f"{'='*60}")
        print(f"\nUse this in API requests:")
        print(f"curl -H 'X-API-Key: {api_key}' http://localhost:8000/api/v1/health")
        print(f"{'='*60}\n")
    else:
        print(f"✓ Admin client already exists: {admin_client.client_id}")
        print(f"\nNote: API key is only shown once during creation.")
    
    client.close()


if __name__ == "__main__":
    asyncio.run(create_admin_client())
