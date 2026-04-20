"""Policy management API routes."""

from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from loguru import logger

from src.middleware.api_key import get_api_key_client
from src.core.database import Database
from src.models.policy import (
    EnhancedPolicy,
    PolicyCreateRequest,
    PolicyUpdateRequest,
    PolicyScope,
    AccessSchedule,
    ParentalControlPolicy,
    QueryLimits,
    AdminPermissions,
    SearchPermissions,
)


router = APIRouter(prefix="/admin/policies", tags=["Policy Management"])


@router.get("")
async def list_policies(
    current_client: dict = Depends(get_api_key_client),
    scope: Optional[str] = Query(None),
    is_active: Optional[bool] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500)
):
    """List all policies."""
    if current_client.get("metadata", {}).get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    db = Database.get_db()
    
    # Build query filter
    query_filter = {}
    if scope:
        query_filter["scope"] = scope
    if is_active is not None:
        query_filter["is_active"] = is_active
    
    # Get policies
    policies_cursor = db.policies.find(query_filter).skip(skip).limit(limit).sort("priority", -1)
    policies = []
    
    async for policy in policies_cursor:
        if "_id" in policy:
            policy["_id"] = str(policy["_id"])
        policies.append(policy)
    
    return policies


@router.post("")
async def create_policy(
    policy_request: PolicyCreateRequest,
    current_client: dict = Depends(get_api_key_client)
):
    """Create a new policy."""
    if current_client.get("metadata", {}).get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    db = Database.get_db()
    
    # Generate policy ID
    policy_id = f"pol-{datetime.utcnow().timestamp()}"
    
    # Build policy document
    policy_doc = {
        "policy_id": policy_id,
        "policy_name": policy_request.policy_name,
        "description": policy_request.description,
        "scope": policy_request.scope.value,
        "target_user_ids": policy_request.target_user_ids,
        "target_group_ids": policy_request.target_group_ids,
        "access_schedule": (policy_request.access_schedule or AccessSchedule()).model_dump(),
        "parental_controls": (policy_request.parental_controls or ParentalControlPolicy()).model_dump(),
        "query_limits": (policy_request.query_limits or QueryLimits()).model_dump(),
        "admin_permissions": (policy_request.admin_permissions or AdminPermissions()).model_dump(),
        "search_permissions": (policy_request.search_permissions or SearchPermissions()).model_dump(),
        "is_active": True,
        "priority": policy_request.priority,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
        "created_by": current_client.get("client_id"),
        "metadata": {}
    }
    
    # Insert policy
    await db.policies.insert_one(policy_doc)
    
    # Log audit event
    await db.audit_logs.insert_one({
        "audit_id": f"audit-{datetime.utcnow().timestamp()}",
        "timestamp": datetime.utcnow(),
        "client_id": current_client.get("client_id"),
        "action": "policy_created",
        "resource_type": "policy",
        "resource_id": policy_id,
        "details": {
            "policy_name": policy_request.policy_name,
            "scope": policy_request.scope.value,
            "priority": policy_request.priority
        }
    })
    
    logger.info(f"Policy created: {policy_id} by {current_client.get('client_id')}")
    
    policy_doc.pop("_id", None)
    return policy_doc


@router.get("/{policy_id}")
async def get_policy(
    policy_id: str,
    current_client: dict = Depends(get_api_key_client)
):
    """Get a specific policy."""
    if current_client.get("metadata", {}).get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    db = Database.get_db()
    
    policy = await db.policies.find_one({"policy_id": policy_id})
    
    if not policy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Policy not found"
        )
    
    policy.pop("_id", None)
    return policy


@router.put("/{policy_id}")
async def update_policy(
    policy_id: str,
    policy_update: PolicyUpdateRequest,
    current_client: dict = Depends(get_api_key_client)
):
    """Update a policy."""
    if current_client.get("metadata", {}).get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    db = Database.get_db()
    
    # Check if policy exists
    existing_policy = await db.policies.find_one({"policy_id": policy_id})
    if not existing_policy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Policy not found"
        )
    
    # Build update document
    update_doc = {
        "updated_at": datetime.utcnow(),
        "updated_by": current_client.get("client_id")
    }
    
    # Update fields if provided
    if policy_update.policy_name is not None:
        update_doc["policy_name"] = policy_update.policy_name
    if policy_update.description is not None:
        update_doc["description"] = policy_update.description
    if policy_update.target_user_ids is not None:
        update_doc["target_user_ids"] = policy_update.target_user_ids
    if policy_update.target_group_ids is not None:
        update_doc["target_group_ids"] = policy_update.target_group_ids
    if policy_update.access_schedule is not None:
        update_doc["access_schedule"] = policy_update.access_schedule.model_dump()
    if policy_update.parental_controls is not None:
        update_doc["parental_controls"] = policy_update.parental_controls.model_dump()
    if policy_update.query_limits is not None:
        update_doc["query_limits"] = policy_update.query_limits.model_dump()
    if policy_update.admin_permissions is not None:
        update_doc["admin_permissions"] = policy_update.admin_permissions.model_dump()
    if policy_update.search_permissions is not None:
        update_doc["search_permissions"] = policy_update.search_permissions.model_dump()
    if policy_update.is_active is not None:
        update_doc["is_active"] = policy_update.is_active
    if policy_update.priority is not None:
        update_doc["priority"] = policy_update.priority
    
    # Update policy
    await db.policies.update_one(
        {"policy_id": policy_id},
        {"$set": update_doc}
    )
    
    # Log audit event
    await db.audit_logs.insert_one({
        "audit_id": f"audit-{datetime.utcnow().timestamp()}",
        "timestamp": datetime.utcnow(),
        "client_id": current_client.get("client_id"),
        "action": "policy_updated",
        "resource_type": "policy",
        "resource_id": policy_id,
        "details": {
            "updated_fields": list(update_doc.keys())
        }
    })
    
    # Get updated policy
    updated_policy = await db.policies.find_one({"policy_id": policy_id})
    updated_policy.pop("_id", None)
    
    logger.info(f"Policy updated: {policy_id} by {current_client.get('client_id')}")
    
    return updated_policy


@router.delete("/{policy_id}")
async def delete_policy(
    policy_id: str,
    current_client: dict = Depends(get_api_key_client)
):
    """Delete a policy."""
    if current_client.get("metadata", {}).get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    db = Database.get_db()
    
    # Check if policy exists
    policy = await db.policies.find_one({"policy_id": policy_id})
    if not policy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Policy not found"
        )
    
    # Delete policy
    await db.policies.delete_one({"policy_id": policy_id})
    
    # Log audit event
    await db.audit_logs.insert_one({
        "audit_id": f"audit-{datetime.utcnow().timestamp()}",
        "timestamp": datetime.utcnow(),
        "client_id": current_client.get("client_id"),
        "action": "policy_deleted",
        "resource_type": "policy",
        "resource_id": policy_id,
        "details": {
            "policy_name": policy.get("policy_name")
        }
    })
    
    logger.info(f"Policy deleted: {policy_id} by {current_client.get('client_id')}")
    
    return {"message": "Policy deleted successfully", "policy_id": policy_id}


@router.post("/{policy_id}/assign")
async def assign_policy(
    policy_id: str,
    user_ids: List[str] = Query(default=[]),
    group_ids: List[str] = Query(default=[]),
    current_client: dict = Depends(get_api_key_client)
):
    """Assign policy to users and/or groups."""
    if current_client.get("metadata", {}).get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    db = Database.get_db()
    
    # Check if policy exists
    policy = await db.policies.find_one({"policy_id": policy_id})
    if not policy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Policy not found"
        )
    
    # Add to existing assignments
    update_ops = {}
    if user_ids:
        update_ops["$addToSet"] = {"target_user_ids": {"$each": user_ids}}
    if group_ids:
        if "$addToSet" in update_ops:
            update_ops["$addToSet"]["target_group_ids"] = {"$each": group_ids}
        else:
            update_ops["$addToSet"] = {"target_group_ids": {"$each": group_ids}}
    
    if update_ops:
        await db.policies.update_one(
            {"policy_id": policy_id},
            update_ops
        )
    
    # Log audit event
    await db.audit_logs.insert_one({
        "audit_id": f"audit-{datetime.utcnow().timestamp()}",
        "timestamp": datetime.utcnow(),
        "client_id": current_client.get("client_id"),
        "action": "policy_assigned",
        "resource_type": "policy",
        "resource_id": policy_id,
        "details": {
            "user_ids": user_ids,
            "group_ids": group_ids
        }
    })
    
    return {"message": "Policy assigned successfully"}


@router.post("/{policy_id}/unassign")
async def unassign_policy(
    policy_id: str,
    user_ids: List[str] = Query(default=[]),
    group_ids: List[str] = Query(default=[]),
    current_client: dict = Depends(get_api_key_client)
):
    """Unassign policy from users and/or groups."""
    if current_client.get("metadata", {}).get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    db = Database.get_db()
    
    # Check if policy exists
    policy = await db.policies.find_one({"policy_id": policy_id})
    if not policy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Policy not found"
        )
    
    # Remove from assignments
    update_ops = {}
    if user_ids:
        update_ops["$pull"] = {"target_user_ids": {"$in": user_ids}}
    if group_ids:
        if "$pull" in update_ops:
            update_ops["$pull"]["target_group_ids"] = {"$in": group_ids}
        else:
            update_ops["$pull"] = {"target_group_ids": {"$in": group_ids}}
    
    if update_ops:
        await db.policies.update_one(
            {"policy_id": policy_id},
            update_ops
        )
    
    # Log audit event
    await db.audit_logs.insert_one({
        "audit_id": f"audit-{datetime.utcnow().timestamp()}",
        "timestamp": datetime.utcnow(),
        "client_id": current_client.get("client_id"),
        "action": "policy_unassigned",
        "resource_type": "policy",
        "resource_id": policy_id,
        "details": {
            "user_ids": user_ids,
            "group_ids": group_ids
        }
    })
    
    return {"message": "Policy unassigned successfully"}
