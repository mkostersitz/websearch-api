"""Search API request and response models."""

from typing import List, Optional
from pydantic import BaseModel, Field, validator
from datetime import datetime

from src.models.search import SearchResult, SearchResultType


class SearchRequest(BaseModel):
    """Request model for search endpoint."""
    query: str = Field(..., min_length=1, max_length=500, description="Search query")
    max_results: int = Field(default=10, ge=1, le=100, description="Maximum results to return")
    safe_search: bool = Field(default=True, description="Enable safe search filtering")
    preferred_provider: Optional[str] = Field(None, description="Preferred search provider (google, bing)")
    
    @validator('query')
    def sanitize_query(cls, v):
        """Sanitize query string."""
        # Remove excessive whitespace
        v = ' '.join(v.split())
        # Basic sanitization (remove null bytes, control characters)
        v = ''.join(char for char in v if ord(char) >= 32 or char in '\n\r\t')
        return v


class SearchResultResponse(BaseModel):
    """Individual search result in response."""
    title: str
    url: str
    snippet: str
    result_type: SearchResultType
    provider: str
    rank: int
    published_date: Optional[datetime] = None
    thumbnail_url: Optional[str] = None


class SearchResponse(BaseModel):
    """Response model for search endpoint."""
    query: str
    results: List[SearchResultResponse]
    total_results: int
    filtered_results: int = Field(default=0, description="Number of results filtered by policies")
    provider: str
    response_time_ms: float
    cached: bool = False
    timestamp: datetime
    policies_applied: List[str] = Field(default_factory=list, description="IDs of applied policies")
    rate_limit_info: Optional[dict] = None
    quota_info: Optional[dict] = None


class SearchStatsResponse(BaseModel):
    """Search statistics response."""
    total_searches: int
    total_results_returned: int
    average_response_time_ms: float
    cache_hit_rate: float
    top_queries: List[dict]
    provider_distribution: dict
