"""Admin dashboard API routes."""

from datetime import datetime, timedelta
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status, Body
from loguru import logger
from pydantic import BaseModel

from src.middleware.api_key import get_api_key_client
from src.core.database import Database
from src.models.api import ClientResponse
from src.utils.audit_log import log_audit_event
from datetime import timezone


router = APIRouter(prefix="/admin", tags=["Admin Dashboard"])


# Admin verification dependency
async def verify_admin(current_client: dict = Depends(get_api_key_client)) -> dict:
    """Verify that the current client has admin role"""
    role = current_client.get("role")
    if role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return current_client


# Settings models
class SearchPolicySettings(BaseModel):
    level: str
    enabled: bool
    block_keywords: List[str]


class ParentalControlsSettings(BaseModel):
    enabled: bool
    age_restriction: int
    block_adult_content: bool
    block_violence: bool
    block_gambling: bool
    block_drugs: bool


class IntegrationsSettings(BaseModel):
    grafana_url: str
    prometheus_url: str
    jaeger_url: str


class UserSyncSourceConfig(BaseModel):
    server_url: Optional[str] = None
    domain: Optional[str] = None
    tenant_id: Optional[str] = None
    client_id: Optional[str] = None
    client_secret: Optional[str] = None
    base_dn: Optional[str] = None
    bind_user: Optional[str] = None
    bind_password: Optional[str] = None
    csv_path: Optional[str] = None
    sync_groups: Optional[bool] = True
    group_filter: Optional[str] = None
    user_filter: Optional[str] = None


class UserSyncSource(BaseModel):
    source_id: str
    name: str
    type: str  # 'active_directory', 'entra_id', 'okta', 'csv', 'ldap'
    enabled: bool
    config: UserSyncSourceConfig
    last_sync: Optional[str] = None
    last_sync_status: Optional[str] = None
    users_synced: Optional[int] = 0
    groups_synced: Optional[int] = 0


class UserSyncSettings(BaseModel):
    enabled: bool
    sync_interval_hours: int
    sources: List[UserSyncSource]
    group_sync_enabled: bool
    auto_create_users: bool
    auto_assign_policies: bool


class SystemSettings(BaseModel):
    otel_endpoint: str
    search_policy: SearchPolicySettings
    parental_controls: ParentalControlsSettings
    integrations: IntegrationsSettings
    user_sync: Optional[UserSyncSettings] = None


@router.get("/stats/overview")
async def get_overview_stats(
    current_client: dict = Depends(get_api_key_client)
):
    """Get overview statistics for the dashboard."""
    # Verify admin permissions
    if current_client.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    db = Database.get_db()
    
    # Count totals
    total_clients = await db.clients.count_documents({})
    total_users = await db.users.count_documents({})
    total_policies = await db.policies.count_documents({})
    
    # Get search statistics (last 24 hours)
    yesterday = datetime.utcnow() - timedelta(days=1)
    searches_24h = await db.search_logs.count_documents({
        "timestamp": {"$gte": yesterday}
    })
    
    # Get active clients (used in last 24h)
    active_clients_24h = len(await db.clients.distinct(
        "client_id",
        {"last_used": {"$gte": yesterday}}
    ))
    
    # Calculate average response time (last 100 searches)
    recent_searches = await db.search_logs.find(
        {},
        {"response_time_ms": 1}
    ).sort("timestamp", -1).limit(100).to_list(100)
    
    avg_response_time = 0
    if recent_searches:
        avg_response_time = sum(s.get("response_time_ms", 0) for s in recent_searches) / len(recent_searches)
    
    return {
        "total_clients": total_clients,
        "total_users": total_users,
        "total_policies": total_policies,
        "searches_24h": searches_24h,
        "active_clients_24h": active_clients_24h,
        "avg_response_time_ms": round(avg_response_time, 2),
        "timestamp": datetime.utcnow().isoformat()
    }


@router.get("/clients", response_model=List[ClientResponse])
async def list_all_clients(
    current_client: dict = Depends(get_api_key_client)
) -> List[ClientResponse]:
    """List all clients in the system (admin only)."""
    # Verify admin permissions
    if current_client.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    db = Database.get_db()
    
    # Get all clients
    clients_cursor = db.clients.find({})
    clients = await clients_cursor.to_list(length=1000)
    
    # Convert to response model, handling missing fields
    result = []
    for client in clients:
        # Ensure updated_at exists (use created_at if missing)
        if "updated_at" not in client:
            client["updated_at"] = client.get("created_at", datetime.utcnow())
        
        # Ensure metadata exists
        if "metadata" not in client:
            client["metadata"] = {}
            
        result.append(ClientResponse(**client))
    
    return result


@router.get("/stats/searches")
async def get_search_stats(
    current_client: dict = Depends(get_api_key_client),
    days: int = Query(7, ge=1, le=90, description="Number of days to analyze")
):
    """Get search statistics over time."""
    if current_client.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    db = Database.get_db()
    start_date = datetime.utcnow() - timedelta(days=days)
    
    # Aggregate searches by day
    pipeline = [
        {"$match": {"timestamp": {"$gte": start_date}}},
        {"$group": {
            "_id": {
                "$dateToString": {
                    "format": "%Y-%m-%d",
                    "date": "$timestamp"
                }
            },
            "count": {"$sum": 1},
            "avg_response_time": {"$avg": "$response_time_ms"},
            "total_results": {"$sum": "$total_results"}
        }},
        {"$sort": {"_id": 1}}
    ]
    
    daily_stats = await db.search_logs.aggregate(pipeline).to_list(days)
    
    return {
        "period_days": days,
        "start_date": start_date.isoformat(),
        "end_date": datetime.utcnow().isoformat(),
        "daily_stats": [
            {
                "date": stat["_id"],
                "searches": stat["count"],
                "avg_response_time_ms": round(stat["avg_response_time"], 2),
                "total_results": stat["total_results"]
            }
            for stat in daily_stats
        ]
    }


@router.get("/stats/providers")
async def get_provider_stats(
    current_client: dict = Depends(get_api_key_client),
    days: int = Query(7, ge=1, le=90)
):
    """Get search provider usage statistics."""
    if current_client.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    db = Database.get_db()
    start_date = datetime.utcnow() - timedelta(days=days)
    
    # Aggregate by provider
    pipeline = [
        {"$match": {"timestamp": {"$gte": start_date}}},
        {"$group": {
            "_id": "$provider",
            "count": {"$sum": 1},
            "avg_response_time": {"$avg": "$response_time_ms"},
            "avg_results": {"$avg": "$total_results"}
        }}
    ]
    
    provider_stats = await db.search_logs.aggregate(pipeline).to_list(10)
    
    return {
        "period_days": days,
        "providers": [
            {
                "provider": stat["_id"],
                "searches": stat["count"],
                "avg_response_time_ms": round(stat["avg_response_time"], 2),
                "avg_results": round(stat["avg_results"], 2)
            }
            for stat in provider_stats
        ]
    }


@router.get("/stats/top-queries")
async def get_top_queries(
    current_client: dict = Depends(get_api_key_client),
    limit: int = Query(10, ge=1, le=100),
    days: int = Query(7, ge=1, le=90)
):
    """Get most frequent search queries."""
    if current_client.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    db = Database.get_db()
    start_date = datetime.utcnow() - timedelta(days=days)
    
    # Aggregate by query
    pipeline = [
        {"$match": {"timestamp": {"$gte": start_date}}},
        {"$group": {
            "_id": "$query",
            "count": {"$sum": 1},
            "unique_clients": {"$addToSet": "$client_id"}
        }},
        {"$project": {
            "query": "$_id",
            "count": 1,
            "unique_clients": {"$size": "$unique_clients"}
        }},
        {"$sort": {"count": -1}},
        {"$limit": limit}
    ]
    
    top_queries = await db.search_logs.aggregate(pipeline).to_list(limit)
    
    return {
        "period_days": days,
        "top_queries": [
            {
                "query": q["query"],
                "search_count": q["count"],
                "unique_clients": q["unique_clients"]
            }
            for q in top_queries
        ]
    }


@router.get("/audit-logs")
async def get_audit_logs(
    current_client: dict = Depends(get_api_key_client),
    limit: int = Query(50, ge=1, le=500),
    skip: int = Query(0, ge=0),
    action_type: Optional[str] = Query(None),
    client_id: Optional[str] = Query(None)
):
    """Query audit logs with filtering and pagination."""
    if current_client.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    db = Database.get_db()
    
    # Build query filter
    query_filter = {}
    if action_type:
        query_filter["action_type"] = action_type
    if client_id:
        query_filter["client_id"] = client_id
    
    # Get total count
    total = await db.audit_logs.count_documents(query_filter)
    
    # Get logs
    logs_cursor = db.audit_logs.find(query_filter).sort(
        "timestamp", -1
    ).skip(skip).limit(limit)
    
    logs = []
    async for log in logs_cursor:
        # Convert ObjectId to string
        if "_id" in log:
            log["_id"] = str(log["_id"])
        logs.append(log)
    
    return {
        "total": total,
        "skip": skip,
        "limit": limit,
        "logs": logs
    }


@router.get("/system/health")
async def get_system_health(
    current_client: dict = Depends(get_api_key_client)
):
    """Get system health metrics."""
    if current_client.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    db = Database.get_db()
    
    # Check database
    try:
        await db.command("ping")
        db_status = "healthy"
    except:
        db_status = "unhealthy"
    
    # Check Redis (rate limiter)
    from src.services.rate_limiter import rate_limiter
    try:
        if rate_limiter.redis_client:
            redis_info = await rate_limiter.redis_client.info()
            redis_status = "healthy"
            redis_memory = redis_info.get("used_memory_human", "unknown")
        else:
            # Redis client not initialized yet
            redis_status = "unhealthy"
            redis_memory = "unknown"
    except Exception as e:
        logger.error(f"Redis health check failed: {e}")
        redis_status = "unhealthy"
        redis_memory = "unknown"
    
    return {
        "status": "healthy" if db_status == "healthy" and redis_status == "healthy" else "degraded",
        "components": {
            "database": {
                "status": db_status,
                "type": "MongoDB"
            },
            "cache": {
                "status": redis_status,
                "type": "Redis",
                "memory_used": redis_memory
            }
        },
        "timestamp": datetime.utcnow().isoformat()
    }


@router.get("/settings")
async def get_settings(
    current_client: dict = Depends(get_api_key_client)
):
    """Get system settings."""
    if current_client.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    db = Database.get_db()
    
    # Get settings from database or return defaults
    settings_doc = await db.system_settings.find_one({"_id": "system"})
    
    if not settings_doc:
        # Return default settings
        default_settings = {
            "otel_endpoint": "http://localhost:5317",
            "search_policy": {
                "level": "moderate",
                "enabled": True,
                "block_keywords": ["adult", "explicit", "violence", "gambling"]
            },
            "parental_controls": {
                "enabled": False,
                "age_restriction": 13,
                "block_adult_content": True,
                "block_violence": True,
                "block_gambling": False,
                "block_drugs": False
            },
            "integrations": {
                "grafana_url": "http://localhost:3002",
                "prometheus_url": "http://localhost:9091",
                "jaeger_url": "http://localhost:17686"
            },
            "user_sync": {
                "enabled": False,
                "sync_interval_hours": 24,
                "sources": [],
                "group_sync_enabled": True,
                "auto_create_users": True,
                "auto_assign_policies": False
            }
        }
        return default_settings
    
    # Remove MongoDB _id field
    settings_doc.pop("_id", None)
    return settings_doc


@router.put("/settings")
async def update_settings(
    settings: SystemSettings = Body(...),
    current_client: dict = Depends(get_api_key_client)
):
    """Update system settings."""
    if current_client.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    db = Database.get_db()
    
    # Validate settings
    if settings.search_policy.level not in ["strict", "moderate", "open", "custom"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid search policy level"
        )
    
    if settings.parental_controls.age_restriction not in [13, 16, 18]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Age restriction must be 13, 16, or 18"
        )
    
    # Convert to dict
    settings_dict = settings.model_dump()
    settings_dict["updated_at"] = datetime.utcnow()
    settings_dict["updated_by"] = current_client.get("client_id")
    
    # Upsert settings
    await db.system_settings.update_one(
        {"_id": "system"},
        {"$set": settings_dict},
        upsert=True
    )
    
    # Log audit entry
    await db.audit_logs.insert_one({
        "audit_id": f"audit_{datetime.utcnow().timestamp()}",
        "timestamp": datetime.utcnow(),
        "client_id": current_client.get("client_id"),
        "action": "UPDATE_SETTINGS",
        "resource_type": "system_settings",
        "resource_id": "system",
        "status": "success",
        "details": {
            "search_policy_level": settings.search_policy.level,
            "parental_controls_enabled": settings.parental_controls.enabled
        }
    })
    
    logger.info(f"System settings updated by {current_client.get('client_id')}")
    
    # Remove internal fields before returning
    settings_dict.pop("updated_at", None)
    settings_dict.pop("updated_by", None)
    
    return settings_dict



@router.post("/reset-to-defaults")
async def reset_to_defaults(
    current_client: dict = Depends(verify_admin)
):
    """
    Reset system to defaults by deleting all users, groups, and custom policies
    except the required defaults (admin user, admins group, default policies).
    
    **Warning: This action cannot be undone!**
    """
    db = Database.get_db()
    
    # Delete all users except admin
    users = db.users
    delete_result = await users.delete_many({
        "username": {"$ne": "admin"}
    })
    users_deleted = delete_result.deleted_count
    
    # Reset admin to default password
    from src.api.routes.auth import hash_password
    await users.update_one(
        {"username": "admin"},
        {
            "$set": {
                "password_hash": hash_password("admin"),
                "first_login": True,
                "email": "admin@websearch.local",
                "name": "Administrator",
                "groups": ["admins"],
                "role": "admin",
                "is_active": True,
                "metadata": {
                    "reset_at": datetime.now(timezone.utc).isoformat()
                }
            },
            "$unset": {
                "api_key_hash": "",
                "last_key_generated": ""
            }
        }
    )
    
    # Delete all groups except admins
    groups = db.groups
    delete_result = await groups.delete_many({
        "group_id": {"$ne": "admins"}
    })
    groups_deleted = delete_result.deleted_count
    
    # Delete all custom policies (keep enterprise default)
    policies = db.policies
    delete_result = await policies.delete_many({
        "policy_id": {"$nin": ["enterprise_default", "safe_search_strict"]}
    })
    policies_deleted = delete_result.deleted_count
    
    # Delete all clients except system clients
    clients = db.clients
    delete_result = await clients.delete_many({
        "client_id": {"$nin": ["system", "monitor", "health_check"]}
    })
    clients_deleted = delete_result.deleted_count
    
    # Clear audit logs older than 7 days (keep recent for debugging)
    audit_logs = db.audit_logs
    seven_days_ago = datetime.now(timezone.utc).timestamp() - (7 * 24 * 3600)
    delete_result = await audit_logs.delete_many({
        "timestamp": {"$lt": datetime.fromtimestamp(seven_days_ago, tz=timezone.utc)}
    })
    logs_deleted = delete_result.deleted_count
    
    # Log the reset action
    await log_audit_event(
        db=db,
        client_id=current_client.get("client_id", "unknown"),
        action="system_reset",
        resource_type="system",
        resource_id="reset_to_defaults",
        user_id=current_client.get("owner_id"),
        details={
            "users_deleted": users_deleted,
            "groups_deleted": groups_deleted,
            "policies_deleted": policies_deleted,
            "clients_deleted": clients_deleted,
            "old_logs_deleted": logs_deleted,
            "performed_by": current_client.get("client_name", "Unknown")
        }
    )
    
    return {
        "success": True,
        "message": "System reset to defaults successfully",
        "deleted": {
            "users": users_deleted,
            "groups": groups_deleted,
            "policies": policies_deleted,
            "clients": clients_deleted,
            "old_audit_logs": logs_deleted
        },
        "defaults_restored": {
            "admin_user": "admin/admin (must change on first login)",
            "admin_group": "admins",
            "default_policies": ["enterprise_default", "safe_search_strict"]
        }
    }
