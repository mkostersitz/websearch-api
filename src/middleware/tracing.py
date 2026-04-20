"""OpenTelemetry tracing middleware and utilities."""

import time
from typing import Callable, Optional
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from loguru import logger

try:
    from opentelemetry import trace
    from opentelemetry.trace import Status, StatusCode
    from src.core.telemetry import get_tracer
    OTEL_AVAILABLE = True
except:
    OTEL_AVAILABLE = False
    trace = None


class TracingMiddleware(BaseHTTPMiddleware):
    """Middleware to add custom tracing to requests."""
    
    def __init__(self, app):
        super().__init__(app)
        self.tracer = get_tracer() if OTEL_AVAILABLE else None
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request with tracing."""
        
        if not OTEL_AVAILABLE or not self.tracer:
            # Skip tracing if not available
            return await call_next(request)
        
        # Get current span (created by FastAPI instrumentor)
        current_span = trace.get_current_span()
        
        if current_span and current_span.is_recording():
            # Add custom attributes
            current_span.set_attribute("http.client_ip", request.client.host if request.client else "unknown")
            current_span.set_attribute("http.user_agent", request.headers.get("user-agent", ""))
            current_span.set_attribute("http.request_id", request.headers.get("X-Request-ID", ""))
            
            # Add API key presence (not the value)
            has_api_key = request.headers.get("X-API-Key") is not None
            current_span.set_attribute("auth.has_api_key", has_api_key)
            
            # Add OAuth token presence
            auth_header = request.headers.get("Authorization", "")
            has_bearer_token = auth_header.startswith("Bearer ")
            current_span.set_attribute("auth.has_bearer_token", has_bearer_token)
        
        start_time = time.time()
        
        try:
            response = await call_next(request)
            
            # Add response attributes to span
            if current_span and current_span.is_recording():
                current_span.set_attribute("http.response.status_code", response.status_code)
                current_span.set_attribute("http.response.duration_ms", (time.time() - start_time) * 1000)
                
                # Set span status based on HTTP status
                if response.status_code >= 500:
                    current_span.set_status(Status(StatusCode.ERROR, f"HTTP {response.status_code}"))
                elif response.status_code >= 400:
                    current_span.set_status(Status(StatusCode.ERROR, f"HTTP {response.status_code}"))
                else:
                    current_span.set_status(Status(StatusCode.OK))
            
            return response
            
        except Exception as e:
            # Record exception in span
            if current_span and current_span.is_recording():
                current_span.record_exception(e)
                current_span.set_status(Status(StatusCode.ERROR, str(e)))
            
            logger.error(f"Request failed: {e}")
            raise


def trace_function(name: str = None):
    """
    Decorator to trace a function with OpenTelemetry.
    
    Usage:
        @trace_function("my_function")
        async def my_function():
            ...
    """
    def decorator(func):
        if not OTEL_AVAILABLE:
            # Return function as-is if OTEL not available
            return func
        
        tracer = get_tracer()
        if not tracer:
            return func
        
        span_name = name or func.__name__
        
        from functools import wraps
        import asyncio
        
        if asyncio.iscoroutinefunction(func):
            @wraps(func)
            async def async_wrapper(*args, **kwargs):
                with tracer.start_as_current_span(span_name) as span:
                    try:
                        result = await func(*args, **kwargs)
                        span.set_status(Status(StatusCode.OK))
                        return result
                    except Exception as e:
                        span.record_exception(e)
                        span.set_status(Status(StatusCode.ERROR, str(e)))
                        raise
            return async_wrapper
        else:
            @wraps(func)
            def sync_wrapper(*args, **kwargs):
                with tracer.start_as_current_span(span_name) as span:
                    try:
                        result = func(*args, **kwargs)
                        span.set_status(Status(StatusCode.OK))
                        return result
                    except Exception as e:
                        span.record_exception(e)
                        span.set_status(Status(StatusCode.ERROR, str(e)))
                        raise
            return sync_wrapper
    
    return decorator
