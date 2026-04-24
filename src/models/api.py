"""API models for requests and responses."""

from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field

from src.models.database import ClientType, UserRole


class ClientCreateRequest(BaseModel):
    """Request model for creating a client."""
    client_name: str = Field(..., min_length=3, max_length=100)
    client_type: ClientType
    quota_per_day: int = Field(default=1000, ge=0)
    quota_per_month: int = Field(default=30000, ge=0)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    # For mTLS clients
    client_cert_pem: Optional[str] = Field(None, description="PEM-encoded client certificate (for mTLS clients)")


class ClientCreateResponse(BaseModel):
    """Response model for client creation."""
    client_id: str
    client_name: str
    client_type: ClientType
    api_key: Optional[str] = Field(None, description="Only returned once for API key clients")
    created_at: datetime


class ClientResponse(BaseModel):
    """Response model for client details."""
    client_id: str
    client_name: str
    client_type: ClientType
    owner_id: str
    role: UserRole
    is_active: bool
    quota_per_day: int
    quota_per_month: int
    created_at: datetime
    updated_at: datetime
    last_used: Optional[datetime] = None
    metadata: Dict[str, Any]


class ClientUpdateRequest(BaseModel):
    """Request model for updating a client."""
    is_active: Optional[bool] = None
    quota_per_day: Optional[int] = Field(None, ge=0)
    quota_per_month: Optional[int] = Field(None, ge=0)
    metadata: Optional[Dict[str, Any]] = None


class APIKeyRegenerateResponse(BaseModel):
    """Response model for API key regeneration."""
    client_id: str
    api_key: str
    regenerated_at: datetime
