"""
Health check routes for CVS Pharmacy Knowledge Assist
Monitors database connectivity and application health
"""

from fastapi import APIRouter
from fastapi.responses import JSONResponse
from ...database.connection import health_check, get_database_info
from ...services.cache_manager import get_cache_stats, get_cache
from ...config import config
import logging
import time
from typing import Dict, Any

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/health")
async def application_health():
    """
    Overall application health check
    Returns basic application status and uptime
    """
    try:
        return {
            "status": "healthy",
            "timestamp": time.time(),
            "application": "CVS Pharmacy Knowledge Assist",
            "version": "1.0.0",
            "environment": config.APP_ENVIRONMENT,
            "database_enabled": True  # Since we have database integration
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "timestamp": time.time(),
                "error": str(e)
            }
        )


@router.get("/health/database")
async def database_health():
    """
    Database-specific health check
    Tests database connectivity and returns detailed connection info
    """
    try:
        # Perform comprehensive database health check
        health_status = await health_check()
        
        # Get additional database information
        db_info = await get_database_info()
        
        # Combine health and info data
        response_data = {
            "timestamp": time.time(),
            "healthy": health_status.get("healthy", False),
            "response_time_ms": health_status.get("response_time_ms"),
            "database_config": {
                "environment": config.APP_ENVIRONMENT,
                "pool_size": config.DB_POOL_SIZE,
                "max_overflow": config.DB_MAX_OVERFLOW,
                "pool_timeout": config.DB_POOL_TIMEOUT,
                "pool_recycle": config.DB_POOL_RECYCLE,
                "pool_pre_ping": config.DB_POOL_PRE_PING,
                "host": config.DB_HOST,
                "port": config.DB_PORT,
                "database": config.database_name,
            },
            "database_info": db_info
        }
        
        # Add error information if unhealthy
        if not health_status.get("healthy", False):
            response_data["error"] = health_status.get("error", "Unknown database error")
        
        # Return appropriate HTTP status code
        status_code = 200 if health_status.get("healthy", False) else 503
        
        return JSONResponse(
            status_code=status_code,
            content=response_data
        )
        
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return JSONResponse(
            status_code=503,
            content={
                "timestamp": time.time(),
                "healthy": False,
                "error": f"Database health check failed: {str(e)}",
                "database_config": {
                    "environment": config.APP_ENVIRONMENT,
                    "host": config.DB_HOST,
                    "port": config.DB_PORT,
                    "database": config.database_name,
                }
            }
        )


@router.get("/health/cache")
async def cache_health():
    """
    Cache-specific health check
    Tests cache functionality and returns detailed cache info
    """
    try:
        # Get cache statistics and configuration
        cache_stats = get_cache_stats()
        
        # Determine cache health
        cache_healthy = cache_stats.get("enabled", False)
        
        response_data = {
            "timestamp": time.time(),
            "healthy": cache_healthy,
            "cache_config": {
                "enabled": cache_stats.get("config", {}).get("enabled", False),
                "ttl_seconds": cache_stats.get("config", {}).get("ttl_seconds", 0),
                "max_size_mb": cache_stats.get("config", {}).get("max_size_mb", 0),
                "cleanup_interval": cache_stats.get("config", {}).get("cleanup_interval", 0)
            },
            "cache_stats": {
                "total_entries": cache_stats.get("total_entries", 0),
                "active_entries": cache_stats.get("active_entries", 0),
                "expired_entries": cache_stats.get("expired_entries", 0),
                "cache_size_mb": cache_stats.get("cache_size_mb", 0.0)
            }
        }
        
        # Add error information if cache is disabled
        if not cache_healthy:
            response_data["error"] = "Cache is disabled in configuration"
        
        # Return appropriate HTTP status code
        status_code = 200 if cache_healthy else 503
        
        return JSONResponse(
            status_code=status_code,
            content=response_data
        )
        
    except Exception as e:
        logger.error(f"Cache health check failed: {e}")
        return JSONResponse(
            status_code=503,
            content={
                "timestamp": time.time(),
                "healthy": False,
                "error": f"Cache health check failed: {str(e)}"
            }
        )


@router.get("/health/detailed")
async def detailed_health():
    """
    Comprehensive health check combining all system components
    """
    try:
        # Application health
        app_start_time = time.time()
        app_healthy = True
        app_error = None
        
        # Database health
        db_health = await health_check()
        db_healthy = db_health.get("healthy", False)
        
        # Overall system health
        overall_healthy = app_healthy and db_healthy
        
        response_data = {
            "timestamp": time.time(),
            "overall_healthy": overall_healthy,
            "components": {
                "application": {
                    "healthy": app_healthy,
                    "version": "1.0.0",
                    "environment": config.APP_ENVIRONMENT,
                    "error": app_error
                },
                "database": {
                    "healthy": db_healthy,
                    "response_time_ms": db_health.get("response_time_ms"),
                    "environment": config.APP_ENVIRONMENT,
                    "connection_info": db_health.get("database_info", {}),
                    "error": db_health.get("error")
                }
            },
            "configuration": {
                "database_enabled": True,
                "environment": config.APP_ENVIRONMENT,
                "log_level": config.LOG_LEVEL
            }
        }
        
        # Return appropriate status code
        status_code = 200 if overall_healthy else 503
        
        return JSONResponse(
            status_code=status_code,
            content=response_data
        )
        
    except Exception as e:
        logger.error(f"Detailed health check failed: {e}")
        return JSONResponse(
            status_code=503,
            content={
                "timestamp": time.time(),
                "overall_healthy": False,
                "error": f"Health check system failure: {str(e)}"
            }
        )
