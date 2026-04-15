"""API Key authentication middleware."""

from typing import Optional
from fastapi import Request, HTTPException, status
from fastapi.security import APIKeyHeader
from motor.motor_asyncio import AsyncIOMotorDatabase
from loguru import logger

from src.core.config import settings
from src.core.database import Database
from src.utils.auth import hash_api_key


api_key_header = APIKeyHeader(name=settings.api_key_header, auto_error=False)


async def verify_api_key(api_key: str) -> Optional[dict]:
    """
    Verify an API key and return the associated client.
    
    Args:
        api_key: The API key to verify
        
    Returns:
        Client document if valid, None otherwise
    """
    try:
        db = Database.get_db()
        api_key_hash = hash_api_key(api_key)
        
        # Find client by API key hash
        client = await db.clients.find_one({
            "api_key_hash": api_key_hash,
            "is_active": True,
            "client_type": "api_key"
        })
        
        if not client:
            logger.warning(f"Invalid API key attempted")
            return None
        
        # Update last_used timestamp
        await db.clients.update_one(
            {"_id": client["_id"]},
            {"$set": {"last_used": datetime.utcnow()}}
        )
        
        logger.info(f"API key authenticated for client: {client['client_id']}")
        return client
        
    except Exception as e:
        logger.error(f"Error verifying API key: {e}")
        return None


async def get_api_key_client(api_key: Optional[str] = None) -> dict:
    """
    FastAPI dependency to get and verify API key.
    
    Args:
        api_key: API key from header
        
    Returns:
        Client document
        
    Raises:
        HTTPException: If API key is missing or invalid
    """
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key missing",
            headers={settings.api_key_header: "required"},
        )
    
    client = await verify_api_key(api_key)
    
    if not client:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired API key",
        )
    
    return client


from datetime import datetime
