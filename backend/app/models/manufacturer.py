import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, LargeBinary
from sqlalchemy.orm import relationship, deferred
from app.database.database import Base

class Manufacturer(Base):
    __tablename__ = "manufacturers"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    company_name = Column(String, nullable=False)
    gstin = Column(String, unique=True, index=True, nullable=False)
    company_address = Column(String, nullable=False)
    phone = Column(String, nullable=False)
    verification_document_path = Column(String, nullable=False)
    # The uploaded file itself, so it survives hosts with temporary disks (e.g. Render).
    # deferred: only loaded when the admin opens the document.
    verification_document = deferred(Column(LargeBinary, nullable=True))
    verification_document_type = Column(String, nullable=True)
    verification_status = Column(String, default="PENDING", nullable=False)  # PENDING, APPROVED, REJECTED, SUSPENDED
    verified_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    verified_at = Column(DateTime(timezone=True), nullable=True)
    rejection_reason = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=datetime.datetime.utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow, nullable=False)

    # Relationships
    user = relationship("User", foreign_keys=[user_id], back_populates="manufacturer")
    verifier = relationship("User", foreign_keys=[verified_by])
    products = relationship("Product", back_populates="manufacturer", cascade="all, delete-orphan")
