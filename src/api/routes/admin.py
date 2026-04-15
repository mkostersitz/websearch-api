"""Admin dashboard API routes."""

from datetime import datetime, timedelta
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from loguru import logger

from src.middleware.api_key import get_api_key_client
from src.core.database import Database
from src.models.api import ClientResponse


router = APIRouter(prefix="/admin", tags=["Admin Dashboard"])


@router.get("/stats/overview")
async def get_overview_stats(
    current_client: dict = Depends(get_api_key_client)
):
    """Get overview statistics for the dashboard."""
    # Verify admin permissions
    if current_client.get("metadata", {}).get("role") != "admin":
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


@router.get("/stats/searches")
async def get_search_stats(
    current_client: dict = Depends(get_api_key_client),
    days: int = Query(7, ge=1, le=90, description="Number of days to analyze")
):
    """Get search statistics over time."""
    if current_client.get("metadata", {}).get("role") != "admin":
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
    if current_client.get("metadata", {}).get("role") != "admin":
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
    if current_client.get("metadata", {}).get("role") != "admin":
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
    if current_client.get("metadata", {}).get("role") != "admin":
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
    logs = await db.audit_logs.find(query_filter).sort(
        "timestamp", -1
    ).skip(skip).limit(limit).to_list(limit)
    
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
    if current_client.get("metadata", {}).get("role") != "admin":
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
    from src.services.rate_limiter import RateLimiter
    try:
        redis_info = await RateLimiter.redis.info()
        redis_status = "healthy"
        redis_memory = redis_info.get("used_memory_human", "unknown")
    except:
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
