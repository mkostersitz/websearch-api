"""Rate limiting with token bucket algorithm and Redis."""

import time
from typing import Optional
from datetime import datetime, timedelta
import redis.asyncio as redis
from fastapi import HTTPException, status
from loguru import logger

from src.core.config import settings
from src.middleware.tracing import trace_function


class RateLimiter:
    """Token bucket rate limiter using Redis."""
    
    def __init__(self):
        self.redis_client: Optional[redis.Redis] = None
        self.rate_limit_per_minute = settings.rate_limit_per_minute
        self.burst_limit = settings.rate_limit_burst
    
    async def connect(self):
        """Connect to Redis."""
        if not self.redis_client:
            self.redis_client = redis.from_url(
                settings.redis_url,
                encoding="utf-8",
                decode_responses=True
            )
            logger.info("Rate limiter connected to Redis")
    
    async def disconnect(self):
        """Disconnect from Redis."""
        if self.redis_client:
            await self.redis_client.close()
            logger.info("Rate limiter disconnected from Redis")
    
    @trace_function("check_rate_limit")
    async def check_rate_limit(
        self,
        key: str,
        limit: Optional[int] = None,
        window_seconds: int = 60
    ) -> tuple[bool, dict]:
        """
        Check if request is within rate limit using token bucket.
        
        Args:
            key: Unique identifier (e.g., client_id, user_id, ip_address)
            limit: Rate limit (requests per window), uses default if None
            window_seconds: Time window in seconds
            
        Returns:
            Tuple of (is_allowed, info_dict)
        """
        if not self.redis_client:
            await self.connect()
        
        limit = limit or self.rate_limit_per_minute
        current_time = time.time()
        
        # Redis key for this rate limit
        redis_key = f"ratelimit:{key}:{window_seconds}"
        
        try:
            # Lua script for atomic token bucket check
            lua_script = """
            local key = KEYS[1]
            local limit = tonumber(ARGV[1])
            local window = tonumber(ARGV[2])
            local current_time = tonumber(ARGV[3])
            local burst = tonumber(ARGV[4])
            
            -- Get current bucket state
            local bucket = redis.call('HMGET', key, 'tokens', 'last_refill')
            local tokens = tonumber(bucket[1]) or limit
            local last_refill = tonumber(bucket[2]) or current_time
            
            -- Calculate refill
            local time_passed = current_time - last_refill
            local refill_rate = limit / window
            local tokens_to_add = time_passed * refill_rate
            
            -- Refill tokens (up to limit + burst)
            tokens = math.min(tokens + tokens_to_add, limit + burst)
            
            -- Check if request is allowed
            if tokens >= 1 then
                tokens = tokens - 1
                redis.call('HMSET', key, 'tokens', tokens, 'last_refill', current_time)
                redis.call('EXPIRE', key, window * 2)
                return {1, math.floor(tokens), limit}
            else
                return {0, 0, limit}
            end
            """
            
            result = await self.redis_client.eval(
                lua_script,
                1,
                redis_key,
                limit,
                window_seconds,
                current_time,
                self.burst_limit
            )
            
            is_allowed = result[0] == 1
            remaining = result[1]
            total_limit = result[2]
            
            # Calculate reset time
            reset_time = int(current_time + window_seconds)
            
            info = {
                "limit": total_limit,
                "remaining": remaining,
                "reset": reset_time,
                "reset_time": datetime.fromtimestamp(reset_time).isoformat()
            }
            
            if not is_allowed:
                logger.warning(f"Rate limit exceeded for key: {key}")
            
            return is_allowed, info
            
        except Exception as e:
            logger.error(f"Rate limit check failed: {e}")
            # Fail open in case of Redis errors
            return True, {
                "limit": limit,
                "remaining": limit,
                "reset": int(current_time + window_seconds),
                "error": "rate_limiter_unavailable"
            }
    
    async def get_quota_usage(
        self,
        key: str,
        period: str = "day"
    ) -> dict:
        """
        Get quota usage statistics.
        
        Args:
            key: Unique identifier
            period: "day" or "month"
            
        Returns:
            Dict with usage stats
        """
        if not self.redis_client:
            await self.connect()
        
        # Get current period
        now = datetime.utcnow()
        if period == "day":
            period_key = now.strftime("%Y-%m-%d")
            period_seconds = 86400
        else:  # month
            period_key = now.strftime("%Y-%m")
            period_seconds = 2592000  # 30 days
        
        quota_key = f"quota:{key}:{period}:{period_key}"
        
        try:
            usage = await self.redis_client.get(quota_key)
            usage = int(usage) if usage else 0
            
            return {
                "period": period,
                "period_key": period_key,
                "usage": usage,
                "reset_time": (now + timedelta(seconds=period_seconds)).isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to get quota usage: {e}")
            return {"period": period, "usage": 0, "error": str(e)}
    
    async def increment_quota(
        self,
        key: str,
        period: str = "day",
        amount: int = 1
    ) -> int:
        """
        Increment quota usage.
        
        Args:
            key: Unique identifier
            period: "day" or "month"
            amount: Amount to increment
            
        Returns:
            New usage count
        """
        if not self.redis_client:
            await self.connect()
        
        now = datetime.utcnow()
        if period == "day":
            period_key = now.strftime("%Y-%m-%d")
            ttl = 86400 * 2  # Keep for 2 days
        else:  # month
            period_key = now.strftime("%Y-%m")
            ttl = 2592000 * 2  # Keep for 2 months
        
        quota_key = f"quota:{key}:{period}:{period_key}"
        
        try:
            # Increment and set expiry
            pipe = self.redis_client.pipeline()
            pipe.incr(quota_key, amount)
            pipe.expire(quota_key, ttl)
            results = await pipe.execute()
            
            return results[0]
            
        except Exception as e:
            logger.error(f"Failed to increment quota: {e}")
            return 0
    
    async def check_quota(
        self,
        key: str,
        daily_limit: int,
        monthly_limit: int
    ) -> tuple[bool, dict]:
        """
        Check if quota is exceeded.
        
        Args:
            key: Unique identifier
            daily_limit: Daily quota limit
            monthly_limit: Monthly quota limit
            
        Returns:
            Tuple of (is_allowed, quota_info)
        """
        # Check daily quota (-1 means unlimited)
        if daily_limit == -1:
            daily_usage = {"usage": 0}
            daily_remaining = -1
            daily_ok = True
        else:
            daily_usage = await self.get_quota_usage(key, "day")
            daily_remaining = max(0, daily_limit - daily_usage["usage"])
            daily_ok = daily_remaining > 0

        # Check monthly quota (-1 means unlimited)
        if monthly_limit == -1:
            monthly_usage = {"usage": 0}
            monthly_remaining = -1
            monthly_ok = True
        else:
            monthly_usage = await self.get_quota_usage(key, "month")
            monthly_remaining = max(0, monthly_limit - monthly_usage["usage"])
            monthly_ok = monthly_remaining > 0

        is_allowed = daily_ok and monthly_ok

        quota_info = {
            "daily": {
                "limit": daily_limit,
                "usage": daily_usage["usage"],
                "remaining": daily_remaining
            },
            "monthly": {
                "limit": monthly_limit,
                "usage": monthly_usage["usage"],
                "remaining": monthly_remaining
            }
        }
        
        if not is_allowed:
            logger.warning(f"Quota exceeded for key: {key}")
        
        return is_allowed, quota_info


# Global instance
rate_limiter = RateLimiter()


async def check_client_rate_limit(client: dict) -> dict:
    """
    FastAPI dependency to check rate limit for a client.
    
    Args:
        client: Client dict from auth middleware
        
    Returns:
        Rate limit info dict
        
    Raises:
        HTTPException: If rate limit exceeded
    """
    client_id = client.get("client_id")
    
    # Check rate limit
    is_allowed, limit_info = await rate_limiter.check_rate_limit(
        key=client_id,
        limit=settings.rate_limit_per_minute
    )
    
    if not is_allowed:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded",
            headers={
                "X-RateLimit-Limit": str(limit_info["limit"]),
                "X-RateLimit-Remaining": str(limit_info["remaining"]),
                "X-RateLimit-Reset": str(limit_info["reset"]),
                "Retry-After": str(limit_info["reset"] - int(time.time()))
            }
        )
    
    # Check quota
    quota_per_day = client.get("quota_per_day", 1000)
    quota_per_month = client.get("quota_per_month", 30000)
    
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
                "X-Quota-Daily-Limit": str(quota_info["daily"]["limit"]),
                "X-Quota-Daily-Remaining": str(quota_info["daily"]["remaining"]),
                "X-Quota-Monthly-Limit": str(quota_info["monthly"]["limit"]),
                "X-Quota-Monthly-Remaining": str(quota_info["monthly"]["remaining"])
            }
        )
    
    return {
        "rate_limit": limit_info,
        "quota": quota_info
    }
