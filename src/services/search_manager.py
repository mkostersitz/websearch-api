"""Search provider manager with fallback support."""

import time
from typing import List, Optional
from datetime import datetime
from loguru import logger

from src.models.search import SearchProvider, SearchResult, SearchResponse, ProviderStatus
from src.services.google_search import GoogleSearchProvider
from src.services.bing_search import BingSearchProvider
from src.middleware.tracing import trace_function


class SearchProviderManager:
    """Manages multiple search providers with fallback logic."""
    
    def __init__(self):
        self.providers: List[SearchProvider] = []
        self._initialize_providers()
    
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
                    
                    return SearchResponse(
                        query=query,
                        query_hash=provider._compute_query_hash(query),
                        results=results,
                        total_results=len(results),
                        provider=provider.name,
                        response_time_ms=duration_ms,
                        cached=False
                    )
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
