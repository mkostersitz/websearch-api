"""Database connection and initialization."""

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from typing import Optional
from loguru import logger
from src.core.config import settings


class Database:
    """Database connection manager."""

    client: Optional[AsyncIOMotorClient] = None
    db: Optional[AsyncIOMotorDatabase] = None

    @classmethod
    async def connect(cls) -> None:
        """Connect to MongoDB."""
        try:
            cls.client = AsyncIOMotorClient(settings.mongodb_url)
            cls.db = cls.client[settings.mongodb_db_name]
            
            # Test connection
            await cls.client.admin.command('ping')
            logger.info(f"Connected to MongoDB: {settings.mongodb_db_name}")
            
            # Initialize indexes
            await cls.initialize_indexes()
            
        except Exception as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            raise

    @classmethod
    async def disconnect(cls) -> None:
        """Disconnect from MongoDB."""
        if cls.client:
            cls.client.close()
            logger.info("Disconnected from MongoDB")

    @classmethod
    async def initialize_indexes(cls) -> None:
        """Create database indexes for performance."""
        if cls.db is None:
            return

        try:
            # Users collection indexes
            await cls.db.users.create_index("email", unique=True)
            await cls.db.users.create_index("username", unique=True)
            await cls.db.users.create_index("created_at")
            
            # Clients collection indexes (for API clients/agents)
            await cls.db.clients.create_index("client_id", unique=True)
            await cls.db.clients.create_index("api_key_hash", unique=True, sparse=True)
            await cls.db.clients.create_index("owner_id")
            await cls.db.clients.create_index("created_at")
            
            # Policies collection indexes
            await cls.db.policies.create_index("policy_id", unique=True)
            await cls.db.policies.create_index("scope")  # global, organization, user
            await cls.db.policies.create_index("target_id")  # user_id or org_id
            await cls.db.policies.create_index([("scope", 1), ("target_id", 1)])
            
            # Search logs collection indexes
            await cls.db.search_logs.create_index("user_id")
            await cls.db.search_logs.create_index("client_id")
            await cls.db.search_logs.create_index("timestamp")
            await cls.db.search_logs.create_index([("timestamp", -1)])  # Recent first
            await cls.db.search_logs.create_index("query_hash")  # For analytics
            
            # Audit logs collection indexes
            await cls.db.audit_logs.create_index("user_id")
            await cls.db.audit_logs.create_index("action")
            await cls.db.audit_logs.create_index("timestamp")
            await cls.db.audit_logs.create_index([("timestamp", -1)])
            await cls.db.audit_logs.create_index("resource_type")
            
            # Configurations collection indexes
            await cls.db.configurations.create_index("key", unique=True)
            await cls.db.configurations.create_index("category")
            
            # Rate limit tracking (TTL index for auto-cleanup)
            await cls.db.rate_limits.create_index("expires_at", expireAfterSeconds=0)
            await cls.db.rate_limits.create_index([("client_id", 1), ("window_start", 1)])
            
            logger.info("Database indexes created successfully")
            
        except Exception as e:
            logger.error(f"Failed to create indexes: {e}")
            raise

    @classmethod
    def get_db(cls) -> AsyncIOMotorDatabase:
        """Get database instance."""
        if cls.db is None:
            raise RuntimeError("Database not connected")
        return cls.db


# Dependency for FastAPI
async def get_database() -> AsyncIOMotorDatabase:
    """FastAPI dependency to get database."""
    return Database.get_db()
