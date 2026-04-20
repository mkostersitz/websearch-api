"""Middleware for collecting Prometheus metrics."""

import time
from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from loguru import logger

from src.api.routes.metrics import (
    http_requests_total,
    http_request_duration,
    active_requests
)


class MetricsMiddleware(BaseHTTPMiddleware):
    """Middleware to collect Prometheus metrics for HTTP requests."""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request and collect metrics."""
        
        # Increment active requests
        active_requests.inc()
        
        # Start timer
        start_time = time.time()
        
        try:
            # Process request
            response = await call_next(request)
            
            # Calculate duration
            duration = (time.time() - start_time) * 1000  # Convert to milliseconds
            
            # Extract endpoint path (without query params)
            endpoint = request.url.path
            method = request.method
            status_code = str(response.status_code)
            
            # Increment request counter
            http_requests_total.labels(
                method=method,
                endpoint=endpoint,
                status_code=status_code
            ).inc()
            
            # Record duration
            http_request_duration.labels(
                method=method,
                endpoint=endpoint
            ).observe(duration)
            
            return response
            
        except Exception as e:
            # Record error
            http_requests_total.labels(
                method=request.method,
                endpoint=request.url.path,
                status_code="500"
            ).inc()
            raise
            
        finally:
            # Decrement active requests
            active_requests.dec()
