"""Search provider manager with fallback support."""

import hashlib
import json
import time
from typing import List, Optional
from datetime import datetime
from loguru import logger
import redis.asyncio as redis

from src.core.config import settings
from src.models.search import SearchProvider, SearchResult, SearchResponse, ProviderStatus
from src.services.google_search import GoogleSearchProvider
from src.services.bing_search import BingSearchProvider
from src.middleware.tracing import trace_function


class SearchProviderManager:
    """Manages multiple search providers with fallback logic."""

    def __init__(self):
        self.providers: List[SearchProvider] = []
        self._redis: Optional[redis.Redis] = None
        self._initialize_providers()

    async def _get_redis(self) -> redis.Redis:
        if not self._redis:
            self._redis = redis.from_url(
                settings.redis_url,
                encoding="utf-8",
                decode_responses=True
            )
        return self._redis

    def _cache_key(self, query: str, max_results: int, safe_search: bool) -> str:
        raw = f"{query}|{max_results}|{safe_search}"
        digest = hashlib.sha256(raw.encode()).hexdigest()[:24]
        return f"search_cache:{digest}"

    async def _get_cached(self, key: str) -> Optional[SearchResponse]:
        try:
            r = await self._get_redis()
            data = await r.get(key)
            if data:
                payload = json.loads(data)
                results = [SearchResult(**res) for res in payload["results"]]
                return SearchResponse(
                    query=payload["query"],
                    query_hash=payload["query_hash"],
                    results=results,
                    total_results=payload["total_results"],
                    provider=payload["provider"],
                    response_time_ms=payload["response_time_ms"],
                    cached=True
                )
        except Exception as e:
            logger.warning(f"Cache read failed: {e}")
        return None

    async def _set_cached(self, key: str, response: SearchResponse) -> None:
        try:
            r = await self._get_redis()
            payload = {
                "query": response.query,
                "query_hash": response.query_hash,
                "results": [res.model_dump() for res in response.results],
                "total_results": response.total_results,
                "provider": response.provider,
                "response_time_ms": response.response_time_ms,
            }
            await r.set(key, json.dumps(payload), ex=settings.search_cache_ttl_seconds)
        except Exception as e:
            logger.warning(f"Cache write failed: {e}")
    
    def _initialize_providers(self):
        """Initialize available search providers."""
        # Add DuckDuckGo provider (no API key needed - always available!)
        from src.services.duckduckgo_search import DuckDuckGoSearchProvider
        duckduckgo = DuckDuckGoSearchProvider()
        self.providers.append(duckduckgo)
        
        # Add Google provider
        google = GoogleSearchProvider()
        self.providers.append(google)
        
        # Add Bing provider
        bing = BingSearchProvider()
        self.providers.append(bing)
        
        logger.info(f"Initialized {len(self.providers)} search providers")
    
    @trace_function("search_with_fallback")
    async def search(
        self,
        query: str,
        max_results: int = 10,
        safe_search: bool = True,
        preferred_provider: Optional[str] = None,
        **kwargs
    ) -> SearchResponse:
        """
        Perform search with automatic fallback.
        
        Args:
            query: Search query
            max_results: Maximum results to return
            safe_search: Enable safe search
            preferred_provider: Preferred provider name (e.g., 'google', 'bing')
            **kwargs: Additional parameters
            
        Returns:
            SearchResponse with results
        """
        start_time = time.time()

        # Check cache first
        cache_key = self._cache_key(query, max_results, safe_search)
        cached = await self._get_cached(cache_key)
        if cached:
            logger.info(f"Cache hit for query: {query!r}")
            cached.response_time_ms = (time.time() - start_time) * 1000
            return cached

        # Determine provider order
        providers = self._get_provider_order(preferred_provider)

        # Try each provider until one succeeds
        for provider in providers:
            try:
                logger.info(f"Attempting search with provider: {provider.name}")
                
                results = await provider.search(
                    query=query,
                    max_results=max_results,
                    safe_search=safe_search,
                    **kwargs
                )
                
                if results:
                    duration_ms = (time.time() - start_time) * 1000
                    response = SearchResponse(
                        query=query,
                        query_hash=provider._compute_query_hash(query),
                        results=results,
                        total_results=len(results),
                        provider=provider.name,
                        response_time_ms=duration_ms,
                        cached=False
                    )
                    await self._set_cached(cache_key, response)
                    return response
                else:
                    logger.warning(f"Provider {provider.name} returned no results")
                    
            except Exception as e:
                logger.error(f"Provider {provider.name} failed: {e}")
                continue
        
        # All providers failed
        duration_ms = (time.time() - start_time) * 1000
        logger.error("All search providers failed")
        
        return SearchResponse(
            query=query,
            query_hash=GoogleSearchProvider()._compute_query_hash(query),
            results=[],
            total_results=0,
            provider="none",
            response_time_ms=duration_ms,
            cached=False
        )
    
    def _get_provider_order(self, preferred: Optional[str] = None) -> List[SearchProvider]:
        """
        Get ordered list of providers based on preference and health.
        
        Args:
            preferred: Preferred provider name
            
        Returns:
            Ordered list of providers
        """
        # Sort providers by: preferred first, then healthy, then degraded
        def sort_key(provider: SearchProvider) -> tuple:
            is_preferred = 0 if provider.name == preferred else 1
            
            if provider.status == ProviderStatus.HEALTHY:
                health_rank = 0
            elif provider.status == ProviderStatus.DEGRADED:
                health_rank = 1
            else:
                health_rank = 2
            
            return (is_preferred, health_rank)
        
        return sorted(self.providers, key=sort_key)
    
    async def check_all_providers(self) -> dict:
        """
        Check health of all providers.
        
        Returns:
            Dict mapping provider names to health status
        """
        results = {}
        
        for provider in self.providers:
            is_healthy = await provider.health_check()
            results[provider.name] = {
                "healthy": is_healthy,
                "status": provider.status.value,
                "last_check": provider.last_check.isoformat() if provider.last_check else None
            }
        
        return results
    
    def get_provider_status(self) -> dict:
        """Get current status of all providers."""
        return {
            provider.name: {
                "status": provider.status.value,
                "last_check": provider.last_check.isoformat() if provider.last_check else None
            }
            for provider in self.providers
        }


# Global instance
search_manager = SearchProviderManager()
