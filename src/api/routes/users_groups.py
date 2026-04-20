"""User and Group management API routes."""

import csv
import io
from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File, status
from loguru import logger
from pydantic import BaseModel

from src.middleware.api_key import get_api_key_client
from src.core.database import Database


router = APIRouter(prefix="/admin", tags=["User Management"])


# Models
class UserUpdate(BaseModel):
    name: Optional[str] = None
    department: Optional[str] = None
    title: Optional[str] = None
    groups: Optional[List[str]] = None
    is_active: Optional[bool] = None
    quota_per_day: Optional[int] = None
    quota_per_month: Optional[int] = None


@router.get("/users")
async def get_users(
    current_client: dict = Depends(get_api_key_client),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500)
):
    """Get all users."""
    if current_client.get("metadata", {}).get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    db = Database.get_db()
    
    # Get users from database
    users_cursor = db.users.find({}).skip(skip).limit(limit)
    users = []
    
    async for user in users_cursor:
        # Build clean user object without sensitive data
        clean_user = {
            "user_id": user.get("user_id"),
            "email": user.get("email"),
            "name": user.get("name"),
            "username": user.get("username"),
            "department": user.get("department"),
            "title": user.get("title"),
            "groups": user.get("groups", []),
            "is_active": user.get("is_active", True),
            "quota_per_day": user.get("quota_per_day", 100),
            "quota_per_month": user.get("quota_per_month", 1000),
            "created_at": user.get("created_at"),
            "last_login": user.get("last_login"),
        }
        users.append(clean_user)
    
    return users


@router.get("/users/{user_id}")
async def get_user(
    user_id: str,
    current_client: dict = Depends(get_api_key_client)
):
    """Get a specific user."""
    if current_client.get("metadata", {}).get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    db = Database.get_db()
    user = await db.users.find_one({"user_id": user_id})
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Return clean user object without sensitive data
    clean_user = {
        "user_id": user.get("user_id"),
        "email": user.get("email"),
        "name": user.get("name"),
        "username": user.get("username"),
        "department": user.get("department"),
        "title": user.get("title"),
        "groups": user.get("groups", []),
        "is_active": user.get("is_active", True),
        "quota_per_day": user.get("quota_per_day", 100),
        "quota_per_month": user.get("quota_per_month", 1000),
        "created_at": user.get("created_at"),
        "last_login": user.get("last_login"),
    }
    
    return clean_user


@router.put("/users/{user_id}")
async def update_user(
    user_id: str,
    user_update: UserUpdate,
    current_client: dict = Depends(get_api_key_client)
):
    """Update a user."""
    if current_client.get("metadata", {}).get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    db = Database.get_db()
    
    # Build update document
    update_doc = {}
    if user_update.name is not None:
        update_doc["name"] = user_update.name
    if user_update.department is not None:
        update_doc["department"] = user_update.department
    if user_update.title is not None:
        update_doc["title"] = user_update.title
    if user_update.groups is not None:
        update_doc["groups"] = user_update.groups
    if user_update.is_active is not None:
        update_doc["is_active"] = user_update.is_active
    if user_update.quota_per_day is not None:
        update_doc["quota_per_day"] = user_update.quota_per_day
    if user_update.quota_per_month is not None:
        update_doc["quota_per_month"] = user_update.quota_per_month
    
    update_doc["updated_at"] = datetime.utcnow()
    
    # Update user
    result = await db.users.update_one(
        {"user_id": user_id},
        {"$set": update_doc}
    )
    
    if result.matched_count == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Log audit entry
    await db.audit_logs.insert_one({
        "audit_id": f"audit_{datetime.utcnow().timestamp()}",
        "timestamp": datetime.utcnow(),
        "client_id": current_client.get("client_id"),
        "action": "UPDATE_USER",
        "resource_type": "user",
        "resource_id": user_id,
        "status": "success",
        "details": update_doc
    })
    
    # Return updated user
    return await get_user(user_id, current_client)


@router.delete("/users/{user_id}")
async def delete_user(
    user_id: str,
    current_client: dict = Depends(get_api_key_client)
):
    """Delete a user."""
    if current_client.get("metadata", {}).get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    db = Database.get_db()
    
    # Delete user
    result = await db.users.delete_one({"user_id": user_id})
    
    if result.deleted_count == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Log audit entry
    await db.audit_logs.insert_one({
        "audit_id": f"audit_{datetime.utcnow().timestamp()}",
        "timestamp": datetime.utcnow(),
        "client_id": current_client.get("client_id"),
        "action": "DELETE_USER",
        "resource_type": "user",
        "resource_id": user_id,
        "status": "success"
    })
    
    logger.info(f"User {user_id} deleted by {current_client.get('client_id')}")
    
    return {"message": "User deleted successfully"}


@router.get("/groups")
async def get_groups(
    current_client: dict = Depends(get_api_key_client)
):
    """Get all groups with user counts."""
    if current_client.get("metadata", {}).get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    db = Database.get_db()
    
    # Aggregate groups from users
    pipeline = [
        {"$unwind": "$groups"},
        {"$group": {
            "_id": "$groups",
            "user_count": {"$sum": 1},
            "users": {"$addToSet": "$user_id"}
        }},
        {"$project": {
            "group_id": "$_id",
            "name": "$_id",
            "user_count": 1,
            "users": 1
        }},
        {"$sort": {"user_count": -1}}
    ]
    
    groups_data = await db.users.aggregate(pipeline).to_list(None)
    
    # Get group policies from policies collection
    groups = []
    for group_data in groups_data:
        group_id = group_data["group_id"]
        
        # Look up policies for this group
        policies = await db.policies.find(
            {"groups": group_id}
        ).to_list(None)
        
        policy_ids = [p.get("policy_id", "") for p in policies]
        
        groups.append({
            "group_id": group_id,
            "name": group_id,
            "description": f"Group with {group_data['user_count']} members",
            "user_count": group_data["user_count"],
            "policies": policy_ids,
            "created_at": datetime.utcnow().isoformat()
        })
    
    return groups


@router.get("/groups/{group_id}")
async def get_group(
    group_id: str,
    current_client: dict = Depends(get_api_key_client)
):
    """Get a specific group with its members."""
    if current_client.get("metadata", {}).get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    db = Database.get_db()
    
    # Get users in this group
    users_cursor = db.users.find({"groups": group_id})
    members = []
    
    async for user in users_cursor:
        members.append({
            "user_id": user.get("user_id"),
            "name": user.get("name"),
            "email": user.get("email")
        })
    
    if not members:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Group not found"
        )
    
    # Get policies
    policies = await db.policies.find({"groups": group_id}).to_list(None)
    policy_ids = [p.get("policy_id", "") for p in policies]
    
    return {
        "group_id": group_id,
        "name": group_id,
        "description": f"Group with {len(members)} members",
        "user_count": len(members),
        "members": members,
        "policies": policy_ids,
        "created_at": datetime.utcnow().isoformat()
    }


@router.post("/users/import-csv")
async def import_users_csv(
    file: UploadFile = File(...),
    current_client: dict = Depends(get_api_key_client)
):
    """Import users from CSV file."""
    if current_client.get("metadata", {}).get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    # Validate file type
    if not file.filename.endswith('.csv'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File must be a CSV"
        )
    
    try:
        # Read file content
        contents = await file.read()
        decoded = contents.decode('utf-8')
        csv_reader = csv.DictReader(io.StringIO(decoded))
        
        # Validate headers
        if not csv_reader.fieldnames or 'email' not in csv_reader.fieldnames or 'name' not in csv_reader.fieldnames:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="CSV must contain 'email' and 'name' columns"
            )
        
        db = Database.get_db()
        users_created = 0
        users_updated = 0
        groups_created = set()
        errors = []
        
        for row_num, row in enumerate(csv_reader, start=2):  # start=2 because row 1 is header
            try:
                # Extract user data
                email = row.get('email', '').strip()
                name = row.get('name', '').strip()
                
                if not email or not name:
                    errors.append(f"Row {row_num}: Missing email or name")
                    continue
                
                # Generate user_id from email
                user_id = email.split('@')[0].lower().replace('.', '_')
                
                # Parse groups (comma-separated)
                groups_str = row.get('groups', '').strip()
                groups = [g.strip() for g in groups_str.split(',') if g.strip()] if groups_str else []
                
                # Track new groups
                groups_created.update(groups)
                
                # Generate username from email if not provided
                username = row.get('username', email.split('@')[0]).strip()
                
                # Parse quotas
                try:
                    quota_per_day = int(row.get('quota_per_day', 500))
                except (ValueError, TypeError):
                    quota_per_day = 500
                
                try:
                    quota_per_month = int(row.get('quota_per_month', 15000))
                except (ValueError, TypeError):
                    quota_per_month = 15000
                
                # Build user document
                user_doc = {
                    "user_id": user_id,
                    "username": username,
                    "email": email,
                    "name": name,
                    "department": row.get('department', '').strip() or None,
                    "title": row.get('title', '').strip() or None,
                    "groups": groups,
                    "is_active": row.get('is_active', 'true').lower() == 'true',
                    "quota_per_day": quota_per_day,
                    "quota_per_month": quota_per_month,
                    "updated_at": datetime.utcnow()
                }
                
                # Check if user exists
                existing_user = await db.users.find_one({"email": email})
                
                if existing_user:
                    # Update existing user
                    await db.users.update_one(
                        {"email": email},
                        {"$set": user_doc}
                    )
                    users_updated += 1
                else:
                    # Create new user
                    user_doc["created_at"] = datetime.utcnow()
                    await db.users.insert_one(user_doc)
                    users_created += 1
                
                # Log audit event
                await db.audit_logs.insert_one({
                    "audit_id": f"audit-{datetime.utcnow().timestamp()}",
                    "timestamp": datetime.utcnow(),
                    "client_id": current_client.get("client_id"),
                    "action": "user_imported" if not existing_user else "user_updated",
                    "resource_type": "user",
                    "resource_id": user_id,
                    "details": {
                        "email": email,
                        "source": "csv_import",
                        "filename": file.filename
                    }
                })
                
            except Exception as e:
                errors.append(f"Row {row_num}: {str(e)}")
                logger.error(f"Error importing row {row_num}: {e}")
        
        # Update settings with sync status
        await db.system_settings.update_one(
            {"_id": "system"},
            {
                "$set": {
                    "user_sync.sources.$[elem].last_sync": datetime.utcnow().isoformat(),
                    "user_sync.sources.$[elem].last_sync_status": "success" if not errors else "failed",
                    "user_sync.sources.$[elem].users_synced": users_created + users_updated,
                    "user_sync.sources.$[elem].groups_synced": len(groups_created)
                }
            },
            array_filters=[{"elem.type": "csv"}],
            upsert=False
        )
        
        return {
            "status": "success" if not errors else "partial",
            "users_created": users_created,
            "users_updated": users_updated,
            "groups_found": len(groups_created),
            "groups": list(groups_created),
            "errors": errors,
            "message": f"Imported {users_created + users_updated} users ({users_created} new, {users_updated} updated)"
        }
        
    except UnicodeDecodeError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File encoding error. Please ensure CSV is UTF-8 encoded"
        )
    except Exception as e:
        logger.error(f"CSV import error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Import failed: {str(e)}"
        )
