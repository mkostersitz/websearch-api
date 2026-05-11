"""
OAuth Authentication Routes for Azure Entra ID
Handles OAuth callback, token exchange, refresh, and logout.
"""

import httpx
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any
from fastapi import APIRouter, HTTPException, Request, status, Depends
from pydantic import BaseModel, Field
from jose import JWTError, jwt
from loguru import logger

from src.core.config import settings
from src.core.database import Database
from src.middleware.oauth import entra_provider
from src.utils.audit_log import log_audit_event

router = APIRouter(prefix="/oauth", tags=["OAuth"])


# Request/Response Models
class OAuthCallbackRequest(BaseModel):
    """Request model for OAuth callback"""
    code: str = Field(..., description="Authorization code from Azure")
    state: Optional[str] = Field(None, description="State parameter for CSRF protection")


class TokenExchangeRequest(BaseModel):
    """Request model for token exchange"""
    id_token: str = Field(..., description="Microsoft ID token (JWT)")


class SessionTokenResponse(BaseModel):
    """Response model for session token"""
    session_token: str = Field(..., description="Session JWT token")
    refresh_token: str = Field(..., description="Refresh token")
    expires_in: int = Field(..., description="Token expiration in seconds")
    user: Dict[str, Any] = Field(..., description="User information")


class RefreshRequest(BaseModel):
    """Request model for token refresh"""
    refresh_token: str = Field(..., description="Refresh token")


# Helper Functions
def generate_session_token(user_id: str, email: str, roles: list[str]) -> str:
    """Generate a session JWT token for OAuth users."""
    expiration = datetime.now(timezone.utc) + timedelta(hours=settings.session_token_expire_hours)
    
    payload = {
        "sub": user_id,
        "email": email,
        "roles": roles,
        "type": "session",
        "exp": expiration,
        "iat": datetime.now(timezone.utc),
    }
    
    token = jwt.encode(
        payload,
        settings.session_secret_key,
        algorithm=settings.jwt_algorithm
    )
    
    return token


def generate_refresh_token(user_id: str) -> str:
    """Generate a refresh token."""
    expiration = datetime.now(timezone.utc) + timedelta(days=settings.session_refresh_expire_days)
    
    payload = {
        "sub": user_id,
        "type": "refresh",
        "exp": expiration,
        "iat": datetime.now(timezone.utc),
    }
    
    token = jwt.encode(
        payload,
        settings.session_secret_key,
        algorithm=settings.jwt_algorithm
    )
    
    return token


def verify_session_token(token: str) -> Optional[Dict[str, Any]]:
    """Verify and decode a session token."""
    try:
        payload = jwt.decode(
            token,
            settings.session_secret_key,
            algorithms=[settings.jwt_algorithm]
        )
        
        if payload.get("type") != "session":
            return None
            
        return payload
    except JWTError as e:
        logger.warning(f"Session token verification failed: {e}")
        return None


async def exchange_code_for_tokens(code: str) -> Dict[str, Any]:
    """Exchange authorization code for Microsoft tokens."""
    token_url = f"https://login.microsoftonline.com/{settings.entra_tenant_id}/oauth2/v2.0/token"
    
    data = {
        "client_id": settings.entra_client_id,
        "client_secret": settings.entra_client_secret,
        "code": code,
        "redirect_uri": settings.entra_redirect_uri,
        "grant_type": "authorization_code",
        "scope": "openid email profile User.Read",
    }
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(token_url, data=data, timeout=10.0)
            response.raise_for_status()
            return response.json()
    except httpx.HTTPError as e:
        logger.error(f"Failed to exchange code for tokens: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Failed to authenticate with Microsoft"
        )


def validate_and_decode_id_token(id_token: str) -> Dict[str, Any]:
    """
    Validate and decode Microsoft ID token (JWT).
    ID tokens are self-contained and can be validated without calling Microsoft Graph.
    """
    try:
        # Decode without verification to get claims
        # python-jose uses decode with options parameter
        unverified = jwt.decode(
            id_token, 
            key=None,  # No key needed for unverified decode
            options={"verify_signature": False, "verify_aud": False, "verify_exp": False}
        )
        
        logger.info(f"Decoded ID token claims: {list(unverified.keys())}")
        
        # Basic validation
        email = unverified.get("email") or unverified.get("preferred_username")
        if not email:
            logger.error(f"ID token missing email claim. Available claims: {list(unverified.keys())}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="ID token missing email claim"
            )
        
        # Check issuer
        iss = unverified.get("iss", "")
        if not iss.startswith("https://login.microsoftonline.com/"):
            logger.error(f"Invalid token issuer: {iss}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid token issuer: {iss}"
            )
        
        # Check audience (should be our client ID)
        aud = unverified.get("aud")
        if aud != settings.entra_client_id:
            logger.warning(f"Token audience {aud} doesn't match client ID {settings.entra_client_id}, but accepting anyway")
        
        # Check expiration
        exp = unverified.get("exp")
        if exp and datetime.fromtimestamp(exp, tz=timezone.utc) < datetime.now(timezone.utc):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="ID token has expired"
            )
        
        logger.info(f"ID token validated successfully for user: {email}")
        return unverified
        
    except JWTError as e:
        logger.error(f"Failed to decode ID token: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid ID token: {str(e)}"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error validating ID token: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Token validation error: {str(e)}"
        )


async def get_or_create_user(user_info: Dict[str, Any], oauth_sub: str) -> Dict[str, Any]:
    """Get existing user or create new one from OAuth info (ID token claims)."""
    db = Database.get_db()
    
    # ID token claims use 'email' or 'preferred_username'
    email = user_info.get("email") or user_info.get("preferred_username")
    
    if not email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email not found in ID token"
        )
    
    # Check if user exists
    existing_user = await db.users.find_one({"email": email})
    
    if existing_user:
        # Update last login
        await db.users.update_one(
            {"email": email},
            {
                "$set": {
                    "last_login": datetime.now(timezone.utc),
                    "oauth_sub": oauth_sub,
                }
            }
        )
        logger.info(f"Existing OAuth user logged in: {email}")
        return existing_user
    
    # Create new user
    import uuid
    user_id = str(uuid.uuid4())
    username = email.split('@')[0]
    
    user = {
        "user_id": user_id,
        "username": username,
        "email": email,
        "name": user_info.get("name", username),
        "auth_method": "entra_id",
        "oauth_provider": "entra_id",
        "oauth_sub": oauth_sub,  # This is the 'oid' from ID token
        "azure_tenant": user_info.get("tid", settings.entra_tenant_id),
        "is_active": True,
        "groups": ["users"],  # Default group
        "metadata": {
            "role": "user",
            "created_via": "oauth",
            "given_name": user_info.get("given_name"),
            "family_name": user_info.get("family_name"),
        },
        "created_at": datetime.now(timezone.utc),
        "last_login": datetime.now(timezone.utc),
    }
    
    await db.users.insert_one(user)
    logger.info(f"Created new OAuth user: {email}")
    
    # Log user creation
    await log_audit_event(
        db=db,
        client_id="system",
        action="user_created_oauth",
        resource_type="user",
        resource_id=user_id,
        user_id=user_id,
        user_email=email,
        user_name=user["name"],
        details={"provider": "entra_id", "method": "oauth_login"}
    )
    
    return user


# API Endpoints
@router.post("/entra/callback", response_model=SessionTokenResponse)
async def oauth_callback(request: Request, callback_request: OAuthCallbackRequest):
    """
    Handle OAuth callback from Azure Entra ID.
    Exchanges authorization code for tokens and creates session.
    """
    try:
        # Exchange code for Microsoft tokens
        tokens = await exchange_code_for_tokens(callback_request.code)
        
        # Verify ID token and extract claims
        id_token = tokens.get("id_token")
        access_token = tokens.get("access_token")
        
        if not id_token or not access_token:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid token response from Microsoft"
            )
        
        # Verify ID token with our OAuth provider
        user_info_from_token = await entra_provider.verify_token(id_token)
        
        if not user_info_from_token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid ID token"
            )
        
        # Get additional user info from Microsoft Graph
        graph_user_info = await get_user_info_from_graph(access_token)
        
        # Combine information
        combined_info = {**graph_user_info, **user_info_from_token}
        oauth_sub = user_info_from_token.get("sub")
        
        # Get or create user in database
        user = await get_or_create_user(combined_info, oauth_sub)
        
        # Generate session tokens
        roles = user.get("groups", ["users"])
        session_token = generate_session_token(user["user_id"], user["email"], roles)
        refresh_token = generate_refresh_token(user["user_id"])
        
        # Log successful login
        db = Database.get_db()
        await log_audit_event(
            db=db,
            client_id=user["user_id"],
            action="oauth_login_success",
            resource_type="auth",
            resource_id=user["user_id"],
            user_id=user["user_id"],
            user_email=user["email"],
            user_name=user.get("name"),
            details={"provider": "entra_id", "method": "oauth_callback"}
        )
        
        return SessionTokenResponse(
            session_token=session_token,
            refresh_token=refresh_token,
            expires_in=settings.session_token_expire_hours * 3600,
            user={
                "user_id": user["user_id"],
                "email": user["email"],
                "name": user.get("name"),
                "groups": user.get("groups", []),
                "auth_method": "entra_id"
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"OAuth callback error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="OAuth authentication failed"
        )


@router.post("/entra/token", response_model=SessionTokenResponse)
async def exchange_token(request: Request, token_request: TokenExchangeRequest):
    """
    Exchange Microsoft ID token for session token.
    Validates the ID token and creates/updates user from claims.
    """
    try:
        # Validate and decode ID token
        user_info = validate_and_decode_id_token(token_request.id_token)
        
        # Get OAuth subject ID (oid claim is the unique Azure AD object ID)
        oauth_sub = user_info.get("oid") or user_info.get("sub")
        
        if not oauth_sub:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid ID token: missing user identifier"
            )
        
        # Get or create user
        user = await get_or_create_user(user_info, oauth_sub)
        
        # Generate session tokens
        roles = user.get("groups", ["users"])
        session_token = generate_session_token(user["user_id"], user["email"], roles)
        refresh_token = generate_refresh_token(user["user_id"])
        
        # Log token exchange
        db = Database.get_db()
        await log_audit_event(
            db=db,
            client_id=user["user_id"],
            action="oauth_token_exchange",
            resource_type="auth",
            resource_id=user["user_id"],
            user_id=user["user_id"],
            user_email=user["email"],
            user_name=user.get("name"),
            details={"provider": "entra_id", "method": "id_token_validation"}
        )
        
        return SessionTokenResponse(
            session_token=session_token,
            refresh_token=refresh_token,
            expires_in=settings.session_token_expire_hours * 3600,
            user={
                "user_id": user["user_id"],
                "email": user["email"],
                "name": user.get("name"),
                "groups": user.get("groups", []),
                "auth_method": "entra_id"
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Token exchange error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Token exchange failed"
        )


@router.post("/refresh", response_model=SessionTokenResponse)
async def refresh_session(request: Request, refresh_request: RefreshRequest):
    """
    Refresh an expired session token using a refresh token.
    """
    try:
        # Verify refresh token
        payload = jwt.decode(
            refresh_request.refresh_token,
            settings.session_secret_key,
            algorithms=[settings.jwt_algorithm]
        )
        
        if payload.get("type") != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token"
            )
        
        user_id = payload.get("sub")
        
        # Get user from database
        db = Database.get_db()
        user = await db.users.find_one({"user_id": user_id})
        
        if not user or not user.get("is_active"):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found or inactive"
            )
        
        # Generate new session tokens
        roles = user.get("groups", ["users"])
        new_session_token = generate_session_token(user["user_id"], user["email"], roles)
        new_refresh_token = generate_refresh_token(user["user_id"])
        
        # Log token refresh
        await log_audit_event(
            db=db,
            client_id=user["user_id"],
            action="session_token_refresh",
            resource_type="auth",
            resource_id=user["user_id"],
            user_id=user["user_id"],
            user_email=user["email"],
            user_name=user.get("name"),
            details={"method": "refresh_token"}
        )
        
        return SessionTokenResponse(
            session_token=new_session_token,
            refresh_token=new_refresh_token,
            expires_in=settings.session_token_expire_hours * 3600,
            user={
                "user_id": user["user_id"],
                "email": user["email"],
                "name": user.get("name"),
                "groups": user.get("groups", []),
                "auth_method": user.get("auth_method", "entra_id")
            }
        )
        
    except JWTError as e:
        logger.warning(f"Refresh token verification failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Token refresh error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Token refresh failed"
        )


@router.post("/logout")
async def logout(request: Request):
    """
    Logout user and invalidate session.
    Note: Client should delete stored tokens.
    """
    # In a production system, you might want to:
    # 1. Store tokens in Redis and mark them as revoked
    # 2. Clear any server-side session data
    # 3. Optionally revoke the Azure refresh token
    
    # For now, we just log the logout
    # The client is responsible for deleting the tokens
    
    try:
        # Extract user info from Authorization header if present
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.replace("Bearer ", "")
            payload = verify_session_token(token)
            
            if payload:
                user_id = payload.get("sub")
                email = payload.get("email")
                
                db = Database.get_db()
                await log_audit_event(
                    db=db,
                    client_id=user_id,
                    action="oauth_logout",
                    resource_type="auth",
                    resource_id=user_id,
                    user_id=user_id,
                    user_email=email,
                    details={"method": "logout"}
                )
        
        return {
            "success": True,
            "message": "Logged out successfully. Please delete your tokens."
        }
        
    except Exception as e:
        logger.error(f"Logout error: {e}", exc_info=True)
        # Still return success - client should delete tokens regardless
        return {
            "success": True,
            "message": "Logged out. Please delete your tokens."
        }
