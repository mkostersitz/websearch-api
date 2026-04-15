"""Bing Search API provider."""

import time
from typing import List, Optional
from datetime import datetime
import httpx
from loguru import logger

from src.models.search import SearchProvider, SearchResult, SearchResultType, ProviderStatus
from src.core.config import settings
from src.middleware.tracing import trace_function


class BingSearchProvider(SearchProvider):
    """Bing Search API implementation."""
    
    def __init__(self):
        super().__init__("bing")
        self.api_key = settings.bing_api_key
        self.base_url = "https://api.bing.microsoft.com/v7.0/search"
        self.timeout = settings.search_timeout_seconds
    
    @trace_function("bing_search")
    async def search(
        self,
        query: str,
        max_results: int = 10,
        safe_search: bool = True,
        **kwargs
    ) -> List[SearchResult]:
        """Perform Bing Search."""
        
        if not self.api_key:
            logger.error("Bing API key not configured")
            return []
        
        try:
            start_time = time.time()
            
            headers = {
                "Ocp-Apim-Subscription-Key": self.api_key
            }
            
            params = {
                "q": query,
                "count": min(max_results, 50),  # Bing max is 50
                "safeSearch": "Strict" if safe_search else "Off",
                "responseFilter": "Webpages"
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    self.base_url,
                    headers=headers,
                    params=params,
                    timeout=self.timeout
                )
                response.raise_for_status()
                data = response.json()
            
            duration_ms = (time.time() - start_time) * 1000
            
            # Parse results
            results = []
            web_pages = data.get("webPages", {}).get("value", [])
            
            for idx, item in enumerate(web_pages[:max_results]):
                # Parse date if available
                published_date = None
                if "dateLastCrawled" in item:
                    try:
                        published_date = datetime.fromisoformat(item["dateLastCrawled"].replace("Z", "+00:00"))
                    except:
                        pass
                
                result = SearchResult(
                    title=item.get("name", ""),
                    url=item.get("url", ""),
                    snippet=item.get("snippet", ""),
                    result_type=SearchResultType.WEB,
                    provider=self.name,
                    rank=idx + 1,
                    published_date=published_date,
                    metadata={
                        "display_url": item.get("displayUrl"),
                        "language": item.get("language")
                    }
                )
                results.append(result)
            
            self._status = ProviderStatus.HEALTHY
            logger.info(f"Bing search completed: {len(results)} results in {duration_ms:.0f}ms")
            
            return results
            
        except httpx.HTTPError as e:
            logger.error(f"Bing search HTTP error: {e}")
            self._status = ProviderStatus.DEGRADED
            return []
        except Exception as e:
            logger.error(f"Bing search error: {e}")
            self._status = ProviderStatus.UNAVAILABLE
            return []
    
    async def health_check(self) -> bool:
        """Check Bing API health."""
        try:
            headers = {
                "Ocp-Apim-Subscription-Key": self.api_key
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    self.base_url,
                    headers=headers,
                    params={"q": "test", "count": 1},
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
            logger.error(f"Bing health check failed: {e}")
            self._status = ProviderStatus.UNAVAILABLE
            self._last_check = datetime.utcnow()
            return False
