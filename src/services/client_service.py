"""Client management service."""

import uuid
from datetime import datetime
from typing import Optional, List
from motor.motor_asyncio import AsyncIOMotorDatabase
from loguru import logger

from src.models.database import Client, ClientType
from src.utils.auth import generate_api_key, hash_api_key
from src.core.database import Database
from src.middleware.mtls import extract_cert_info


class ClientService:
    """Service for managing API clients."""

    @staticmethod
    async def create_client(
        client_name: str,
        owner_id: str,
        client_type: ClientType,
        quota_per_day: int = 1000,
        quota_per_month: int = 30000,
        metadata: Optional[dict] = None,
        client_cert_pem: Optional[str] = None
    ) -> tuple[Client, Optional[str]]:
        """
        Create a new API client.
        
        Args:
            client_name: Name of the client
            owner_id: User ID of the owner
            client_type: Type of client authentication
            quota_per_day: Daily search quota
            quota_per_month: Monthly search quota
            metadata: Additional metadata
            client_cert_pem: PEM-encoded client certificate (for mTLS)
            
        Returns:
            Tuple of (Client object, API key if type is api_key else None)
        """
        db = Database.get_db()
        
        client_id = str(uuid.uuid4())
        api_key = None
        api_key_hash = None
        client_cert_cn = None
        client_cert_serial = None
        client_cert_fingerprint = None
        
        # Generate API key if needed
        if client_type == ClientType.API_KEY:
            api_key = generate_api_key()
            api_key_hash = hash_api_key(api_key)
        
        # Extract certificate info if provided
        if client_type == ClientType.MTLS and client_cert_pem:
            cert_info = extract_cert_info(client_cert_pem)
            client_cert_cn = cert_info["common_name"]
            client_cert_serial = cert_info["serial_number"]
            client_cert_fingerprint = cert_info["fingerprint"]
            
            # Store additional cert info in metadata
            if metadata is None:
                metadata = {}
            metadata.update({
                "cert_issuer": cert_info["issuer"],
                "cert_subject": cert_info["subject"],
                "cert_not_valid_before": cert_info["not_valid_before"],
                "cert_not_valid_after": cert_info["not_valid_after"]
            })
        
        client = Client(
            client_id=client_id,
            client_name=client_name,
            client_type=client_type,
            owner_id=owner_id,
            api_key_hash=api_key_hash,
            client_cert_cn=client_cert_cn,
            client_cert_serial=client_cert_serial,
            client_cert_fingerprint=client_cert_fingerprint,
            quota_per_day=quota_per_day,
            quota_per_month=quota_per_month,
            metadata=metadata or {}
        )
        
        # Insert into database
        await db.clients.insert_one(client.model_dump())
        
        logger.info(f"Created client {client_id} of type {client_type} for owner {owner_id}")
        
        return client, api_key

    @staticmethod
    async def get_client(client_id: str) -> Optional[Client]:
        """Get a client by ID."""
        db = Database.get_db()
        client_doc = await db.clients.find_one({"client_id": client_id})
        
        if not client_doc:
            return None
        
        return Client(**client_doc)

    @staticmethod
    async def get_clients_by_owner(owner_id: str) -> List[Client]:
        """Get all clients for an owner."""
        db = Database.get_db()
        cursor = db.clients.find({"owner_id": owner_id})
        clients = []
        
        async for client_doc in cursor:
            clients.append(Client(**client_doc))
        
        return clients

    @staticmethod
    async def revoke_api_key(client_id: str) -> Optional[str]:
        """
        Revoke an API key and generate a new one.
        
        Args:
            client_id: Client ID
            
        Returns:
            New API key or None if client not found
        """
        db = Database.get_db()
        
        # Get client
        client_doc = await db.clients.find_one({"client_id": client_id})
        if not client_doc or client_doc["client_type"] != "api_key":
            return None
        
        # Generate new API key
        new_api_key = generate_api_key()
        new_api_key_hash = hash_api_key(new_api_key)
        
        # Update in database
        await db.clients.update_one(
            {"client_id": client_id},
            {
                "$set": {
                    "api_key_hash": new_api_key_hash,
                    "updated_at": datetime.utcnow()
                }
            }
        )
        
        logger.info(f"Revoked and regenerated API key for client {client_id}")
        
        return new_api_key

    @staticmethod
    async def update_client(
        client_id: str,
        is_active: Optional[bool] = None,
        quota_per_day: Optional[int] = None,
        quota_per_month: Optional[int] = None,
        metadata: Optional[dict] = None
    ) -> bool:
        """
        Update client settings.
        
        Args:
            client_id: Client ID
            is_active: Active status
            quota_per_day: Daily quota
            quota_per_month: Monthly quota
            metadata: Metadata updates
            
        Returns:
            True if updated, False if not found
        """
        db = Database.get_db()
        
        update_data = {"updated_at": datetime.utcnow()}
        
        if is_active is not None:
            update_data["is_active"] = is_active
        if quota_per_day is not None:
            update_data["quota_per_day"] = quota_per_day
        if quota_per_month is not None:
            update_data["quota_per_month"] = quota_per_month
        if metadata is not None:
            update_data["metadata"] = metadata
        
        result = await db.clients.update_one(
            {"client_id": client_id},
            {"$set": update_data}
        )
        
        if result.modified_count > 0:
            logger.info(f"Updated client {client_id}")
            return True
        
        return False

    @staticmethod
    async def delete_client(client_id: str) -> bool:
        """
        Delete a client (soft delete by setting is_active to False).
        
        Args:
            client_id: Client ID
            
        Returns:
            True if deleted, False if not found
        """
        db = Database.get_db()
        
        result = await db.clients.update_one(
            {"client_id": client_id},
            {
                "$set": {
                    "is_active": False,
                    "updated_at": datetime.utcnow()
                }
            }
        )
        
        if result.modified_count > 0:
            logger.info(f"Deleted (deactivated) client {client_id}")
            return True
        
        return False
