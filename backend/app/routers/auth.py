import os
import uuid
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Form, File, UploadFile
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.database.database import get_db
from app.models.user import User
from app.models.manufacturer import Manufacturer
from app.core.config import settings
from app.core.security import (
    hash_password,
    verify_password,
    create_access_token,
    validate_email,
    validate_gstin,
    validate_password_strength
)
from app.core.deps import get_current_user

router = APIRouter(prefix="/auth", tags=["Authentication"])

class LoginRequest(BaseModel):
    email: str
    password: str

@router.post("/manufacturer/register", status_code=status.HTTP_201_CREATED)
async def register_manufacturer(
    company_name: str = Form(...),
    gstin: Optional[str] = Form(None),
    GSTIN: Optional[str] = Form(None),
    company_address: str = Form(...),
    phone: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    verification_document: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    Register a new Manufacturer account.
    Initial verification status will be set to PENDING.
    Verification document is saved in a non-public storage directory.
    """
    raw_gstin = gstin or GSTIN
    if not raw_gstin:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="GSTIN field is required"
        )

    clean_email = email.strip().lower()
    clean_gstin = raw_gstin.strip().upper()
    clean_company_name = company_name.strip()
    clean_company_address = company_address.strip()
    clean_phone = phone.strip()

    # 1. Email format validation
    if not validate_email(clean_email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid email format"
        )

    # 2. Password strength validation
    if not validate_password_strength(password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password does not meet strength requirements (minimum 8 characters, at least 1 uppercase letter, 1 lowercase letter, 1 digit, and 1 special character)"
        )

    # 3. GSTIN format validation
    if not validate_gstin(clean_gstin):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid GSTIN format. Must be 15 alphanumeric characters (e.g. 27AAACA1234A1Z5)"
        )

    # 4. Check Unique Email
    existing_user = db.query(User).filter(User.email == clean_email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email address is already registered"
        )

    # 5. Check Unique GSTIN
    existing_gstin = db.query(Manufacturer).filter(Manufacturer.gstin == clean_gstin).first()
    if existing_gstin:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="GSTIN is already registered"
        )

    # 6. Validate Document Type
    ext = os.path.splitext(verification_document.filename)[1].lower()
    if ext not in settings.ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Allowed document types: {', '.join(settings.ALLOWED_EXTENSIONS)}"
        )

    # 7. Validate Document Size
    doc_contents = await verification_document.read()
    if len(doc_contents) > settings.MAX_UPLOAD_SIZE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Document file size exceeds maximum limit of {settings.MAX_UPLOAD_SIZE // (1024 * 1024)}MB"
        )

    # Save verification document file in secure private directory
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    filename = f"mfr_{uuid.uuid4().hex}{ext}"
    doc_path = os.path.join(settings.UPLOAD_DIR, filename)
    with open(doc_path, "wb") as f:
        f.write(doc_contents)

    # Create User
    user = User(
        email=clean_email,
        password_hash=hash_password(password),
        role="MANUFACTURER",
        is_active=True
    )
    db.add(user)
    db.flush()

    # Create Manufacturer
    manufacturer = Manufacturer(
        user_id=user.id,
        company_name=clean_company_name,
        gstin=clean_gstin,
        company_address=clean_company_address,
        phone=clean_phone,
        verification_document_path=doc_path,
        verification_document=doc_contents,
        verification_document_type={".pdf": "application/pdf", ".png": "image/png",
                                    ".jpg": "image/jpeg", ".jpeg": "image/jpeg"}.get(ext),
        verification_status="PENDING"
    )
    db.add(manufacturer)
    db.flush()
    from app.services.audit import create_audit_log
    create_audit_log(
        db=db, action="MANUFACTURER_REGISTERED", entity_type="MANUFACTURER", entity_id=str(manufacturer.id),
        user_id=user.id,
        description=f"'{clean_company_name}' (GSTIN {clean_gstin}) registered and is waiting for verification.",
    )
    db.commit()
    db.refresh(manufacturer)

    return {
        "message": "Manufacturer registered successfully. Pending admin approval.",
        "manufacturer_id": manufacturer.id,
        "user_id": user.id,
        "email": user.email,
        "company_name": manufacturer.company_name,
        "gstin": manufacturer.gstin,
        "verification_status": manufacturer.verification_status
    }

@router.post("/login")
async def login(
    payload: LoginRequest,
    db: Session = Depends(get_db)
):
    """
    Unified Login endpoint for Admin and Manufacturer users.
    Returns JWT Access Token and basic user info.
    """
    clean_email = payload.email.strip().lower()
    user = db.query(User).filter(User.email == clean_email).first()

    # Generic invalid-login error for security
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Inactive users cannot login
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Build claims
    access_token = create_access_token(
        subject=str(user.id),
        extra_claims={
            "user_id": user.id,
            "email": user.email,
            "role": user.role
        }
    )

    user_info = {
        "id": user.id,
        "email": user.email,
        "role": user.role,
        "is_active": user.is_active
    }
    if user.manufacturer:
        user_info["company_name"] = user.manufacturer.company_name
        user_info["verification_status"] = user.manufacturer.verification_status

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "role": user.role,
        "user": user_info
    }

@router.get("/me")
async def get_me(current_user: User = Depends(get_current_user)):
    """
    Get profile details of the currently authenticated user.
    """
    profile = {
        "id": current_user.id,
        "email": current_user.email,
        "role": current_user.role,
        "is_active": current_user.is_active
    }
    if current_user.manufacturer:
        profile["manufacturer"] = {
            "id": current_user.manufacturer.id,
            "company_name": current_user.manufacturer.company_name,
            "gstin": current_user.manufacturer.gstin,
            "company_address": current_user.manufacturer.company_address,
            "phone": current_user.manufacturer.phone,
            "verification_status": current_user.manufacturer.verification_status
        }
    return profile
