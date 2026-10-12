from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database.database import get_db
from app.models.user import User
from app.core.deps import require_manufacturer, get_current_manufacturer_user

router = APIRouter(prefix="/manufacturer", tags=["Manufacturer Profile"])

@router.get("/profile")
async def get_own_manufacturer_profile(
    current_user: User = Depends(get_current_manufacturer_user)
):
    """
    Get company/profile information for the currently authenticated manufacturer.
    Strict IDOR protection: Manufacturer can view ONLY their own profile.
    Password hashes and sensitive secrets are never exposed.
    """
    mfr = current_user.manufacturer
    return {
        "id": mfr.id,
        "user_id": current_user.id,
        "email": current_user.email,
        "company_name": mfr.company_name,
        "gstin": mfr.gstin,
        "company_address": mfr.company_address,
        "phone": mfr.phone,
        "verification_status": mfr.verification_status,
        "rejection_reason": mfr.rejection_reason,
        "verified_at": mfr.verified_at,
        "created_at": mfr.created_at,
        "updated_at": mfr.updated_at
    }

@router.get("/me")
async def get_manufacturer_profile_legacy(
    current_user: User = Depends(get_current_manufacturer_user)
):
    """Legacy alias endpoint for retrieving authenticated manufacturer profile."""
    return await get_own_manufacturer_profile(current_user=current_user)

@router.get("/test")
async def manufacturer_test(
    current_user: User = Depends(require_manufacturer)
):
    """Development/testing endpoint for Approved Manufacturer role."""
    mfr = current_user.manufacturer
    return {
        "message": "Manufacturer test endpoint reached successfully",
        "role": current_user.role,
        "user": {
            "id": current_user.id,
            "email": current_user.email,
            "company_name": mfr.company_name,
            "verification_status": mfr.verification_status
        }
    }
