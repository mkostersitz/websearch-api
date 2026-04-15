"""Main FastAPI application."""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from loguru import logger

from src.core.config import settings
from src.core.logging import configure_logging
from src.core.database import Database
from src.middleware.logging import LoggingMiddleware
from src.api.routes import health


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    # Startup
    configure_logging()
    logger.info(f"Starting {settings.app_name} v{settings.app_version}")
    logger.info(f"Environment: {settings.environment}")
    
    # Connect to databases
    await Database.connect()
    
    logger.info(f"Application started successfully on {settings.host}:{settings.port}")
    
    yield
    
    # Shutdown
    logger.info("Shutting down application")
    await Database.disconnect()
    logger.info("Application shutdown complete")


def create_application() -> FastAPI:
    """Create and configure FastAPI application."""
    
    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description="Enterprise-grade Web Search API for AI Agents with OTEL, OAuth, and advanced guardrails",
        docs_url="/docs" if settings.debug else None,
        redoc_url="/redoc" if settings.debug else None,
        lifespan=lifespan,
    )
    
    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Custom middleware
    app.add_middleware(LoggingMiddleware)
    
    # Include routers
    app.include_router(health.router, prefix="/api/v1", tags=["health"])
    
    # Import clients router lazily to avoid circular imports
    from src.api.routes import clients
    app.include_router(clients.router, prefix="/api/v1", tags=["clients"])
    
    # Exception handlers
    @app.exception_handler(Exception)
    async def global_exception_handler(request, exc):
        logger.error(f"Unhandled exception: {exc}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={
                "error": "Internal Server Error",
                "detail": str(exc) if settings.debug else "An unexpected error occurred"
            }
        )
    
    return app


app = create_application()


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "src.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_level=settings.log_level.lower(),
    )
