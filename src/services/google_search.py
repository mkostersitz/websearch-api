"""Google Custom Search API provider."""

import time
from typing import List, Optional
from datetime import datetime
import httpx
from loguru import logger

from src.models.search import SearchProvider, SearchResult, SearchResultType, ProviderStatus
from src.core.config import settings
from src.middleware.tracing import trace_function


class GoogleSearchProvider(SearchProvider):
    """Google Custom Search API implementation."""
    
    def __init__(self):
        super().__init__("google")
        self.api_key = settings.google_api_key
        self.search_engine_id = settings.google_search_engine_id
        self.base_url = "https://www.googleapis.com/customsearch/v1"
        self.timeout = settings.search_timeout_seconds
    
    @trace_function("google_search")
    async def search(
        self,
        query: str,
        max_results: int = 10,
        safe_search: bool = True,
        **kwargs
    ) -> List[SearchResult]:
        """Perform Google Custom Search."""
        
        if not self.api_key or not self.search_engine_id:
            logger.error("Google API key or Search Engine ID not configured")
            return []
        
        try:
            start_time = time.time()
            
            params = {
                "key": self.api_key,
                "cx": self.search_engine_id,
                "q": query,
                "num": min(max_results, 10),  # Google max is 10 per request
                "safe": "active" if safe_search else "off"
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    self.base_url,
                    params=params,
                    timeout=self.timeout
                )
                response.raise_for_status()
                data = response.json()
            
            duration_ms = (time.time() - start_time) * 1000
            
            # Parse results
            results = []
            items = data.get("items", [])
            
            for idx, item in enumerate(items[:max_results]):
                result = SearchResult(
                    title=item.get("title", ""),
                    url=item.get("link", ""),
                    snippet=item.get("snippet", ""),
                    result_type=self._determine_type(item),
                    provider=self.name,
                    rank=idx + 1,
                    thumbnail_url=item.get("pagemap", {}).get("cse_thumbnail", [{}])[0].get("src"),
                    metadata={
                        "display_link": item.get("displayLink"),
                        "html_snippet": item.get("htmlSnippet")
                    }
                )
                results.append(result)
            
            self._status = ProviderStatus.HEALTHY
            logger.info(f"Google search completed: {len(results)} results in {duration_ms:.0f}ms")
            
            return results
            
        except httpx.HTTPError as e:
            logger.error(f"Google search HTTP error: {e}")
            self._status = ProviderStatus.DEGRADED
            return []
        except Exception as e:
            logger.error(f"Google search error: {e}")
            self._status = ProviderStatus.UNAVAILABLE
            return []
    
    async def health_check(self) -> bool:
        """Check Google API health."""
        try:
            # Simple query to check API availability
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    self.base_url,
                    params={
                        "key": self.api_key,
                        "cx": self.search_engine_id,
                        "q": "test",
                        "num": 1
                    },
                    timeout=5.0
                )
                
                self._last_check = datetime.utcnow()
                
                if response.status_code == 200:
                    self._status = ProviderStatus.HEALTHY
                    return True
                else:
                    self._status = ProviderStatus.DEGRADED
                    return False
                    
        except Exception as e:
            logger.error(f"Google health check failed: {e}")
            self._status = ProviderStatus.UNAVAILABLE
            self._last_check = datetime.utcnow()
            return False
    
    def _determine_type(self, item: dict) -> SearchResultType:
        """Determine result type from item data."""
        mime_type = item.get("mime", "")
        file_format = item.get("fileFormat", "")
        
        if "image" in mime_type or "image" in file_format:
            return SearchResultType.IMAGE
        elif "video" in mime_type or "video" in file_format:
            return SearchResultType.VIDEO
        else:
            return SearchResultType.WEB
