"""Role-based access control (RBAC) implementation."""

from enum import Enum
from typing import List, Optional
from functools import wraps
from fastapi import HTTPException, status
from loguru import logger

from src.models.database import UserRole


class Permission(str, Enum):
    """System permissions."""
    # Search permissions
    SEARCH_QUERY = "search:query"
    SEARCH_VIEW_LOGS = "search:view_logs"
    
    # Client management permissions
    CLIENT_CREATE = "client:create"
    CLIENT_VIEW = "client:view"
    CLIENT_UPDATE = "client:update"
    CLIENT_DELETE = "client:delete"
    
    # Policy permissions
    POLICY_CREATE = "policy:create"
    POLICY_VIEW = "policy:view"
    POLICY_UPDATE = "policy:update"
    POLICY_DELETE = "policy:delete"
    
    # Admin permissions
    ADMIN_USERS = "admin:users"
    ADMIN_CONFIG = "admin:config"
    ADMIN_AUDIT = "admin:audit"
    ADMIN_ANALYTICS = "admin:analytics"


# Role to permissions mapping
ROLE_PERMISSIONS = {
    UserRole.ADMIN: [
        # Admins have all permissions
        Permission.SEARCH_QUERY,
        Permission.SEARCH_VIEW_LOGS,
        Permission.CLIENT_CREATE,
        Permission.CLIENT_VIEW,
        Permission.CLIENT_UPDATE,
        Permission.CLIENT_DELETE,
        Permission.POLICY_CREATE,
        Permission.POLICY_VIEW,
        Permission.POLICY_UPDATE,
        Permission.POLICY_DELETE,
        Permission.ADMIN_USERS,
        Permission.ADMIN_CONFIG,
        Permission.ADMIN_AUDIT,
        Permission.ADMIN_ANALYTICS,
    ],
    UserRole.USER: [
        # Regular users can search and manage their own clients
        Permission.SEARCH_QUERY,
        Permission.CLIENT_CREATE,
        Permission.CLIENT_VIEW,
        Permission.CLIENT_UPDATE,
        Permission.CLIENT_DELETE,
        Permission.POLICY_VIEW,
    ],
    UserRole.AGENT: [
        # AI agents can only search
        Permission.SEARCH_QUERY,
    ],
}


def has_permission(role: UserRole, permission: Permission) -> bool:
    """
    Check if a role has a specific permission.
    
    Args:
        role: User role
        permission: Required permission
        
    Returns:
        True if role has permission, False otherwise
    """
    role_perms = ROLE_PERMISSIONS.get(role, [])
    return permission in role_perms


def has_any_permission(role: UserRole, permissions: List[Permission]) -> bool:
    """
    Check if a role has any of the specified permissions.
    
    Args:
        role: User role
        permissions: List of permissions
        
    Returns:
        True if role has at least one permission, False otherwise
    """
    return any(has_permission(role, perm) for perm in permissions)


def has_all_permissions(role: UserRole, permissions: List[Permission]) -> bool:
    """
    Check if a role has all of the specified permissions.
    
    Args:
        role: User role
        permissions: List of permissions
        
    Returns:
        True if role has all permissions, False otherwise
    """
    return all(has_permission(role, perm) for perm in permissions)


def require_permission(permission: Permission):
    """
    Decorator to require a specific permission for an endpoint.
    
    Usage:
        @router.get("/admin/config")
        @require_permission(Permission.ADMIN_CONFIG)
        async def get_config(client: dict = Depends(get_api_key_client)):
            ...
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Extract client from kwargs (injected by FastAPI dependency)
            client = kwargs.get('current_client') or kwargs.get('client')
            
            if not client:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authentication required"
                )
            
            # Get user role from client metadata or default to AGENT
            role_str = client.get('role', 'agent')
            try:
                role = UserRole(role_str)
            except ValueError:
                role = UserRole.AGENT
            
            # Check permission
            if not has_permission(role, permission):
                logger.warning(
                    f"Permission denied: {client.get('client_id')} "
                    f"(role: {role}) lacks {permission}"
                )
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Permission denied: {permission} required"
                )
            
            return await func(*args, **kwargs)
        
        return wrapper
    
    return decorator


def require_any_permission(permissions: List[Permission]):
    """
    Decorator to require any of the specified permissions.
    
    Usage:
        @router.get("/data")
        @require_any_permission([Permission.CLIENT_VIEW, Permission.ADMIN_USERS])
        async def get_data(client: dict = Depends(get_api_key_client)):
            ...
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            client = kwargs.get('current_client') or kwargs.get('client')
            
            if not client:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authentication required"
                )
            
            role_str = client.get('role', 'agent')
            try:
                role = UserRole(role_str)
            except ValueError:
                role = UserRole.AGENT
            
            if not has_any_permission(role, permissions):
                logger.warning(
                    f"Permission denied: {client.get('client_id')} "
                    f"(role: {role}) lacks any of {permissions}"
                )
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Permission denied: one of {permissions} required"
                )
            
            return await func(*args, **kwargs)
        
        return wrapper
    
    return decorator


def require_role(required_role: UserRole):
    """
    Decorator to require a specific role.
    
    Usage:
        @router.get("/admin")
        @require_role(UserRole.ADMIN)
        async def admin_endpoint(client: dict = Depends(get_api_key_client)):
            ...
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            client = kwargs.get('current_client') or kwargs.get('client')
            
            if not client:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authentication required"
                )
            
            role_str = client.get('role', 'agent')
            try:
                role = UserRole(role_str)
            except ValueError:
                role = UserRole.AGENT
            
            if role != required_role:
                logger.warning(
                    f"Role denied: {client.get('client_id')} "
                    f"has role {role}, but {required_role} required"
                )
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Role {required_role} required"
                )
            
            return await func(*args, **kwargs)
        
        return wrapper
    
    return decorator
