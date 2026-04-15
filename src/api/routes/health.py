"""Health check endpoints."""

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from datetime import datetime
from typing import Dict, Any
from motor.motor_asyncio import AsyncIOMotorDatabase

from src.core.config import settings
from src.core.database import get_database


router = APIRouter()


class HealthResponse(BaseModel):
    """Health check response model."""
    status: str
    version: str
    timestamp: datetime
    environment: str


class ReadinessResponse(BaseModel):
    """Readiness check response model."""
    status: str
    version: str
    timestamp: datetime
    checks: Dict[str, Any]


@router.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """
    Basic health check endpoint.
    
    Returns service status without checking dependencies.
    Used for liveness probes in Kubernetes.
    """
    return HealthResponse(
        status="healthy",
        version=settings.app_version,
        timestamp=datetime.utcnow(),
        environment=settings.environment,
    )


@router.get("/ready", response_model=ReadinessResponse)
async def readiness_check(db: AsyncIOMotorDatabase = Depends(get_database)) -> ReadinessResponse:
    """
    Readiness check endpoint.
    
    Checks all dependencies (database, cache, etc.) are available.
    Used for readiness probes in Kubernetes.
    """
    checks = {}
    overall_status = "ready"
    
    # Check MongoDB
    try:
        await db.command('ping')
        checks["mongodb"] = {"status": "healthy", "message": "Connected"}
    except Exception as e:
        checks["mongodb"] = {"status": "unhealthy", "message": str(e)}
        overall_status = "not_ready"
    
    # TODO: Add Redis check when implemented
    # TODO: Add search provider checks when implemented
    
    return ReadinessResponse(
        status=overall_status,
        version=settings.app_version,
        timestamp=datetime.utcnow(),
        checks=checks,
    )
