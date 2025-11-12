"""
Authentication models for role-based access control.
"""

from enum import Enum
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from datetime import datetime


class UserRole(str, Enum):
    """Predefined user roles aligned with Databricks workspace roles."""
    ADMIN = "admin"
    DATA_ENGINEER = "data_engineer"
    DATA_ANALYST = "data_analyst"
    DATA_SCIENTIST = "data_scientist"
    BUSINESS_USER = "business_user"
    VIEWER = "viewer"


class Permission(str, Enum):
    """Granular permissions for semantic layer operations."""
    # Metric permissions
    METRIC_READ = "metric:read"
    METRIC_CREATE = "metric:create"
    METRIC_UPDATE = "metric:update"
    METRIC_DELETE = "metric:delete"
    METRIC_APPROVE = "metric:approve"
    
    # Volume permissions
    VOLUME_READ = "volume:read"
    VOLUME_WRITE = "volume:write"
    VOLUME_ADMIN = "volume:admin"
    
    # System permissions
    SYSTEM_ADMIN = "system:admin"
    USER_MANAGEMENT = "user:management"
    
    # Query permissions
    QUERY_EXECUTE = "query:execute"
    QUERY_VALIDATE = "query:validate"


class User(BaseModel):
    """User model with Databricks integration."""
    id: str  # Databricks user ID
    email: str
    display_name: Optional[str] = None
    roles: List[UserRole] = []
    permissions: List[Permission] = []
    groups: List[str] = []  # Databricks workspace groups
    is_active: bool = True
    created_at: datetime
    last_login: Optional[datetime] = None
    
    # Additional attributes for ABAC
    attributes: Dict[str, Any] = {}
    
    def has_role(self, role: UserRole) -> bool:
        """Check if user has a specific role."""
        return role in self.roles
    
    def has_permission(self, permission: Permission) -> bool:
        """Check if user has a specific permission."""
        return permission in self.permissions
    
    def has_any_role(self, roles: List[UserRole]) -> bool:
        """Check if user has any of the specified roles."""
        return any(role in self.roles for role in roles)
    
    def has_any_permission(self, permissions: List[Permission]) -> bool:
        """Check if user has any of the specified permissions."""
        return any(perm in self.permissions for perm in permissions)


class TokenData(BaseModel):
    """JWT token data."""
    user_id: str
    email: str
    roles: List[str] = []
    exp: Optional[int] = None


class LoginRequest(BaseModel):
    """Login request model."""
    token: str  # Databricks access token or OAuth token


class AuthConfig(BaseModel):
    """Authentication configuration."""
    secret_key: str
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    databricks_host: str
    
    
# Role-permission mapping
ROLE_PERMISSIONS: Dict[UserRole, List[Permission]] = {
    UserRole.ADMIN: [
        Permission.METRIC_READ, Permission.METRIC_CREATE, Permission.METRIC_UPDATE, 
        Permission.METRIC_DELETE, Permission.METRIC_APPROVE,
        Permission.VOLUME_READ, Permission.VOLUME_WRITE, Permission.VOLUME_ADMIN,
        Permission.SYSTEM_ADMIN, Permission.USER_MANAGEMENT,
        Permission.QUERY_EXECUTE, Permission.QUERY_VALIDATE
    ],
    UserRole.DATA_ENGINEER: [
        Permission.METRIC_READ, Permission.METRIC_CREATE, Permission.METRIC_UPDATE,
        Permission.VOLUME_READ, Permission.VOLUME_WRITE,
        Permission.QUERY_EXECUTE, Permission.QUERY_VALIDATE
    ],
    UserRole.DATA_ANALYST: [
        Permission.METRIC_READ, Permission.METRIC_CREATE, Permission.METRIC_UPDATE,
        Permission.VOLUME_READ, Permission.VOLUME_WRITE,
        Permission.QUERY_EXECUTE, Permission.QUERY_VALIDATE
    ],
    UserRole.DATA_SCIENTIST: [
        Permission.METRIC_READ, Permission.METRIC_CREATE, Permission.METRIC_UPDATE,
        Permission.VOLUME_READ, Permission.VOLUME_WRITE,
        Permission.QUERY_EXECUTE, Permission.QUERY_VALIDATE
    ],
    UserRole.BUSINESS_USER: [
        Permission.METRIC_READ, Permission.VOLUME_READ,
        Permission.QUERY_EXECUTE, Permission.QUERY_VALIDATE
    ],
    UserRole.VIEWER: [
        Permission.METRIC_READ, Permission.VOLUME_READ
    ]
}