"""
User Authentication API Routes
Handles user API key requests, revocation, user info retrieval, and login.
"""

import hashlib
import secrets
import string
from datetime import datetime, timezone
from typing import Optional
import bcrypt

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, EmailStr, Field

from src.core.database import Database
from src.middleware.api_key import get_api_key_client
from src.utils.audit_log import log_audit_event

router = APIRouter(prefix="/auth", tags=["Authentication"])


# Request/Response Models
class APIKeyRequest(BaseModel):
    """Request model for API key generation"""
    email: EmailStr = Field(..., description="User's email address")


class APIKeyResponse(BaseModel):
    """Response model for API key generation"""
    api_key: str = Field(..., description="Generated API key (shown only once)")
    user_id: str
    username: str
    email: str
    name: str
    groups: list[str]
    quotas: dict
    message: str = "API key generated successfully. Store it securely - it won't be shown again."


class UserInfoResponse(BaseModel):
    """Response model for user info endpoint"""
    user_id: str
    username: str
    email: str
    name: str
    groups: list[str]
    is_active: bool
    api_key_status: str
    quotas: dict
    policies_applied: list[dict]
    usage_stats: dict


class RevokeKeyRequest(BaseModel):
    """Request model for API key revocation"""
    reason: Optional[str] = Field(None, description="Optional reason for revocation")


class LoginRequest(BaseModel):
    """Request model for username/password login"""
    username: str = Field(..., min_length=1, max_length=100)
    password: str = Field(..., min_length=1)


class LoginResponse(BaseModel):
    """Response model for login"""
    success: bool
    first_login: bool = Field(default=False, description="True if this is the first login")
    message: str
    user_info: Optional[dict] = None


class ChangePasswordRequest(BaseModel):
    """Request model for changing password"""
    username: str
    old_password: str
    new_password: str = Field(..., min_length=8, description="New password (min 8 characters)")


class CreateAdminKeyRequest(BaseModel):
    """Request model for creating admin API key"""
    username: str
    password: str
    force: bool = Field(default=False, description="Revoke existing key and generate a new one")


# Helper Functions
def generate_user_api_key() -> str:
    """Generate a secure random API key with UK_ prefix"""
    alphabet = string.ascii_letters + string.digits
    random_part = ''.join(secrets.choice(alphabet) for _ in range(32))
    return f"UK_{random_part}"


def generate_admin_api_key() -> str:
    """Generate a secure random API key with GA_ prefix"""
    alphabet = string.ascii_letters + string.digits
    random_part = ''.join(secrets.choice(alphabet) for _ in range(38))
    return f"GA_{random_part}"


def hash_api_key(api_key: str) -> str:
    """Hash an API key using SHA-256"""
    return hashlib.sha256(api_key.encode()).hexdigest()


def hash_password(password: str) -> str:
    """Hash a password using bcrypt"""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')


def verify_password(password: str, hashed: str) -> bool:
    """Verify a password against its hash"""
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))


async def check_rate_limit(request: Request, email: str, db) -> bool:
    """
    Check rate limit for API key requests
    Limit: 5 requests per hour per IP address
    """
    client_ip = request.client.host if request.client else "unknown"
    rate_limit_key = f"key_request:{client_ip}:{email}"
    
    # Get recent requests from a hypothetical rate_limits collection
    # For now, we'll use a simple time-based check
    current_time = datetime.now(timezone.utc)
    rate_limits = db["rate_limits"]
    
    # Count requests in the last hour
    one_hour_ago = datetime.now(timezone.utc).timestamp() - 3600
    recent_requests = await rate_limits.count_documents({
        "key": rate_limit_key,
        "timestamp": {"$gt": one_hour_ago}
    })
    
    if recent_requests >= 5:
        return False
    
    # Log this request
    await rate_limits.insert_one({
        "key": rate_limit_key,
        "timestamp": current_time.timestamp(),
        "email": email,
        "ip": client_ip
    })
    
    return True


# API Endpoints
@router.post("/request-key", response_model=APIKeyResponse, status_code=status.HTTP_201_CREATED)
async def request_api_key(
    request: Request,
    key_request: APIKeyRequest
):
    """
    Request an API key using email address.
    
    This is a public endpoint that allows users to request API keys.
    Rate limited to 5 requests per hour per IP address.
    """
    email = key_request.email.lower()
    db = Database.get_db()
    
    # Check rate limit
    if not await check_rate_limit(request, email, db):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many API key requests. Please try again later."
        )
    
    # Look up user by email
    users = db.users
    user = await users.find_one({"email": email})
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No user found with this email address. Please contact your administrator."
        )
    
    if not user.get("is_active", True):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive. Please contact your administrator."
        )
    
    # Generate API key
    api_key = generate_user_api_key()
    api_key_hash = hash_api_key(api_key)
    
    # Create or update client record
    clients = db.clients
    client_id = f"user-{user['user_id']}"
    
    client_data = {
        "client_id": client_id,
        "client_name": user.get("name", user.get("username", email)),
        "client_type": "api_key",
        "owner_id": user["user_id"],
        "api_key_hash": api_key_hash,
        "quota_per_day": user.get("quota_per_day", 500),
        "quota_per_month": user.get("quota_per_month", 15000),
        "is_active": True,
        "created_at": datetime.now(timezone.utc),
        "last_key_generated": datetime.now(timezone.utc),
        "metadata": {
            "role": "user",
            "email": email,
            "groups": user.get("groups", [])
        }
    }
    
    # Update or insert
    await clients.update_one(
        {"client_id": client_id},
        {"$set": client_data},
        upsert=True
    )
    
    # Update user record with key generation timestamp
    await users.update_one(
        {"user_id": user["user_id"]},
        {
            "$set": {
                "api_key_hash": api_key_hash,
                "last_key_generated": datetime.now(timezone.utc)
            }
        }
    )
    
    # Log audit event with enhanced details
    await log_audit_event(
        db=db,
        client_id=client_id,
        action="api_key_generated",
        resource_type="api_key",
        resource_id=client_id,
        user_id=user["user_id"],
        user_email=email,
        user_name=user.get("name", ""),
        request_info={
            "method": "POST",
            "path": "/api/v1/auth/request-key",
            "ip_address": request.client.host if request.client else "unknown",
            "user_agent": request.headers.get("user-agent")
        },
        details={
            "groups": user.get("groups", [])
        }
    )
    
    # Return response
    return APIKeyResponse(
        api_key=api_key,
        user_id=user["user_id"],
        username=user.get("username", ""),
        email=email,
        name=user.get("name", ""),
        groups=user.get("groups", []),
        quotas={
            "daily_limit": client_data["quota_per_day"],
            "monthly_limit": client_data["quota_per_month"]
        }
    )


@router.post("/revoke-key", status_code=status.HTTP_200_OK)
async def revoke_api_key(
    revoke_request: RevokeKeyRequest,
    current_client: dict = Depends(get_api_key_client)
):
    """
    Revoke the current user's API key.
    Requires authentication with the key to be revoked.
    """
    client_id = current_client["client_id"]
    db = Database.get_db()
    
    # Check if this is a user key (not admin)
    if not client_id.startswith("user-"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This endpoint is only for user API keys. Admin keys cannot be revoked this way."
        )
    
    # Deactivate the client
    clients = db.clients
    result = await clients.update_one(
        {"client_id": client_id},
        {
            "$set": {
                "is_active": False,
                "revoked_at": datetime.now(timezone.utc),
                "revocation_reason": revoke_request.reason or "User requested"
            }
        }
    )
    
    if result.modified_count == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="API key not found or already revoked"
        )
    
    # Log audit event
    await log_audit_event(
        db=db,
        client_id=client_id,
        action="api_key_revoked",
        resource_type="api_key",
        resource_id=client_id,
        details={
            "reason": revoke_request.reason,
            "owner_id": current_client.get("owner_id")
        }
    )
    
    return {"message": "API key revoked successfully"}


@router.get("/me", response_model=UserInfoResponse)
async def get_user_info(
    current_client: dict = Depends(get_api_key_client)
):
    """
    Get information about the current authenticated user.
    Returns user details, policies, quotas, and usage statistics.
    """
    # Get user information
    owner_id = current_client.get("owner_id")
    if not owner_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This endpoint is only available for user API keys"
        )
    
    db = Database.get_db()
    users = db.users
    user = await users.find_one({"user_id": owner_id})
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Get applicable policies
    policies = db.policies
    user_groups = user.get("groups", [])
    
    # Find policies that apply to this user
    applicable_policies = []
    async for policy in policies.find({
        "$or": [
            {"scope": "global"},
            {"target_group_ids": {"$in": user_groups}},
            {"target_user_ids": owner_id}
        ],
        "is_active": True
    }).sort("priority", -1):  # Higher priority first
        applicable_policies.append({
            "policy_id": policy["policy_id"],
            "policy_name": policy["policy_name"],
            "scope": policy["scope"],
            "priority": policy["priority"],
            "search_policy": policy.get("search_policy", {})
        })
    
    # Get usage statistics
    audit_logs = db.audit_logs
    today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    month_start = datetime.now(timezone.utc).replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    
    searches_today = await audit_logs.count_documents({
        "client_id": current_client["client_id"],
        "action": "search",
        "timestamp": {"$gte": today_start}
    })
    
    searches_this_month = await audit_logs.count_documents({
        "client_id": current_client["client_id"],
        "action": "search",
        "timestamp": {"$gte": month_start}
    })
    
    # Determine API key status
    api_key_status = "active" if current_client.get("is_active", True) else "revoked"
    if current_client.get("last_key_generated"):
        api_key_status += f" (generated {current_client['last_key_generated'].strftime('%Y-%m-%d')})"
    
    return UserInfoResponse(
        user_id=user["user_id"],
        username=user.get("username", ""),
        email=user.get("email", ""),
        name=user.get("name", ""),
        groups=user_groups,
        is_active=user.get("is_active", True),
        api_key_status=api_key_status,
        quotas={
            "daily_limit": current_client.get("quota_per_day", 500),
            "monthly_limit": current_client.get("quota_per_month", 15000),
            "used_today": searches_today,
            "used_this_month": searches_this_month,
            "remaining_today": max(0, current_client.get("quota_per_day", 500) - searches_today),
            "remaining_this_month": max(0, current_client.get("quota_per_month", 15000) - searches_this_month)
        },
        policies_applied=applicable_policies,
        usage_stats={
            "searches_today": searches_today,
            "searches_this_month": searches_this_month,
            "total_policies": len(applicable_policies)
        }
    )


@router.post("/login", response_model=LoginResponse)
async def login(request: Request, login_request: LoginRequest):
    """
    Authenticate with username and password.
    Default admin credentials: admin/admin (must be changed on first login).
    """
    db = Database.get_db()
    users = db.users
    
    # Find user by username
    user = await users.find_one({"username": login_request.username})
    
    if not user:
        # Log failed attempt
        await log_audit_event(
            db=db,
            client_id="anonymous",
            action="login_failed",
            resource_type="auth",
            resource_id=login_request.username,
            details={"reason": "user_not_found"}
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password"
        )
    
    # Check if account is active
    if not user.get("is_active", True):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is inactive. Please contact your administrator."
        )
    
    # Verify password
    password_hash = user.get("password_hash")
    if not password_hash:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Account not properly configured"
        )
    
    if not verify_password(login_request.password, password_hash):
        # Log failed attempt
        await log_audit_event(
            db=db,
            client_id="anonymous",
            action="login_failed",
            resource_type="auth",
            resource_id=login_request.username,
            details={"reason": "invalid_password"}
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password"
        )
    
    # Check if this is first login (default password)
    first_login = user.get("first_login", False)
    
    # Log successful login
    await log_audit_event(
        db=db,
        client_id=user.get("user_id", "unknown"),
        action="login_success",
        resource_type="auth",
        resource_id=login_request.username,
        user_id=user.get("user_id"),
        user_name=user.get("name", ""),
        user_email=user.get("email", ""),
        details={"first_login": first_login}
    )
    
    # Update last login timestamp
    await users.update_one(
        {"username": login_request.username},
        {"$set": {"last_login": datetime.now(timezone.utc)}}
    )
    
    return LoginResponse(
        success=True,
        first_login=first_login,
        message="Login successful" if not first_login else "First login - please change your password",
        user_info={
            "user_id": user.get("user_id"),
            "username": user.get("username"),
            "email": user.get("email"),
            "name": user.get("name"),
            "groups": user.get("groups", []),
            "role": user.get("role", "user")
        }
    )


@router.post("/change-password")
async def change_password(request: Request, change_request: ChangePasswordRequest):
    """
    Change user password. Used for first-time password setup and password changes.
    """
    db = Database.get_db()
    users = db.users
    
    # Find user
    user = await users.find_one({"username": change_request.username})
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Verify old password
    if not verify_password(change_request.old_password, user.get("password_hash", "")):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Current password is incorrect"
        )
    
    # Hash new password
    new_password_hash = hash_password(change_request.new_password)
    
    # Update password and clear first_login flag
    await users.update_one(
        {"username": change_request.username},
        {
            "$set": {
                "password_hash": new_password_hash,
                "first_login": False,
                "password_changed_at": datetime.now(timezone.utc)
            }
        }
    )
    
    # Log password change
    await log_audit_event(
        db=db,
        client_id=user.get("user_id", "unknown"),
        action="password_changed",
        resource_type="auth",
        resource_id=change_request.username,
        user_id=user.get("user_id"),
        details={"method": "user_initiated"}
    )
    
    return {"message": "Password changed successfully"}


@router.post("/create-admin-key")
async def create_admin_key(request: Request, key_request: CreateAdminKeyRequest):
    """
    Create an admin API key after password setup.
    This is called after first login password change.
    """
    db = Database.get_db()
    users = db.users
    
    # Find user
    user = await users.find_one({"username": key_request.username})
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Verify password
    if not verify_password(key_request.password, user.get("password_hash", "")):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid password"
        )
    
    # Check if user is admin
    user_role = user.get("role", "user")
    if user_role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can create admin API keys"
        )
    
    # Check if API key already exists
    clients = db.clients
    client_id = f"admin-{user['user_id']}"
    existing_client = await clients.find_one({"client_id": client_id})
    
    # If API key exists and is active, either block or revoke depending on force flag
    if existing_client and existing_client.get("is_active"):
        if not key_request.force:
            return {
                "existing": True,
                "message": "You already have an active API key.",
            }
        # force=True: revoke existing key so a fresh one is generated below
        await clients.update_one(
            {"client_id": client_id},
            {"$set": {"is_active": False, "revoked_at": datetime.now(timezone.utc), "revocation_reason": "Admin requested regeneration"}}
        )
        await log_audit_event(
            db=db,
            client_id=client_id,
            action="admin_key_revoked",
            resource_type="api_key",
            resource_id=client_id,
            user_id=user["user_id"],
            details={"reason": "force regeneration"}
        )
    
    # Generate new admin API key
    api_key = generate_admin_api_key()
    api_key_hash = hash_api_key(api_key)
    
    client_data = {
        "client_id": client_id,
        "client_name": f"Admin: {user.get('name', user.get('username'))}",
        "client_type": "api_key",
        "owner_id": user["user_id"],
        "role": "admin",
        "api_key_hash": api_key_hash,
        "quota_per_day": -1,  # Unlimited for admin
        "quota_per_month": -1,  # Unlimited for admin
        "is_active": True,
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc),
        "metadata": {
            "email": user.get("email"),
            "groups": user.get("groups", [])
        }
    }
    
    # Update or insert
    await clients.update_one(
        {"client_id": client_id},
        {"$set": client_data},
        upsert=True
    )
    
    # Update user record
    await users.update_one(
        {"user_id": user["user_id"]},
        {
            "$set": {
                "api_key_hash": api_key_hash,
                "last_key_generated": datetime.now(timezone.utc)
            }
        }
    )
    
    # Log key creation
    await log_audit_event(
        db=db,
        client_id=client_id,
        action="admin_key_generated",
        resource_type="api_key",
        resource_id=client_id,
        user_id=user["user_id"],
        user_email=user.get("email"),
        user_name=user.get("name", ""),
        details={"key_type": "admin"}
    )
    
    return {
        "api_key": api_key,
        "existing": False,
        "client_id": client_id,
        "user_id": user["user_id"],
        "username": user["username"],
        "email": user.get("email", ""),
        "name": user.get("name", user["username"]),
        "groups": user.get("groups", []),
        "quotas": {
            "per_day": -1,
            "per_month": -1
        },
        "message": "Admin API key created successfully. Store it securely - it won't be shown again."
    }


async def initialize_default_admin():
    """Initialize default admin user if it doesn't exist"""
    db = Database.get_db()
    users = db.users
    
    # Check if admin exists
    admin = await users.find_one({"username": "admin"})
    if not admin:
        # Create default admin
        default_password_hash = hash_password("admin")
        admin_user = {
            "user_id": "admin-001",
            "username": "admin",
            "email": "admin@websearch.local",
            "name": "Administrator",
            "password_hash": default_password_hash,
            "first_login": True,
            "is_active": True,
            "role": "admin",
            "groups": ["admins"],
            "created_at": datetime.now(timezone.utc),
            "metadata": {
                "created_by": "system"
            }
        }
        await users.insert_one(admin_user)
        print("✓ Default admin user created (username: admin, password: admin)")
