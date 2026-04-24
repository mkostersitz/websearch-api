"""Data models for MongoDB collections."""

from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, EmailStr
from enum import Enum


class UserRole(str, Enum):
    """User roles for RBAC."""
    ADMIN = "admin"
    USER = "user"
    AGENT = "agent"


class User(BaseModel):
    """User model."""
    user_id: str = Field(..., description="Unique user identifier")
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    full_name: Optional[str] = None
    role: UserRole = UserRole.USER
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ClientType(str, Enum):
    """Client type."""
    API_KEY = "api_key"
    OAUTH = "oauth"
    CERTIFICATE = "certificate"


class Client(BaseModel):
    """API Client/Agent model."""
    client_id: str = Field(..., description="Unique client identifier")
    client_name: str = Field(..., min_length=3, max_length=100)
    client_type: ClientType
    owner_id: str = Field(..., description="User ID of the owner")
    role: UserRole = Field(default=UserRole.AGENT, description="Client role — not user-settable via API")
    api_key_hash: Optional[str] = None
    certificate_fingerprint: Optional[str] = None
    is_active: bool = True
    quota_per_day: int = Field(default=1000, description="Daily search quota")
    quota_per_month: int = Field(default=30000, description="Monthly search quota")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class PolicyScope(str, Enum):
    """Policy scope."""
    GLOBAL = "global"
    ORGANIZATION = "organization"
    USER = "user"


class Policy(BaseModel):
    """Search policy model."""
    policy_id: str = Field(..., description="Unique policy identifier")
    policy_name: str = Field(..., min_length=3, max_length=100)
    scope: PolicyScope
    target_id: Optional[str] = None  # user_id or organization_id
    
    # Content filtering
    safe_search: bool = True
    blocked_keywords: List[str] = Field(default_factory=list)
    allowed_domains: Optional[List[str]] = None  # None means all allowed
    blocked_domains: List[str] = Field(default_factory=list)
    
    # Parental controls
    parental_control_enabled: bool = False
    min_age_rating: int = 0  # 0-18
    
    # Result controls
    max_results_per_query: int = 100
    enable_caching: bool = True
    
    # Provider preferences
    preferred_providers: List[str] = Field(default_factory=lambda: ["google", "bing"])
    
    is_active: bool = True
    priority: int = 0  # Higher priority policies override lower ones
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class SearchLog(BaseModel):
    """Search query log for audit and analytics."""
    log_id: str = Field(..., description="Unique log identifier")
    user_id: Optional[str] = None
    client_id: str
    query: str
    query_hash: str  # For analytics without storing full query
    provider_used: str
    results_count: int
    policies_applied: List[str] = Field(default_factory=list)
    filtered_results_count: int = 0
    response_time_ms: float
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class AuditAction(str, Enum):
    """Audit log actions."""
    USER_LOGIN = "user_login"
    USER_LOGOUT = "user_logout"
    POLICY_CREATED = "policy_created"
    POLICY_UPDATED = "policy_updated"
    POLICY_DELETED = "policy_deleted"
    CLIENT_CREATED = "client_created"
    CLIENT_UPDATED = "client_updated"
    CLIENT_DELETED = "client_deleted"
    API_KEY_GENERATED = "api_key_generated"
    API_KEY_REVOKED = "api_key_revoked"
    CONFIG_CHANGED = "config_changed"


class AuditLog(BaseModel):
    """Audit log for compliance."""
    log_id: str = Field(..., description="Unique log identifier")
    user_id: Optional[str] = None
    action: AuditAction
    resource_type: str
    resource_id: str
    details: Dict[str, Any] = Field(default_factory=dict)
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class Configuration(BaseModel):
    """System configuration."""
    key: str = Field(..., description="Configuration key")
    value: Any
    category: str = "general"
    description: Optional[str] = None
    is_sensitive: bool = False
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    updated_by: Optional[str] = None
