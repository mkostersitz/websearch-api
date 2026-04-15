"""Client management API routes."""

from datetime import datetime
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from loguru import logger

from src.models.api import (
    ClientCreateRequest,
    ClientCreateResponse,
    ClientResponse,
    ClientUpdateRequest,
    APIKeyRegenerateResponse
)
from src.services.client_service import ClientService
from src.middleware.api_key import get_api_key_client


router = APIRouter()


@router.post("/clients", response_model=ClientCreateResponse, status_code=status.HTTP_201_CREATED)
async def create_client(
    request: ClientCreateRequest,
    current_client: dict = Depends(get_api_key_client)
) -> ClientCreateResponse:
    """
    Create a new API client.
    
    Requires authentication via API key.
    """
    try:
        # Use the authenticated client's owner as the owner of the new client
        owner_id = current_client["owner_id"]
        
        client, api_key = await ClientService.create_client(
            client_name=request.client_name,
            owner_id=owner_id,
            client_type=request.client_type,
            quota_per_day=request.quota_per_day,
            quota_per_month=request.quota_per_month,
            metadata=request.metadata,
            client_cert_pem=request.client_cert_pem
        )
        
        return ClientCreateResponse(
            client_id=client.client_id,
            client_name=client.client_name,
            client_type=client.client_type,
            api_key=api_key,
            created_at=client.created_at
        )
        
    except Exception as e:
        logger.error(f"Error creating client: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create client"
        )


@router.get("/clients/{client_id}", response_model=ClientResponse)
async def get_client(
    client_id: str,
    current_client: dict = Depends(get_api_key_client)
) -> ClientResponse:
    """Get client details by ID."""
    client = await ClientService.get_client(client_id)
    
    if not client:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Client not found"
        )
    
    # Ensure user can only access their own clients
    if client.owner_id != current_client["owner_id"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    return ClientResponse(**client.model_dump())


@router.get("/clients", response_model=List[ClientResponse])
async def list_clients(
    current_client: dict = Depends(get_api_key_client)
) -> List[ClientResponse]:
    """List all clients for the authenticated user."""
    clients = await ClientService.get_clients_by_owner(current_client["owner_id"])
    return [ClientResponse(**c.model_dump()) for c in clients]


@router.patch("/clients/{client_id}", response_model=ClientResponse)
async def update_client(
    client_id: str,
    request: ClientUpdateRequest,
    current_client: dict = Depends(get_api_key_client)
) -> ClientResponse:
    """Update client settings."""
    # Verify ownership
    client = await ClientService.get_client(client_id)
    if not client or client.owner_id != current_client["owner_id"]:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Client not found"
        )
    
    # Update client
    success = await ClientService.update_client(
        client_id=client_id,
        is_active=request.is_active,
        quota_per_day=request.quota_per_day,
        quota_per_month=request.quota_per_month,
        metadata=request.metadata
    )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update client"
        )
    
    # Return updated client
    updated_client = await ClientService.get_client(client_id)
    return ClientResponse(**updated_client.model_dump())


@router.post("/clients/{client_id}/regenerate-key", response_model=APIKeyRegenerateResponse)
async def regenerate_api_key(
    client_id: str,
    current_client: dict = Depends(get_api_key_client)
) -> APIKeyRegenerateResponse:
    """Regenerate API key for a client."""
    # Verify ownership
    client = await ClientService.get_client(client_id)
    if not client or client.owner_id != current_client["owner_id"]:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Client not found"
        )
    
    if client.client_type != "api_key":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Client does not use API key authentication"
        )
    
    new_api_key = await ClientService.revoke_api_key(client_id)
    
    if not new_api_key:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to regenerate API key"
        )
    
    return APIKeyRegenerateResponse(
        client_id=client_id,
        api_key=new_api_key,
        regenerated_at=datetime.utcnow()
    )


@router.delete("/clients/{client_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_client(
    client_id: str,
    current_client: dict = Depends(get_api_key_client)
) -> None:
    """Delete (deactivate) a client."""
    # Verify ownership
    client = await ClientService.get_client(client_id)
    if not client or client.owner_id != current_client["owner_id"]:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Client not found"
        )
    
    success = await ClientService.delete_client(client_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete client"
        )
