"""OAuth authentication middleware for Okta, Entra ID, and Keycloak."""

from typing import Optional, Dict, Any
from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
import httpx
from loguru import logger

from src.core.config import settings
from src.core.database import Database


security = HTTPBearer(auto_error=False)


class OAuthProvider:
    """Base OAuth provider class."""
    
    async def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Verify OAuth token and return user info."""
        raise NotImplementedError


class OktaProvider(OAuthProvider):
    """Okta OAuth provider."""
    
    def __init__(self):
        self.domain = settings.okta_domain
        self.client_id = settings.okta_client_id
        self.issuer = f"https://{self.domain}/oauth2/default"
        self.jwks_uri = f"{self.issuer}/v1/keys"
        self._jwks_cache: Optional[Dict] = None
    
    async def get_jwks(self) -> Dict:
        """Fetch JSON Web Key Set from Okta."""
        if self._jwks_cache:
            return self._jwks_cache
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(self.jwks_uri, timeout=10.0)
                response.raise_for_status()
                self._jwks_cache = response.json()
                return self._jwks_cache
        except Exception as e:
            logger.error(f"Failed to fetch Okta JWKS: {e}")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="OAuth provider unavailable"
            )
    
    async def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        """
        Verify Okta JWT token.
        
        Args:
            token: JWT token
            
        Returns:
            User info dict or None
        """
        try:
            # Decode token header to get key ID
            unverified_header = jwt.get_unverified_header(token)
            kid = unverified_header.get('kid')
            
            if not kid:
                logger.warning("Token missing key ID")
                return None
            
            # Get JWKS
            jwks = await self.get_jwks()
            
            # Find the signing key
            signing_key = None
            for key in jwks.get('keys', []):
                if key.get('kid') == kid:
                    signing_key = key
                    break
            
            if not signing_key:
                logger.warning(f"Signing key {kid} not found in JWKS")
                return None
            
            # Verify and decode token
            payload = jwt.decode(
                token,
                signing_key,
                algorithms=['RS256'],
                audience=self.client_id,
                issuer=self.issuer
            )
            
            # Extract user information
            user_info = {
                'sub': payload.get('sub'),
                'email': payload.get('email'),
                'name': payload.get('name'),
                'provider': 'okta',
                'claims': payload
            }
            
            logger.info(f"Okta token verified for user: {user_info['email']}")
            return user_info
            
        except JWTError as e:
            logger.warning(f"JWT verification failed: {e}")
            return None
        except Exception as e:
            logger.error(f"Error verifying Okta token: {e}")
            return None


class EntraIDProvider(OAuthProvider):
    """Microsoft Entra ID (Azure AD) OAuth provider."""
    
    def __init__(self):
        self.tenant_id = settings.entra_tenant_id
        self.client_id = settings.entra_client_id
        self.issuer = f"https://login.microsoftonline.com/{self.tenant_id}/v2.0"
        self.jwks_uri = f"https://login.microsoftonline.com/{self.tenant_id}/discovery/v2.0/keys"
        self._jwks_cache: Optional[Dict] = None
    
    async def get_jwks(self) -> Dict:
        """Fetch JSON Web Key Set from Entra ID."""
        if self._jwks_cache:
            return self._jwks_cache
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(self.jwks_uri, timeout=10.0)
                response.raise_for_status()
                self._jwks_cache = response.json()
                return self._jwks_cache
        except Exception as e:
            logger.error(f"Failed to fetch Entra ID JWKS: {e}")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="OAuth provider unavailable"
            )
    
    async def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        """
        Verify Entra ID JWT token.
        
        Args:
            token: JWT token
            
        Returns:
            User info dict or None
        """
        try:
            # Decode token header to get key ID
            unverified_header = jwt.get_unverified_header(token)
            kid = unverified_header.get('kid')
            
            if not kid:
                logger.warning("Token missing key ID")
                return None
            
            # Get JWKS
            jwks = await self.get_jwks()
            
            # Find the signing key
            signing_key = None
            for key in jwks.get('keys', []):
                if key.get('kid') == kid:
                    signing_key = key
                    break
            
            if not signing_key:
                logger.warning(f"Signing key {kid} not found in JWKS")
                return None
            
            # Verify and decode token
            payload = jwt.decode(
                token,
                signing_key,
                algorithms=['RS256'],
                audience=self.client_id,
                issuer=self.issuer
            )
            
            # Extract user information
            user_info = {
                'sub': payload.get('sub') or payload.get('oid'),
                'email': payload.get('email') or payload.get('preferred_username'),
                'name': payload.get('name'),
                'provider': 'entra_id',
                'claims': payload
            }
            
            logger.info(f"Entra ID token verified for user: {user_info['email']}")
            return user_info
            
        except JWTError as e:
            logger.warning(f"JWT verification failed: {e}")
            return None
        except Exception as e:
            logger.error(f"Error verifying Entra ID token: {e}")
            return None


class KeycloakProvider(OAuthProvider):
    """Keycloak OIDC provider."""

    def __init__(self):
        self.base_url = settings.keycloak_url
        self.realm = settings.keycloak_realm
        self.client_id = settings.keycloak_client_id
        self.issuer = f"{self.base_url}/realms/{self.realm}"
        self.jwks_uri = f"{self.issuer}/protocol/openid-connect/certs"
        self._jwks_cache: Optional[Dict] = None

    async def get_jwks(self) -> Dict:
        """Fetch JSON Web Key Set from Keycloak."""
        if self._jwks_cache:
            return self._jwks_cache
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(self.jwks_uri, timeout=10.0)
                response.raise_for_status()
                self._jwks_cache = response.json()
                return self._jwks_cache
        except Exception as e:
            logger.error(f"Failed to fetch Keycloak JWKS: {e}")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="OAuth provider unavailable"
            )

    async def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Verify Keycloak JWT token."""
        try:
            unverified_header = jwt.get_unverified_header(token)
            kid = unverified_header.get('kid')
            if not kid:
                return None

            jwks = await self.get_jwks()
            signing_key = next(
                (k for k in jwks.get('keys', []) if k.get('kid') == kid), None
            )

            # Key not found — JWKS may have rotated, bust cache and retry once
            if not signing_key:
                self._jwks_cache = None
                jwks = await self.get_jwks()
                signing_key = next(
                    (k for k in jwks.get('keys', []) if k.get('kid') == kid), None
                )

            if not signing_key:
                logger.warning(f"Signing key {kid} not found in Keycloak JWKS")
                return None

            payload = jwt.decode(
                token,
                signing_key,
                algorithms=['RS256'],
                audience=self.client_id,
                issuer=self.issuer,
            )

            realm_roles = payload.get('realm_access', {}).get('roles', [])
            groups = payload.get('groups', [])

            user_info = {
                'sub': payload.get('sub'),
                'email': payload.get('email'),
                'name': payload.get('name'),
                'provider': 'keycloak',
                'roles': realm_roles,
                'groups': groups,
                'claims': payload,
            }

            logger.info(f"Keycloak token verified for user: {user_info['email']}")
            return user_info

        except JWTError as e:
            logger.warning(f"Keycloak JWT verification failed: {e}")
            return None
        except Exception as e:
            logger.error(f"Error verifying Keycloak token: {e}")
            return None


# Provider instances
okta_provider = OktaProvider()
entra_provider = EntraIDProvider()
keycloak_provider = KeycloakProvider()


async def verify_oauth_token(credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)) -> Optional[Dict[str, Any]]:
    """
    Verify OAuth token from either Okta or Entra ID.
    
    Args:
        credentials: HTTP authorization credentials
        
    Returns:
        User info dict or None
    """
    if not credentials:
        return None
    
    token = credentials.credentials
    
    # Try Okta first
    if settings.okta_domain:
        user_info = await okta_provider.verify_token(token)
        if user_info:
            return user_info
    
    # Try Entra ID
    if settings.entra_tenant_id:
        user_info = await entra_provider.verify_token(token)
        if user_info:
            return user_info

    # Try Keycloak
    if settings.keycloak_url:
        user_info = await keycloak_provider.verify_token(token)
        if user_info:
            return user_info

    return None


async def get_oauth_user(credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)) -> Dict[str, Any]:
    """
    FastAPI dependency to get and verify OAuth user.
    
    Args:
        credentials: HTTP authorization credentials
        
    Returns:
        User info dict
        
    Raises:
        HTTPException: If token is missing or invalid
    """
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Bearer token required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user_info = await verify_oauth_token(credentials)
    
    if not user_info:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Optionally sync user to database
    db = Database.get_db()
    existing_user = await db.users.find_one({"email": user_info['email']})
    
    if not existing_user:
        # Create user in database
        from src.models.database import User, UserRole
        import uuid
        
        user = User(
            user_id=str(uuid.uuid4()),
            username=user_info['email'].split('@')[0],
            email=user_info['email'],
            full_name=user_info.get('name'),
            role=UserRole.USER,
            metadata={'oauth_provider': user_info['provider'], 'oauth_sub': user_info['sub']}
        )
        
        await db.users.insert_one(user.model_dump())
        logger.info(f"Created new user from OAuth: {user.email}")
    
    return user_info


async def get_current_user_flexible(
    api_key: Optional[str] = Depends(lambda: None),
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> Dict[str, Any]:
    """
    Flexible authentication that accepts either API key or OAuth token.
    
    Returns:
        User/client info dict
        
    Raises:
        HTTPException: If authentication fails
    """
    # Try OAuth first
    if credentials:
        user_info = await verify_oauth_token(credentials)
        if user_info:
            return user_info
    
    # Try API key
    if api_key:
        from src.middleware.api_key import verify_api_key
        client = await verify_api_key(api_key)
        if client:
            return client
    
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Authentication required (API key or Bearer token)",
    )
