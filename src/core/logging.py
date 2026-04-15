"""Logging configuration using loguru."""

import sys
from loguru import logger
from src.core.config import settings


def configure_logging() -> None:
    """Configure application logging with loguru."""
    
    # Remove default handler
    logger.remove()
    
    # Add console handler with formatting
    logger.add(
        sys.stdout,
        format="<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | <level>{message}</level>",
        level=settings.log_level,
        colorize=True,
        backtrace=True,
        diagnose=True,
    )
    
    # Add file handler for errors
    logger.add(
        "logs/errors.log",
        format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {name}:{function}:{line} | {message}",
        level="ERROR",
        rotation="100 MB",
        retention="30 days",
        compression="zip",
    )
    
    # Add file handler for all logs in production
    if settings.environment == "production":
        logger.add(
            "logs/app.log",
            format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {name}:{function}:{line} | {message}",
            level="INFO",
            rotation="500 MB",
            retention="7 days",
            compression="zip",
        )
    
    logger.info(f"Logging configured - Level: {settings.log_level}, Environment: {settings.environment}")


def get_logger(name: str):
    """Get a logger instance for a module."""
    return logger.bind(module=name)
