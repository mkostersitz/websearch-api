"""Enhanced policy models with comprehensive access controls."""

from datetime import datetime, time
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from enum import Enum


class DayOfWeek(str, Enum):
    """Days of the week."""
    MONDAY = "monday"
    TUESDAY = "tuesday"
    WEDNESDAY = "wednesday"
    THURSDAY = "thursday"
    FRIDAY = "friday"
    SATURDAY = "saturday"
    SUNDAY = "sunday"


class AccessSchedule(BaseModel):
    """Access schedule definition."""
    enabled: bool = False
    days: List[DayOfWeek] = Field(default_factory=lambda: [
        DayOfWeek.MONDAY, DayOfWeek.TUESDAY, DayOfWeek.WEDNESDAY,
        DayOfWeek.THURSDAY, DayOfWeek.FRIDAY
    ])
    start_time: str = "09:00"  # HH:MM format
    end_time: str = "17:00"    # HH:MM format
    timezone: str = "UTC"


class ParentalControlPolicy(BaseModel):
    """Parental control settings."""
    enabled: bool = False
    age_restriction: int = Field(default=13, ge=0, le=18)
    block_adult_content: bool = True
    block_violence: bool = True
    block_gambling: bool = True
    block_drugs: bool = True
    block_profanity: bool = False
    safe_search_forced: bool = True


class QueryLimits(BaseModel):
    """Query limits and quotas."""
    queries_per_hour: Optional[int] = None
    queries_per_day: Optional[int] = 1000
    queries_per_month: Optional[int] = 30000
    max_query_length: int = 500
    max_results_per_query: int = 100
    rate_limit_enabled: bool = True


class AdminPermissions(BaseModel):
    """Admin dashboard permissions."""
    dashboard_access: bool = False
    view_analytics: bool = False
    view_metrics: bool = False
    view_audit_logs: bool = False
    manage_users: bool = False
    manage_groups: bool = False
    manage_policies: bool = False
    manage_clients: bool = False
    manage_settings: bool = False
    view_system_health: bool = False


class SearchPermissions(BaseModel):
    """Search API permissions."""
    search_enabled: bool = True
    enable_caching: bool = True
    allowed_providers: List[str] = Field(default_factory=lambda: ["google", "bing"])
    blocked_keywords: List[str] = Field(default_factory=list)
    allowed_domains: Optional[List[str]] = None
    blocked_domains: List[str] = Field(default_factory=list)
    require_safe_search: bool = True


class PolicyScope(str, Enum):
    """Policy scope."""
    GLOBAL = "global"
    GROUP = "group"
    USER = "user"


class EnhancedPolicy(BaseModel):
    """Comprehensive policy model with all access controls."""
    policy_id: str = Field(..., description="Unique policy identifier")
    policy_name: str = Field(..., min_length=3, max_length=100)
    description: Optional[str] = None
    scope: PolicyScope
    
    # Targets
    target_user_ids: List[str] = Field(default_factory=list)
    target_group_ids: List[str] = Field(default_factory=list)
    
    # Access schedule
    access_schedule: AccessSchedule = Field(default_factory=AccessSchedule)
    
    # Parental controls
    parental_controls: ParentalControlPolicy = Field(default_factory=ParentalControlPolicy)
    
    # Query limits
    query_limits: QueryLimits = Field(default_factory=QueryLimits)
    
    # Admin permissions
    admin_permissions: AdminPermissions = Field(default_factory=AdminPermissions)
    
    # Search permissions
    search_permissions: SearchPermissions = Field(default_factory=SearchPermissions)
    
    # Policy metadata
    is_active: bool = True
    priority: int = Field(default=0, description="Higher priority overrides lower")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    created_by: Optional[str] = None
    updated_by: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class PolicyCreateRequest(BaseModel):
    """Request to create a new policy."""
    policy_name: str = Field(..., min_length=3, max_length=100)
    description: Optional[str] = None
    scope: PolicyScope
    target_user_ids: List[str] = Field(default_factory=list)
    target_group_ids: List[str] = Field(default_factory=list)
    access_schedule: Optional[AccessSchedule] = None
    parental_controls: Optional[ParentalControlPolicy] = None
    query_limits: Optional[QueryLimits] = None
    admin_permissions: Optional[AdminPermissions] = None
    search_permissions: Optional[SearchPermissions] = None
    priority: int = 0


class PolicyUpdateRequest(BaseModel):
    """Request to update a policy."""
    policy_name: Optional[str] = None
    description: Optional[str] = None
    target_user_ids: Optional[List[str]] = None
    target_group_ids: Optional[List[str]] = None
    access_schedule: Optional[AccessSchedule] = None
    parental_controls: Optional[ParentalControlPolicy] = None
    query_limits: Optional[QueryLimits] = None
    admin_permissions: Optional[AdminPermissions] = None
    search_permissions: Optional[SearchPermissions] = None
    is_active: Optional[bool] = None
    priority: Optional[int] = None
