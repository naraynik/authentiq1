import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from app.database.database import Base

class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(String, unique=True, index=True, nullable=False)
    manufacturer_id = Column(Integer, ForeignKey("manufacturers.id"), nullable=False)
    manufacturer_name = Column(String, nullable=False)
    product_name = Column(String, nullable=False)
    batch_number = Column(String, nullable=False)
    manufacturing_date = Column(DateTime(timezone=True), nullable=False)
    expiry_date = Column(DateTime(timezone=True), nullable=True)
    product_hash = Column(String, nullable=False)
    current_location = Column(String, nullable=False)
    next_location = Column(String, nullable=False)
    status = Column(String, default="GENUINE", nullable=False)  # GENUINE, SUSPICIOUS, RECALLED
    is_onchain = Column(Boolean, default=False, nullable=False)
    registration_tx_hash = Column(String, nullable=True)
    # Added for the AuthentiQ web frontend (see CHANGES.md)
    sku = Column(String, nullable=True)
    facility = Column(JSON, nullable=True)  # {"street","city","country","lat","lon"}
    distributors = Column(JSON, nullable=True)  # [{"name","street","city","country","lat","lon"}]
    registration_block = Column(Integer, nullable=True)
    created_at = Column(DateTime(timezone=True), default=datetime.datetime.utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow, nullable=False)

    # Relationships
    manufacturer = relationship("Manufacturer", back_populates="products")
    scans = relationship("ScanHistory", back_populates="product", cascade="all, delete-orphan")
    locations = relationship("LocationHistory", back_populates="product", cascade="all, delete-orphan")
