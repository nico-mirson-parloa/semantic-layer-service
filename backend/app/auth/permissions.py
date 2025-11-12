"""
Permission checking utilities for volume and metric access.
"""

from typing import List, Optional
import structlog

from .auth_models import User, Permission

logger = structlog.get_logger(__name__)


def check_volume_access(user: User, volume_path: str, action: str = "read") -> bool:
    """
    Check if user has access to a specific Unity Catalog volume path.
    
    Args:
        user: Authenticated user
        volume_path: Volume path (e.g., /Volumes/semantic_layer/metrics/production_models)
        action: Action type (read, write, admin)
        
    Returns:
        True if access is granted, False otherwise
    """
    try:
        # Admin users have access to everything
        if user.has_permission(Permission.VOLUME_ADMIN):
            logger.debug(f"Admin access granted for {user.email} to {volume_path}")
            return True
        
        # Check basic permissions
        if action == "read" and user.has_permission(Permission.VOLUME_READ):
            return _check_volume_read_access(user, volume_path)
        
        if action == "write" and user.has_permission(Permission.VOLUME_WRITE):
            return _check_volume_write_access(user, volume_path)
        
        logger.warning(f"Access denied for {user.email} to {volume_path} (action: {action})")
        return False
        
    except Exception as e:
        logger.error(f"Error checking volume access for {user.email}: {e}")
        return False


def _check_volume_read_access(user: User, volume_path: str) -> bool:
    """Check read access to volume path based on business rules."""
    
    # Parse volume path to extract category
    path_parts = volume_path.strip('/').split('/')
    if len(path_parts) < 4:
        return False
    
    category = path_parts[-1]  # e.g., production_models, staging_models
    
    # Business rules for read access
    read_rules = {
        "production_models": [Permission.METRIC_READ],
        "staging_models": [Permission.METRIC_READ, Permission.METRIC_CREATE],
        "templates": [Permission.METRIC_READ],
        "archives": [Permission.VOLUME_ADMIN]  # Only admins can read archives
    }
    
    required_permissions = read_rules.get(category, [Permission.VOLUME_READ])
    has_access = user.has_any_permission(required_permissions)
    
    logger.debug(f"Read access check for {user.email} to {category}: {has_access}")
    return has_access


def _check_volume_write_access(user: User, volume_path: str) -> bool:
    """Check write access to volume path based on business rules."""
    
    # Parse volume path to extract category
    path_parts = volume_path.strip('/').split('/')
    if len(path_parts) < 4:
        return False
    
    category = path_parts[-1]
    
    # Business rules for write access
    write_rules = {
        "production_models": [Permission.METRIC_APPROVE],  # Only approved users can write to production
        "staging_models": [Permission.METRIC_CREATE, Permission.METRIC_UPDATE],
        "templates": [Permission.VOLUME_ADMIN],  # Only admins can modify templates
        "archives": [Permission.VOLUME_ADMIN]   # Only admins can write to archives
    }
    
    required_permissions = write_rules.get(category, [Permission.VOLUME_WRITE])
    has_access = user.has_any_permission(required_permissions)
    
    logger.debug(f"Write access check for {user.email} to {category}: {has_access}")
    return has_access


def check_metric_access(user: User, metric_name: str, action: str = "read", 
                       access_level: str = "internal") -> bool:
    """
    Check if user has access to a specific metric based on governance metadata.
    
    Args:
        user: Authenticated user
        metric_name: Name of the metric
        action: Action type (read, create, update, delete, approve)
        access_level: Metric access level (public, internal, confidential, restricted)
        
    Returns:
        True if access is granted, False otherwise
    """
    try:
        # Admin users have access to everything
        if user.has_permission(Permission.SYSTEM_ADMIN):
            return True
        
        # Check action-specific permissions
        action_permissions = {
            "read": [Permission.METRIC_READ],
            "create": [Permission.METRIC_CREATE],
            "update": [Permission.METRIC_UPDATE],
            "delete": [Permission.METRIC_DELETE],
            "approve": [Permission.METRIC_APPROVE]
        }
        
        required_perms = action_permissions.get(action, [Permission.METRIC_READ])
        if not user.has_any_permission(required_perms):
            logger.warning(f"User {user.email} lacks permission for action {action} on {metric_name}")
            return False
        
        # Check access level restrictions
        return _check_access_level_permission(user, access_level)
        
    except Exception as e:
        logger.error(f"Error checking metric access for {user.email}: {e}")
        return False


def _check_access_level_permission(user: User, access_level: str) -> bool:
    """Check if user can access metrics at the specified access level."""
    
    # Define access level hierarchy and required roles/permissions
    access_rules = {
        "public": [],  # Anyone can access public metrics
        "internal": [Permission.METRIC_READ],  # Internal users
        "confidential": [Permission.METRIC_APPROVE],  # Senior analysts and above
        "restricted": [Permission.SYSTEM_ADMIN]  # Only system admins
    }
    
    required_permissions = access_rules.get(access_level, [Permission.METRIC_READ])
    
    if not required_permissions:  # Public access
        return True
    
    has_access = user.has_any_permission(required_permissions)
    logger.debug(f"Access level check for {user.email} to {access_level}: {has_access}")
    
    return has_access


def get_accessible_categories(user: User) -> List[str]:
    """
    Get list of volume categories the user can access.
    
    Args:
        user: Authenticated user
        
    Returns:
        List of accessible category names
    """
    categories = []
    
    # Check access to each category
    category_paths = [
        ("production_models", "/Volumes/semantic_layer/metrics/production_models"),
        ("staging_models", "/Volumes/semantic_layer/metrics/staging_models"),
        ("templates", "/Volumes/semantic_layer/metrics/templates"),
        ("archives", "/Volumes/semantic_layer/metrics/archives")
    ]
    
    for category_name, category_path in category_paths:
        if check_volume_access(user, category_path, "read"):
            categories.append(category_name)
    
    logger.debug(f"Accessible categories for {user.email}: {categories}")
    return categories


def filter_metrics_by_access(user: User, metrics: List[dict]) -> List[dict]:
    """
    Filter a list of metrics based on user access permissions.
    
    Args:
        user: Authenticated user
        metrics: List of metric dictionaries with governance metadata
        
    Returns:
        Filtered list of accessible metrics
    """
    accessible_metrics = []
    
    for metric in metrics:
        # Extract access level from governance metadata
        governance = metric.get("governance", {})
        access_level = governance.get("access_level", "internal")
        
        if check_metric_access(user, metric.get("name", ""), "read", access_level):
            accessible_metrics.append(metric)
    
    logger.debug(f"Filtered {len(accessible_metrics)} accessible metrics for {user.email}")
    return accessible_metrics


# Simple authentication dependency for FastAPI
def require_auth():
    """
    Placeholder authentication dependency.
    In production, this would validate JWT tokens and return authenticated user.
    """
    # For testing, return a mock user
    return {
        "user_id": "test_user",
        "email": "test@example.com",
        "roles": ["analyst"],
        "permissions": ["METRIC_READ", "METRIC_CREATE"]
    }