"""
Databricks-integrated authentication and authorization.
"""

import jwt
from datetime import datetime, timedelta
from typing import Optional, List
from functools import wraps

import structlog
from fastapi import HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from databricks.sdk import WorkspaceClient
from databricks.sdk.service import iam

from .auth_models import User, UserRole, Permission, TokenData, ROLE_PERMISSIONS
from ..core.config import settings

logger = structlog.get_logger(__name__)

security = HTTPBearer()


class DatabricksAuth:
    """Databricks-integrated authentication service."""
    
    def __init__(self):
        self.client = WorkspaceClient()
        self.secret_key = settings.secret_key
        self.algorithm = "HS256"
        
    def verify_databricks_token(self, token: str) -> Optional[dict]:
        """Verify Databricks access token and get user info."""
        try:
            # Use token to create client and get current user
            temp_client = WorkspaceClient(token=token)
            current_user = temp_client.current_user.me()
            
            return {
                "id": str(current_user.id),
                "email": current_user.emails[0].value if current_user.emails else current_user.user_name,
                "display_name": current_user.display_name,
                "groups": [group.display for group in current_user.groups] if current_user.groups else [],
                "is_active": current_user.active
            }
        except Exception as e:
            logger.error(f"Failed to verify Databricks token: {e}")
            return None
    
    def get_user_roles(self, user_groups: List[str]) -> List[UserRole]:
        """Map Databricks groups to semantic layer roles."""
        roles = []
        
        # Map groups to roles (customize based on your group naming)
        group_role_mapping = {
            "admins": UserRole.ADMIN,
            "data-engineers": UserRole.DATA_ENGINEER,
            "data-analysts": UserRole.DATA_ANALYST,
            "data-scientists": UserRole.DATA_SCIENTIST,
            "business-users": UserRole.BUSINESS_USER,
        }
        
        for group in user_groups:
            if group.lower() in group_role_mapping:
                roles.append(group_role_mapping[group.lower()])
        
        # Default role if no specific groups found
        if not roles:
            roles.append(UserRole.VIEWER)
            
        return roles
    
    def get_permissions_for_roles(self, roles: List[UserRole]) -> List[Permission]:
        """Get all permissions for a list of roles."""
        permissions = set()
        for role in roles:
            if role in ROLE_PERMISSIONS:
                permissions.update(ROLE_PERMISSIONS[role])
        return list(permissions)
    
    def create_access_token(self, user: User) -> str:
        """Create JWT access token for user."""
        expire = datetime.utcnow() + timedelta(minutes=30)
        
        to_encode = {
            "user_id": user.id,
            "email": user.email,
            "roles": [role.value for role in user.roles],
            "exp": expire
        }
        
        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        return encoded_jwt
    
    def verify_token(self, token: str) -> Optional[TokenData]:
        """Verify JWT token and return token data."""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            user_id: str = payload.get("user_id")
            email: str = payload.get("email")
            roles: List[str] = payload.get("roles", [])
            
            if user_id is None or email is None:
                return None
                
            return TokenData(user_id=user_id, email=email, roles=roles)
        except jwt.PyJWTError:
            return None
    
    def authenticate_user(self, databricks_token: str) -> Optional[User]:
        """Authenticate user with Databricks token."""
        user_info = self.verify_databricks_token(databricks_token)
        if not user_info:
            return None
        
        # Map to User model
        roles = self.get_user_roles(user_info.get("groups", []))
        permissions = self.get_permissions_for_roles(roles)
        
        user = User(
            id=user_info["id"],
            email=user_info["email"],
            display_name=user_info.get("display_name"),
            roles=roles,
            permissions=permissions,
            groups=user_info.get("groups", []),
            is_active=user_info.get("is_active", True),
            created_at=datetime.now()
        )
        
        logger.info(f"Authenticated user {user.email} with roles {[r.value for r in user.roles]}")
        return user
    
    def check_volume_access(self, user: User, volume_path: str, action: str = "read") -> bool:
        """Check if user has access to a specific volume path."""
        try:
            # Use Unity Catalog to check permissions
            # This is a simplified check - in practice, you'd use UC permissions API
            
            if user.has_permission(Permission.VOLUME_ADMIN):
                return True
                
            if action == "read" and user.has_permission(Permission.VOLUME_READ):
                return True
                
            if action == "write" and user.has_permission(Permission.VOLUME_WRITE):
                return True
                
            # Additional volume-specific logic can be added here
            return False
            
        except Exception as e:
            logger.error(f"Failed to check volume access for user {user.email}: {e}")
            return False


# Global auth instance
auth_service = DatabricksAuth()


async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> User:
    """FastAPI dependency to get current authenticated user."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        # Try JWT token first
        token_data = auth_service.verify_token(credentials.credentials)
        if token_data:
            # Reconstruct user from token (in production, you might want to cache/store this)
            roles = [UserRole(role) for role in token_data.roles]
            permissions = auth_service.get_permissions_for_roles(roles)
            
            return User(
                id=token_data.user_id,
                email=token_data.email,
                roles=roles,
                permissions=permissions,
                is_active=True,
                created_at=datetime.now()
            )
        
        # Try Databricks token
        user = auth_service.authenticate_user(credentials.credentials)
        if user:
            return user
            
    except Exception as e:
        logger.error(f"Authentication failed: {e}")
        
    raise credentials_exception


def require_role(*required_roles: UserRole):
    """Decorator to require specific roles."""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Extract user from kwargs (assumes get_current_user dependency)
            user = kwargs.get('user') or kwargs.get('current_user')
            if not user or not isinstance(user, User):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authentication required"
                )
            
            if not user.has_any_role(list(required_roles)):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Requires one of roles: {[r.value for r in required_roles]}"
                )
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator


def require_permission(*required_permissions: Permission):
    """Decorator to require specific permissions."""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Extract user from kwargs
            user = kwargs.get('user') or kwargs.get('current_user')
            if not user or not isinstance(user, User):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authentication required"
                )
            
            if not user.has_any_permission(list(required_permissions)):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Requires one of permissions: {[p.value for p in required_permissions]}"
                )
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator