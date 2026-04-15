"""Mutual TLS (mTLS) authentication middleware."""

from typing import Optional, Dict, Any
from datetime import datetime
from fastapi import Request, HTTPException, status
from cryptography import x509
from cryptography.hazmat.backends import default_backend
from cryptography.x509.oid import NameOID, ExtensionOID
import ssl
from loguru import logger

from src.core.config import settings
from src.core.database import Database
from src.models.database import Client


async def verify_client_certificate(request: Request) -> Optional[Dict[str, Any]]:
    """
    Verify client certificate from mTLS connection.
    
    This middleware extracts and validates the client certificate
    from the TLS connection, then looks up the associated client
    in the database.
    
    Args:
        request: FastAPI request object
        
    Returns:
        Client document if certificate is valid, None otherwise
    """
    try:
        # Get client certificate from request
        # Note: This requires configuring uvicorn/nginx with SSL client verification
        cert_pem = request.headers.get("X-Client-Cert")
        
        if not cert_pem:
            # Check if cert is in request scope (from reverse proxy)
            if hasattr(request, "scope") and "client_cert" in request.scope:
                cert_pem = request.scope["client_cert"]
        
        if not cert_pem:
            logger.debug("No client certificate provided")
            return None
        
        # Parse certificate
        cert_bytes = cert_pem.encode() if isinstance(cert_pem, str) else cert_pem
        cert = x509.load_pem_x509_certificate(cert_bytes, default_backend())
        
        # Extract certificate details
        subject = cert.subject
        issuer = cert.issuer
        serial_number = cert.serial_number
        not_valid_before = cert.not_valid_before
        not_valid_after = cert.not_valid_after
        
        # Verify certificate is currently valid
        now = datetime.utcnow()
        if now < not_valid_before or now > not_valid_after:
            logger.warning(f"Client certificate expired or not yet valid: {serial_number}")
            return None
        
        # Extract Common Name (CN) from subject
        cn = None
        for attr in subject:
            if attr.oid == NameOID.COMMON_NAME:
                cn = attr.value
                break
        
        if not cn:
            logger.warning("Client certificate has no Common Name")
            return None
        
        # Look up client by certificate CN or serial number
        db = Database.get_database()
        client = await db.clients.find_one({
            "$or": [
                {"client_cert_cn": cn},
                {"client_cert_serial": str(serial_number)}
            ],
            "is_active": True,
            "client_type": "mtls"
        })
        
        if not client:
            logger.warning(f"No client found for certificate CN: {cn}")
            return None
        
        # Verify certificate fingerprint if stored
        if "client_cert_fingerprint" in client:
            import hashlib
            cert_fingerprint = hashlib.sha256(cert.public_bytes(
                encoding=x509.Encoding.DER
            )).hexdigest()
            
            if cert_fingerprint != client["client_cert_fingerprint"]:
                logger.warning(f"Certificate fingerprint mismatch for client: {client['client_id']}")
                return None
        
        # Update last_used timestamp
        await db.clients.update_one(
            {"_id": client["_id"]},
            {"$set": {"last_used": datetime.utcnow()}}
        )
        
        logger.info(f"Client authenticated via mTLS: {client['client_id']} (CN: {cn})")
        return client
        
    except Exception as e:
        logger.error(f"Error verifying client certificate: {e}")
        return None


async def get_mtls_client(request: Request) -> Dict[str, Any]:
    """
    FastAPI dependency for mTLS authentication.
    
    Verifies the client certificate and returns the client document.
    
    Args:
        request: FastAPI request
        
    Returns:
        Client document
        
    Raises:
        HTTPException: If certificate is invalid or missing
    """
    client = await verify_client_certificate(request)
    
    if not client:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing client certificate",
            headers={"WWW-Authenticate": "Certificate"}
        )
    
    return client


def extract_cert_info(cert_pem: str) -> Dict[str, Any]:
    """
    Extract information from a PEM-encoded certificate.
    
    Useful for registering new mTLS clients.
    
    Args:
        cert_pem: PEM-encoded certificate
        
    Returns:
        Dictionary with certificate details
    """
    try:
        cert_bytes = cert_pem.encode() if isinstance(cert_pem, str) else cert_pem
        cert = x509.load_pem_x509_certificate(cert_bytes, default_backend())
        
        # Extract subject details
        subject = cert.subject
        cn = None
        org = None
        
        for attr in subject:
            if attr.oid == NameOID.COMMON_NAME:
                cn = attr.value
            elif attr.oid == NameOID.ORGANIZATION_NAME:
                org = attr.value
        
        # Calculate fingerprint
        import hashlib
        fingerprint = hashlib.sha256(cert.public_bytes(
            encoding=x509.Encoding.DER
        )).hexdigest()
        
        return {
            "common_name": cn,
            "organization": org,
            "serial_number": str(cert.serial_number),
            "fingerprint": fingerprint,
            "not_valid_before": cert.not_valid_before.isoformat(),
            "not_valid_after": cert.not_valid_after.isoformat(),
            "issuer": cert.issuer.rfc4514_string(),
            "subject": cert.subject.rfc4514_string()
        }
    except Exception as e:
        logger.error(f"Error extracting certificate info: {e}")
        raise ValueError(f"Invalid certificate: {e}")
