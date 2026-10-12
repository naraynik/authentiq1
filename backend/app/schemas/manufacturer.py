import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr

class ManufacturerBase(BaseModel):
    company_name: str
    gstin: str
    company_address: str
    phone: str

class ManufacturerCreate(ManufacturerBase):
    email: EmailStr
    password: str

class ManufacturerApproval(BaseModel):
    status: str  # APPROVED, REJECTED, SUSPENDED
    rejection_reason: Optional[str] = None

class ManufacturerResponse(ManufacturerBase):
    id: int
    user_id: int
    verification_document_path: str
    verification_status: str
    verified_by: Optional[int] = None
    verified_at: Optional[datetime.datetime] = None
    rejection_reason: Optional[str] = None
    created_at: datetime.datetime
    updated_at: datetime.datetime

    class Config:
        from_attributes = True
