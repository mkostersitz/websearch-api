"""
Enhanced Audit Logging Utility
Provides comprehensive audit logging with trace information, user context, and detailed metadata.
"""

from datetime import datetime, timezone
from typing import Dict, Optional, List, Any
from opentelemetry import trace

from loguru import logger


async def log_audit_event(
    db,
    client_id: str,
    action: str,
    resource_type: str,
    resource_id: str,
    details: Optional[Dict[str, Any]] = None,
    user_id: Optional[str] = None,
    user_email: Optional[str] = None,
    user_name: Optional[str] = None,
    request_info: Optional[Dict[str, Any]] = None,
    response_info: Optional[Dict[str, Any]] = None,
    policies_applied: Optional[List[Dict[str, Any]]] = None,
    quotas: Optional[Dict[str, Any]] = None,
    filtering_info: Optional[Dict[str, Any]] = None
):
    """
    Log an audit event with comprehensive details.
    
    Args:
        db: Database instance
        client_id: Client ID performing the action
        action: Action being performed (e.g., "search", "api_key_generated")
        resource_type: Type of resource (e.g., "search", "api_key", "policy")
        resource_id: ID of the resource
        details: Additional details about the action
        user_id: Optional user ID
        user_email: Optional user email
        user_name: Optional user name
        request_info: Request details (method, path, query, ip, user_agent)
        response_info: Response details (status_code, provider, results_count, response_time_ms)
        policies_applied: List of applied policies with details
        quotas: Quota usage information
        filtering_info: Result filtering information
    """
    # Get current trace context
    tracer = trace.get_tracer(__name__)
    current_span = trace.get_current_span()
    trace_id = None
    span_id = None
    
    if current_span and current_span.get_span_context().is_valid:
        span_context = current_span.get_span_context()
        trace_id = format(span_context.trace_id, '032x')
        span_id = format(span_context.span_id, '016x')
    
    # Build audit log document
    audit_doc = {
        "audit_id": f"audit-{datetime.now(timezone.utc).timestamp()}",
        "timestamp": datetime.now(timezone.utc),
        
        # User context
        "client_id": client_id,
        "user_id": user_id,
        "user_email": user_email,
        "user_name": user_name,
        
        # Action details
        "action": action,
        "resource_type": resource_type,
        "resource_id": resource_id,
        "details": details or {},
    }
    
    # Add trace information
    if trace_id:
        audit_doc["trace"] = {
            "trace_id": trace_id,
            "span_id": span_id,
            "parent_span_id": None  # Could be extracted if needed
        }
    
    # Add request information
    if request_info:
        audit_doc["request"] = request_info
    
    # Add response information
    if response_info:
        audit_doc["response"] = response_info
    
    # Add policy information
    if policies_applied:
        audit_doc["policies_applied"] = [p.get("policy_id") if isinstance(p, dict) else str(p) for p in policies_applied]
        audit_doc["policies_details"] = policies_applied
    
    # Add quota information
    if quotas:
        audit_doc["quotas"] = quotas
    
    # Add filtering information
    if filtering_info:
        audit_doc["filtering"] = filtering_info
    
    # Insert into database
    try:
        await db.audit_logs.insert_one(audit_doc)
        logger.debug(f"Audit log created: {action} by {client_id} on {resource_type}/{resource_id}")
    except Exception as e:
        logger.error(f"Failed to create audit log: {e}")
        # Don't fail the main operation if audit logging fails


async def get_user_context_from_client(db, client: dict) -> Dict[str, Optional[str]]:
    """
    Extract user context from a client record.
    
    Args:
        db: Database instance
        client: Client record
        
    Returns:
        Dict with user_id, user_email, user_name
    """
    user_id = client.get("owner_id")
    user_email = client.get("metadata", {}).get("email")
    user_name = client.get("client_name")
    
    # If we have a user_id but missing name/email, fetch from users collection
    if user_id and (not user_email or not user_name):
        user = await db.users.find_one({"user_id": user_id})
        if user:
            user_email = user_email or user.get("email")
            user_name = user_name or user.get("name") or user.get("username")
    
    return {
        "user_id": user_id,
        "user_email": user_email,
        "user_name": user_name
    }
