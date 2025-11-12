"""
Authentication API endpoints for user login and token management.
"""

from fastapi import APIRouter, HTTPException, Depends, status
from typing import Dict, Any
import structlog

from ..auth import get_current_user, User
from ..auth.databricks_auth import DatabricksAuth, auth_service
from ..auth.auth_models import LoginRequest
from ..auth.permissions import get_accessible_categories

router = APIRouter()
logger = structlog.get_logger()


@router.post("/login")
async def login(login_request: LoginRequest) -> Dict[str, Any]:
    """
    Authenticate user with Databricks token and return JWT access token.
    
    Args:
        login_request: Contains Databricks access token
        
    Returns:
        JWT access token and user information
    """
    try:
        # Authenticate user with Databricks token
        user = auth_service.authenticate_user(login_request.token)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid Databricks token or authentication failed"
            )
        
        # Generate JWT access token
        access_token = auth_service.create_access_token(user)
        
        logger.info(f"User {user.email} logged in successfully")
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user": {
                "id": user.id,
                "email": user.email,
                "display_name": user.display_name,
                "roles": [role.value for role in user.roles],
                "groups": user.groups
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Authentication service error"
        )


@router.get("/me")
async def get_current_user_info(current_user: User = Depends(get_current_user)) -> Dict[str, Any]:
    """
    Get current authenticated user information.
    
    Returns:
        Current user details and permissions
    """
    try:
        # Get accessible volume categories for user
        accessible_categories = get_accessible_categories(current_user)
        
        return {
            "user": {
                "id": current_user.id,
                "email": current_user.email,
                "display_name": current_user.display_name,
                "roles": [role.value for role in current_user.roles],
                "permissions": [perm.value for perm in current_user.permissions],
                "groups": current_user.groups,
                "is_active": current_user.is_active,
                "last_login": current_user.last_login
            },
            "access": {
                "accessible_categories": accessible_categories,
                "can_create_metrics": any(perm.value == "metric:create" for perm in current_user.permissions),
                "can_approve_metrics": any(perm.value == "metric:approve" for perm in current_user.permissions),
                "is_admin": any(perm.value == "system:admin" for perm in current_user.permissions)
            }
        }
        
    except Exception as e:
        logger.error(f"Failed to get user info: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve user information"
        )


@router.post("/refresh")
async def refresh_token(current_user: User = Depends(get_current_user)) -> Dict[str, Any]:
    """
    Refresh JWT access token for authenticated user.
    
    Returns:
        New JWT access token
    """
    try:
        # Generate new access token
        access_token = auth_service.create_access_token(current_user)
        
        logger.info(f"Token refreshed for user {current_user.email}")
        
        return {
            "access_token": access_token,
            "token_type": "bearer"
        }
        
    except Exception as e:
        logger.error(f"Token refresh failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Token refresh failed"
        )


@router.get("/permissions")
async def get_user_permissions(current_user: User = Depends(get_current_user)) -> Dict[str, Any]:
    """
    Get detailed permission information for the current user.
    
    Returns:
        Detailed permissions and access controls
    """
    try:
        accessible_categories = get_accessible_categories(current_user)
        
        # Group permissions by category
        permissions_by_category = {
            "metrics": [perm.value for perm in current_user.permissions if perm.value.startswith("metric:")],
            "volumes": [perm.value for perm in current_user.permissions if perm.value.startswith("volume:")],
            "queries": [perm.value for perm in current_user.permissions if perm.value.startswith("query:")],
            "system": [perm.value for perm in current_user.permissions if perm.value.startswith("system:")]
        }
        
        return {
            "user_id": current_user.id,
            "email": current_user.email,
            "roles": [role.value for role in current_user.roles],
            "permissions": {
                "all": [perm.value for perm in current_user.permissions],
                "by_category": permissions_by_category
            },
            "access": {
                "accessible_volume_categories": accessible_categories,
                "volume_access": {
                    "production_models": {
                        "read": "volume:read" in [p.value for p in current_user.permissions],
                        "write": "metric:approve" in [p.value for p in current_user.permissions]
                    },
                    "staging_models": {
                        "read": "volume:read" in [p.value for p in current_user.permissions],
                        "write": "volume:write" in [p.value for p in current_user.permissions]
                    }
                }
            }
        }
        
    except Exception as e:
        logger.error(f"Failed to get user permissions: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve user permissions"
        )