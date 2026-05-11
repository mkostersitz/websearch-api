"""
Session Token Middleware
Handles session-based authentication for OAuth users.
"""

from typing import Optional, Dict, Any
from fastapi import HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from loguru import logger

from src.core.config import settings
from src.core.database import Database


security = HTTPBearer(auto_error=False)


def verify_session_token(token: str) -> Optional[Dict[str, Any]]:
    """
    Verify and decode a session token.
    
    Args:
        token: Session JWT token
        
    Returns:
        Decoded payload or None if invalid
    """
    try:
        payload = jwt.decode(
            token,
            settings.session_secret_key,
            algorithms=[settings.jwt_algorithm]
        )
        
        # Verify token type
        if payload.get("type") != "session":
            logger.warning("Token is not a session token")
            return None
            
        return payload
        
    except JWTError as e:
        logger.warning(f"Session token verification failed: {e}")
        return None
    except Exception as e:
        logger.error(f"Error verifying session token: {e}")
        return None


async def get_session_user(token: str) -> Optional[Dict[str, Any]]:
    """
    Get user information from session token.
    
    Args:
        token: Session JWT token
        
    Returns:
        User dict from database or None
    """
    payload = verify_session_token(token)
    
    if not payload:
        return None
    
    user_id = payload.get("sub")
    
    # Get user from database
    db = Database.get_db()
    user = await db.users.find_one({"user_id": user_id})
    
    if not user or not user.get("is_active"):
        logger.warning(f"User not found or inactive: {user_id}")
        return None
    
    return user


async def get_current_user_from_session(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = None
) -> Optional[Dict[str, Any]]:
    """
    FastAPI dependency to get current user from session token.
    
    Args:
        request: FastAPI request object
        credentials: HTTP Bearer credentials
        
    Returns:
        User dict or None if not authenticated
    """
    if not credentials:
        return None
    
    token = credentials.credentials
    user = await get_session_user(token)
    
    return user


async def require_session_auth(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = None
) -> Dict[str, Any]:
    """
    FastAPI dependency that requires session authentication.
    Raises HTTPException if not authenticated.
    
    Args:
        request: FastAPI request object
        credentials: HTTP Bearer credentials
        
    Returns:
        User dict
        
    Raises:
        HTTPException: If not authenticated or token invalid
    """
    user = await get_current_user_from_session(request, credentials)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Valid session token required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return user


class SessionManager:
    """Manager for session tokens and user sessions."""
    
    @staticmethod
    async def create_session(user_id: str, email: str, roles: list[str]) -> tuple[str, str]:
        """
        Create a new session for a user.
        
        Args:
            user_id: User ID
            email: User email
            roles: User roles/groups
            
        Returns:
            Tuple of (session_token, refresh_token)
        """
        from src.api.routes.oauth import generate_session_token, generate_refresh_token
        
        session_token = generate_session_token(user_id, email, roles)
        refresh_token = generate_refresh_token(user_id)
        
        return session_token, refresh_token
    
    @staticmethod
    async def verify_and_refresh(refresh_token: str) -> Optional[tuple[str, str]]:
        """
        Verify refresh token and generate new session.
        
        Args:
            refresh_token: Refresh token
            
        Returns:
            Tuple of (new_session_token, new_refresh_token) or None
        """
        try:
            payload = jwt.decode(
                refresh_token,
                settings.session_secret_key,
                algorithms=[settings.jwt_algorithm]
            )
            
            if payload.get("type") != "refresh":
                return None
            
            user_id = payload.get("sub")
            
            # Get user
            db = Database.get_db()
            user = await db.users.find_one({"user_id": user_id})
            
            if not user or not user.get("is_active"):
                return None
            
            # Generate new tokens
            roles = user.get("groups", ["users"])
            return await SessionManager.create_session(
                user["user_id"],
                user["email"],
                roles
            )
            
        except JWTError:
            return None
    
    @staticmethod
    async def invalidate_session(session_token: str) -> bool:
        """
        Invalidate a session token.
        In a production system, you would store invalidated tokens in Redis.
        
        Args:
            session_token: Session token to invalidate
            
        Returns:
            True if successful
        """
        # For now, just return True
        # In production: store token in Redis with expiration
        # All token verification would check Redis blacklist
        return True
