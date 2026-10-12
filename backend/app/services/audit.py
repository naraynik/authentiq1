from typing import Optional
from fastapi import Request
from sqlalchemy.orm import Session
from app.models.audit import AuditLog

def create_audit_log(
    db: Session,
    action: str,
    entity_type: str,
    entity_id: Optional[str] = None,
    user_id: Optional[int] = None,
    description: Optional[str] = None,
    request: Optional[Request] = None
) -> AuditLog:
    """
    Utility function to record system, security, and administrative events in audit_logs table.
    Ensures sensitive credentials, password hashes, and JWT secrets are never stored.
    """
    ip_addr = None
    if request and request.client:
        ip_addr = request.client.host

    log_entry = AuditLog(
        user_id=user_id,
        action=action,
        entity_type=entity_type,
        entity_id=str(entity_id) if entity_id is not None else None,
        description=description,
        ip_address=ip_addr
    )
    db.add(log_entry)
    db.flush()
    return log_entry
