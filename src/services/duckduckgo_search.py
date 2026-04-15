"""DuckDuckGo search provider implementation."""

import time
from typing import List, Optional
from datetime import datetime
from loguru import logger

from src.models.search import SearchProvider, SearchResult, SearchResultType, ProviderStatus
from src.core.config import settings
from src.middleware.tracing import trace_function


class DuckDuckGoSearchProvider(SearchProvider):
    """
    DuckDuckGo search implementation using duckduckgo-search library.
    
    Note: DuckDuckGo doesn't require API keys, making it a great
    free alternative to Google and Bing. No authentication needed!
    """
    
    def __init__(self):
        super().__init__("duckduckgo")
        self.timeout = settings.search_timeout_seconds
    
    @trace_function("duckduckgo_search")
    async def search(
        self,
        query: str,
        max_results: int = 10,
        safe_search: bool = True,
        **kwargs
    ) -> List[SearchResult]:
        """
        Perform DuckDuckGo search.
        
        Args:
            query: Search query
            max_results: Maximum number of results to return
            safe_search: Enable safe search
            **kwargs: Additional search parameters
            
        Returns:
            List of SearchResult objects
        """
        try:
            from ddgs import DDGS
            
            start_time = time.time()
            
            # Use DDGS for search
            safesearch = "on" if safe_search else "off"
            results = []
            
            try:
                with DDGS() as ddgs:
                    # ddgs.text returns a generator, convert to list
                    search_results = list(ddgs.text(
                        query,
                        max_results=max_results,
                        safesearch=safesearch
                    ))
                    
                    for idx, item in enumerate(search_results):
                        result = SearchResult(
                            title=item.get('title', ''),
                            url=item.get('href', ''),
                            snippet=item.get('body', ''),
                            source="DuckDuckGo",
                            result_type=SearchResultType.WEB,
                            timestamp=datetime.utcnow(),
                            provider="duckduckgo",
                            rank=idx + 1
                        )
                        results.append(result)
                
                elapsed = (time.time() - start_time) * 1000
                logger.info(
                    f"DuckDuckGo search completed: query='{query}', "
                    f"results={len(results)}, time={elapsed:.2f}ms"
                )
                
                return results
                
            except Exception as e:
                logger.error(f"DuckDuckGo library error: {e}")
                return []
                
        except ImportError:
            logger.error("ddgs library not installed")
            return []
        except Exception as e:
            logger.error(f"DuckDuckGo search error: {e}", exc_info=True)
            return []
    
    async def health_check(self) -> ProviderStatus:
        """
        Check if DuckDuckGo is accessible.
        
        Returns:
            ProviderStatus with health information
        """
        try:
            import httpx
            start_time = time.time()
            
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get("https://duckduckgo.com/")
                response.raise_for_status()
            
            latency_ms = (time.time() - start_time) * 1000
            
            return ProviderStatus(
                name=self.name,
                healthy=True,
                enabled=True,
                latency_ms=latency_ms,
                last_check=datetime.utcnow(),
                message="DuckDuckGo is accessible"
            )
            
        except Exception as e:
            logger.error(f"DuckDuckGo health check failed: {e}")
            return ProviderStatus(
                name=self.name,
                healthy=False,
                enabled=True,
                latency_ms=0.0,
                last_check=datetime.utcnow(),
                message=f"Health check failed: {str(e)}"
            )
