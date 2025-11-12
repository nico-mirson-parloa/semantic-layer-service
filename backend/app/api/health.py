"""
Health check endpoints
"""
from fastapi import APIRouter, HTTPException
from typing import Dict, Any
import structlog
import asyncio
import httpx

from app.integrations.databricks import get_databricks_connector
from app.core.config import settings

router = APIRouter()
logger = structlog.get_logger()


@router.get("/")
async def health_check() -> Dict[str, Any]:
    """Basic health check"""
    return {
        "status": "healthy",
        "service": "semantic-layer-service",
        "version": "0.1.0"
    }


@router.get("/databricks")
async def databricks_health() -> Dict[str, Any]:
    """Check Databricks connectivity"""
    if not all([settings.databricks_host, settings.databricks_token, settings.databricks_http_path]):
        return {
            "status": "not_configured",
            "message": "Databricks credentials not configured",
            "configured": False
        }
    
    try:
        # First, do a quick HTTP connectivity check (faster than SQL connection)
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(
                    f"https://{settings.databricks_host}/api/2.0/clusters/list",
                    headers={"Authorization": f"Bearer {settings.databricks_token}"}
                )
                
                # Check for invalid token (403)
                if response.status_code == 403:
                    logger.error("Databricks token is invalid or expired")
                    return {
                        "status": "unhealthy",
                        "message": "Databricks token is invalid or expired. Please update DATABRICKS_TOKEN in .env",
                        "configured": True,
                        "connected": False,
                        "error": "Invalid access token"
                    }
                
                # 200 or 401 mean host is reachable
                if response.status_code not in [200, 401]:
                    logger.warning(f"Unexpected status code from Databricks: {response.status_code}")
                    return {
                        "status": "unhealthy",
                        "message": f"Unexpected response from Databricks: {response.status_code}",
                        "configured": True,
                        "connected": False
                    }
                    
        except httpx.TimeoutException:
            logger.error("Databricks HTTP connectivity check timed out")
            return {
                "status": "unhealthy",
                "message": "Cannot reach Databricks host (timeout after 5 seconds)",
                "configured": True,
                "connected": False
            }
        except Exception as e:
            logger.error("Databricks HTTP connectivity check failed", error=str(e))
            return {
                "status": "unhealthy",
                "message": f"Cannot reach Databricks host: {str(e)}",
                "configured": True,
                "connected": False
            }
        
        # If HTTP check passes, try SQL connection with shorter timeout
        connector = get_databricks_connector()
        try:
            is_connected = await asyncio.wait_for(
                asyncio.to_thread(connector.test_connection),
                timeout=5.0
            )
        except asyncio.TimeoutError:
            logger.error("Databricks SQL connection test timed out")
            return {
                "status": "unhealthy",
                "message": "Databricks SQL Warehouse connection timed out. The warehouse may be stopped or unavailable.",
                "configured": True,
                "connected": False,
                "suggestion": "Check if the SQL Warehouse is running in your Databricks workspace"
            }
        
        if is_connected:
            return {
                "status": "healthy",
                "message": "Successfully connected to Databricks SQL Warehouse",
                "host": settings.databricks_host,
                "configured": True,
                "connected": True
            }
        else:
            raise Exception("Connection test returned False")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Databricks health check failed", error=str(e))
        return {
            "status": "unhealthy",
            "message": f"Failed to connect to Databricks: {str(e)}",
            "configured": True,
            "connected": False
        }


@router.get("/ready")
async def readiness_check() -> Dict[str, Any]:
    """Readiness check for all dependencies"""
    checks = {
        "api": True,
        "databricks": False
    }
    
    # Check Databricks if configured
    if all([settings.databricks_host, settings.databricks_token, settings.databricks_http_path]):
        try:
            connector = get_databricks_connector()
            # Run blocking connection test in thread pool with timeout
            try:
                checks["databricks"] = await asyncio.wait_for(
                    asyncio.to_thread(connector.test_connection),
                    timeout=10.0
                )
            except (asyncio.TimeoutError, Exception):
                checks["databricks"] = False
        except Exception:
            checks["databricks"] = False
    
    all_ready = all(checks.values())
    
    return {
        "ready": all_ready,
        "checks": checks
    }
