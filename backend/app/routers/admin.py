import os
from datetime import datetime
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, status, Request, Query
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from sqlalchemy import func
from pydantic import BaseModel

from app.database.database import get_db
from app.models.user import User
from app.models.manufacturer import Manufacturer
from app.core.config import settings
from app.core.deps import require_admin
from app.services.audit import create_audit_log

router = APIRouter(prefix="/admin", tags=["Admin Governance"])

class StatusUpdatePayload(BaseModel):
    status: str  # APPROVED, REJECTED, SUSPENDED, PENDING
    rejection_reason: Optional[str] = None

@router.get("/me")
async def get_admin_profile(current_user: User = Depends(require_admin)):
    """Get profile of currently authenticated Admin."""
    return {
        "id": current_user.id,
        "email": current_user.email,
        "role": current_user.role,
        "is_active": current_user.is_active
    }

@router.get("/test")
async def admin_test(current_user: User = Depends(require_admin)):
    """Development/testing endpoint for Admin role."""
    return {
        "message": "Admin test endpoint reached successfully",
        "role": current_user.role,
        "user": {
            "id": current_user.id,
            "email": current_user.email
        }
    }

@router.get("/audit-logs")
async def list_audit_logs(
    limit: int = Query(50, ge=1, le=500),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """
    List platform administrative and security audit logs (Admin only).
    """
    from app.models.audit import AuditLog
    logs = db.query(AuditLog).order_by(AuditLog.created_at.desc()).limit(limit).all()
    user_ids = {log.user_id for log in logs if log.user_id}
    emails = dict(db.query(User.id, User.email).filter(User.id.in_(user_ids)).all()) if user_ids else {}
    results = []
    for log in logs:
        results.append({
            "id": log.id,
            "user_id": log.user_id,
            "user_email": emails.get(log.user_id),
            "action": log.action,
            "entity_type": log.entity_type,
            "entity_id": log.entity_id,
            "description": log.description,
            "ip_address": log.ip_address,
            "created_at": log.created_at
        })
    return results

@router.get("/manufacturers")
async def list_manufacturers(
    status: Optional[str] = Query(None, description="Filter by status: PENDING, APPROVED, REJECTED, SUSPENDED"),
    company_name: Optional[str] = Query(None, description="Filter by company name (partial match)"),
    gstin: Optional[str] = Query(None, description="Filter by GSTIN (partial match)"),
    email: Optional[str] = Query(None, description="Filter by email (partial match)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """
    List registered manufacturers with support for status, company_name, GSTIN, and email filtering (Admin only).
    """
    query = db.query(Manufacturer).join(User, Manufacturer.user_id == User.id)

    if status:
        query = query.filter(func.upper(Manufacturer.verification_status) == status.strip().upper())
    if company_name:
        query = query.filter(func.lower(Manufacturer.company_name).contains(company_name.strip().lower()))
    if gstin:
        query = query.filter(func.lower(Manufacturer.gstin).contains(gstin.strip().lower()))
    if email:
        query = query.filter(func.lower(User.email).contains(email.strip().lower()))

    manufacturers = query.all()

    results = []
    for mfr in manufacturers:
        results.append({
            "id": mfr.id,
            "user_id": mfr.user_id,
            "email": mfr.user.email if mfr.user else None,
            "company_name": mfr.company_name,
            "gstin": mfr.gstin,
            "company_address": mfr.company_address,
            "phone": mfr.phone,
            "verification_status": mfr.verification_status,
            "verification_document_path": mfr.verification_document_path,
            "verified_by": mfr.verified_by,
            "verified_at": mfr.verified_at,
            "rejection_reason": mfr.rejection_reason,
            "created_at": mfr.created_at,
            "updated_at": mfr.updated_at
        })
    return results

@router.get("/manufacturers/{manufacturer_id}")
async def get_manufacturer_details(
    manufacturer_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """
    Retrieve complete manufacturer details for Admin review (Admin only).
    """
    mfr = db.query(Manufacturer).filter(Manufacturer.id == manufacturer_id).first()
    if not mfr:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Manufacturer not found"
        )

    return {
        "id": mfr.id,
        "user_id": mfr.user_id,
        "email": mfr.user.email if mfr.user else None,
        "company_name": mfr.company_name,
        "gstin": mfr.gstin,
        "company_address": mfr.company_address,
        "phone": mfr.phone,
        "verification_status": mfr.verification_status,
        "verification_document_path": mfr.verification_document_path,
        "verified_by": mfr.verified_by,
        "verified_at": mfr.verified_at,
        "rejection_reason": mfr.rejection_reason,
        "created_at": mfr.created_at,
        "updated_at": mfr.updated_at
    }

@router.get("/manufacturers/{manufacturer_id}/document")
async def view_manufacturer_document(
    manufacturer_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """
    Secure Admin-only endpoint to view/download a manufacturer's uploaded verification document.
    Prevents path traversal attacks and unauthorized public file access.
    """
    mfr = db.query(Manufacturer).filter(Manufacturer.id == manufacturer_id).first()
    if not mfr:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Manufacturer not found"
        )

    if mfr.verification_document:
        from fastapi.responses import Response
        return Response(
            content=mfr.verification_document,
            media_type=mfr.verification_document_type or "application/octet-stream",
            headers={"Content-Disposition": f'inline; filename="aadhaar-{mfr.gstin}"',
                     "Cache-Control": "no-store"},
        )

    doc_path = mfr.verification_document_path
    if not doc_path or not os.path.exists(doc_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Verification document file not found"
        )

    # Path traversal protection check
    canonical_doc_path = os.path.realpath(doc_path)
    canonical_upload_dir = os.path.realpath(settings.UPLOAD_DIR)
    if not canonical_doc_path.startswith(canonical_upload_dir):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden file path access"
        )

    # Determine media type
    ext = os.path.splitext(doc_path)[1].lower()
    media_type_map = {
        ".pdf": "application/pdf",
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg"
    }
    media_type = media_type_map.get(ext, "application/octet-stream")

    return FileResponse(
        path=canonical_doc_path,
        filename=os.path.basename(canonical_doc_path),
        media_type=media_type
    )

@router.put("/manufacturers/{manufacturer_id}/status")
async def update_manufacturer_status(
    manufacturer_id: int,
    payload: StatusUpdatePayload,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """
    Approve, Reject, or Suspend a Manufacturer (Admin only).
    Validates state transitions and records audit logs.
    """
    mfr = db.query(Manufacturer).filter(Manufacturer.id == manufacturer_id).first()
    if not mfr:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Manufacturer not found"
        )

    new_status = payload.status.upper()
    if new_status not in ["APPROVED", "REJECTED", "SUSPENDED", "PENDING"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid status. Allowed values: APPROVED, REJECTED, SUSPENDED, PENDING"
        )

    # Validate transition: setting same status
    if mfr.verification_status == new_status:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Manufacturer status is already {new_status}"
        )

    # Rejection reason validation
    if new_status == "REJECTED" and not payload.rejection_reason:
        payload.rejection_reason = "Verification document or compliance check failed"

    # State update
    old_status = mfr.verification_status
    mfr.verification_status = new_status
    mfr.verified_by = current_user.id
    mfr.verified_at = datetime.utcnow()
    if payload.rejection_reason:
        mfr.rejection_reason = payload.rejection_reason
    elif new_status == "APPROVED":
        mfr.rejection_reason = None  # clear an old rejection reason on approval

    # Audit Logging
    action_name = f"MANUFACTURER_{new_status}"
    audit_desc = (
        f"Manufacturer status changed from {old_status} to {new_status} "
        f"by Admin '{current_user.email}'."
    )
    if payload.rejection_reason:
        audit_desc += f" Reason: {payload.rejection_reason}"

    create_audit_log(
        db=db,
        action=action_name,
        entity_type="MANUFACTURER",
        entity_id=str(mfr.id),
        user_id=current_user.id,
        description=audit_desc,
        request=request
    )

    db.commit()
    db.refresh(mfr)

    return {
        "message": f"Manufacturer status updated from {old_status} to {new_status}",
        "manufacturer_id": mfr.id,
        "company_name": mfr.company_name,
        "previous_status": old_status,
        "verification_status": mfr.verification_status,
        "verified_by": current_user.id,
        "verified_at": mfr.verified_at,
        "rejection_reason": mfr.rejection_reason
    }
