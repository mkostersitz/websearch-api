"""Search provider abstraction and implementation."""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel
from enum import Enum
import hashlib


class SearchResultType(str, Enum):
    """Type of search result."""
    WEB = "web"
    IMAGE = "image"
    VIDEO = "video"
    NEWS = "news"


class SearchResult(BaseModel):
    """Normalized search result model."""
    title: str
    url: str
    snippet: str
    result_type: SearchResultType = SearchResultType.WEB
    provider: str
    rank: int
    published_date: Optional[datetime] = None
    thumbnail_url: Optional[str] = None
    metadata: Dict[str, Any] = {}


class SearchResponse(BaseModel):
    """Search response model."""
    query: str
    query_hash: str
    results: List[SearchResult]
    total_results: int
    provider: str
    response_time_ms: float
    cached: bool = False
    timestamp: datetime = datetime.utcnow()


class ProviderStatus(str, Enum):
    """Provider health status."""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNAVAILABLE = "unavailable"


class SearchProvider(ABC):
    """Abstract base class for search providers."""
    
    def __init__(self, name: str):
        self.name = name
        self._status = ProviderStatus.HEALTHY
        self._last_check: Optional[datetime] = None
    
    @abstractmethod
    async def search(
        self,
        query: str,
        max_results: int = 10,
        safe_search: bool = True,
        **kwargs
    ) -> List[SearchResult]:
        """
        Perform a search query.
        
        Args:
            query: Search query string
            max_results: Maximum number of results to return
            safe_search: Enable safe search filtering
            **kwargs: Additional provider-specific parameters
            
        Returns:
            List of SearchResult objects
        """
        pass
    
    @abstractmethod
    async def health_check(self) -> bool:
        """
        Check if provider is healthy.
        
        Returns:
            True if healthy, False otherwise
        """
        pass
    
    @property
    def status(self) -> ProviderStatus:
        """Get current provider status."""
        return self._status
    
    @property
    def last_check(self) -> Optional[datetime]:
        """Get timestamp of last health check."""
        return self._last_check
    
    def _compute_query_hash(self, query: str) -> str:
        """Compute hash of query for caching and analytics."""
        return hashlib.sha256(query.encode()).hexdigest()[:16]
