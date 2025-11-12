"""
Authentication and authorization module for Databricks-integrated semantic layer.
"""

from .auth_models import User, UserRole, Permission
from .databricks_auth import DatabricksAuth, get_current_user, require_role, require_permission
from .permissions import check_volume_access, check_metric_access

__all__ = [
    "User",
    "UserRole", 
    "Permission",
    "DatabricksAuth",
    "get_current_user",
    "require_role",
    "require_permission",
    "check_volume_access",
    "check_metric_access"
]