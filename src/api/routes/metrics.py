"""Prometheus metrics endpoint."""

from fastapi import APIRouter, Response
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest, CollectorRegistry
from prometheus_client import Counter, Histogram, Gauge
import time

router = APIRouter()

# Create a custom registry
REGISTRY = CollectorRegistry()

# Define some basic metrics
http_requests_total = Counter(
    'http_server_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status_code'],
    registry=REGISTRY
)

http_request_duration = Histogram(
    'http_server_duration_milliseconds',
    'HTTP request duration in milliseconds',
    ['method', 'endpoint'],
    registry=REGISTRY
)

active_requests = Gauge(
    'http_server_active_requests',
    'Number of active HTTP requests',
    registry=REGISTRY
)


@router.get("/metrics")
async def metrics():
    """
    Expose Prometheus metrics.
    
    This endpoint returns metrics in Prometheus text format.
    """
    return Response(
        content=generate_latest(REGISTRY),
        media_type=CONTENT_TYPE_LATEST
    )
