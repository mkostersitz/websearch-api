"""Search API endpoints."""

import time
import uuid
from typing import Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status, Request
from loguru import logger

from src.models.api_search import SearchRequest, SearchResponse, SearchResultResponse
from src.models.database import SearchLog
from src.middleware.api_key import get_api_key_client
from src.middleware.tracing import trace_function
from src.services.search_manager import search_manager
from src.services.policy_engine import policy_engine
from src.services.rate_limiter import rate_limiter
from src.core.database import Database


router = APIRouter()


@router.post("/search", response_model=SearchResponse)
@trace_function("search_endpoint")
async def search(
    request: SearchRequest,
    http_request: Request,
    current_client: dict = Depends(get_api_key_client)
) -> SearchResponse:
    """
    Perform a web search with policy enforcement and rate limiting.
    
    - **query**: Search query string (1-500 characters)
    - **max_results**: Maximum number of results to return (1-100, default: 10)
    - **safe_search**: Enable safe search filtering (default: true)
    - **preferred_provider**: Preferred search provider (optional)
    
    Returns filtered search results based on applicable policies.
    Rate limited per client based on configured quotas.
    """
    start_time = time.time()
    client_id = current_client.get("client_id")
    owner_id = current_client.get("owner_id")
    
    logger.info(f"Search request from client {client_id}: {request.query}")
    
    try:
        # 1. Check rate limit
        is_allowed, limit_info = await rate_limiter.check_rate_limit(
            key=client_id,
            limit=60  # 60 requests per minute
        )
        
        if not is_allowed:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Rate limit exceeded",
                headers={
                    "X-RateLimit-Limit": str(limit_info["limit"]),
                    "X-RateLimit-Remaining": str(limit_info["remaining"]),
                    "X-RateLimit-Reset": str(limit_info["reset"])
                }
            )
        
        # 2. Check quota
        quota_per_day = current_client.get("quota_per_day", 1000)
        quota_per_month = current_client.get("quota_per_month", 30000)
        
        is_quota_ok, quota_info = await rate_limiter.check_quota(
            key=client_id,
            daily_limit=quota_per_day,
            monthly_limit=quota_per_month
        )
        
        if not is_quota_ok:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Quota exceeded",
                headers={
                    "X-Quota-Daily-Remaining": str(quota_info["daily"]["remaining"]),
                    "X-Quota-Monthly-Remaining": str(quota_info["monthly"]["remaining"])
                }
            )
        
        # 3. Get applicable policies
        policies = await policy_engine.get_applicable_policies(
            user_id=owner_id,
            client_id=client_id
        )
        
        effective_policy = policy_engine.merge_policies(policies)
        logger.info(f"Applied {len(policies)} policies for client {client_id}")
        
        # 4. Apply policy limits to request
        max_results = min(request.max_results, effective_policy.max_results_per_query)
        safe_search = request.safe_search or effective_policy.safe_search
        
        # 5. Perform search
        search_response = await search_manager.search(
            query=request.query,
            max_results=max_results,
            safe_search=safe_search,
            preferred_provider=request.preferred_provider
        )
        
        # 6. Apply policy filters to results
        filtered_results, filtered_count = await policy_engine.apply_policy(
            results=search_response.results,
            policy=effective_policy
        )
        
        # 7. Increment quota usage
        await rate_limiter.increment_quota(client_id, "day", 1)
        await rate_limiter.increment_quota(client_id, "month", 1)
        
        # 8. Log search for audit
        log_id = str(uuid.uuid4())
        search_log = SearchLog(
            log_id=log_id,
            user_id=owner_id,
            client_id=client_id,
            query=request.query,
            query_hash=search_response.query_hash,
            provider_used=search_response.provider,
            results_count=len(filtered_results),
            policies_applied=[p.policy_id for p in policies],
            filtered_results_count=filtered_count,
            response_time_ms=search_response.response_time_ms,
            ip_address=http_request.client.host if http_request.client else None,
            user_agent=http_request.headers.get("user-agent"),
            metadata={
                "safe_search": safe_search,
                "max_results": max_results,
                "preferred_provider": request.preferred_provider
            }
        )
        
        # Store in database (non-blocking)
        db = Database.get_db()
        await db.search_logs.insert_one(search_log.model_dump())
        
        # 9. Build response
        response = SearchResponse(
            query=search_response.query,
            results=[
                SearchResultResponse(**result.model_dump())
                for result in filtered_results
            ],
            total_results=len(filtered_results),
            filtered_results=filtered_count,
            provider=search_response.provider,
            response_time_ms=(time.time() - start_time) * 1000,
            cached=search_response.cached,
            timestamp=datetime.utcnow(),
            policies_applied=[p.policy_id for p in policies],
            rate_limit_info=limit_info,
            quota_info=quota_info
        )
        
        logger.info(
            f"Search completed: {len(filtered_results)} results, "
            f"{response.response_time_ms:.0f}ms, provider: {search_response.provider}"
        )
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Search failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Search failed"
        )


@router.get("/search/providers")
async def get_provider_status(
    current_client: dict = Depends(get_api_key_client)
) -> dict:
    """
    Get status of all search providers.
    
    Returns health status and availability of each configured provider.
    """
    return search_manager.get_provider_status()


@router.post("/search/providers/health-check")
async def check_providers_health(
    current_client: dict = Depends(get_api_key_client)
) -> dict:
    """
    Trigger health check for all providers.
    
    Performs active health check on all configured search providers
    and returns their current status.
    """
    results = await search_manager.check_all_providers()
    return {"providers": results, "timestamp": datetime.utcnow().isoformat()}
