import datetime
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime
from app.database import Base

class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(String, unique=True, index=True, nullable=False)
    name = Column(String, nullable=False)
    batch_number = Column(String, nullable=False)
    production_location = Column(String, nullable=False)
    registered_at = Column(DateTime, default=datetime.datetime.utcnow)

class ScanHistory(Base):
    __tablename__ = "scan_history"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(String, index=True, nullable=False)
    location = Column(String, nullable=False)
    scan_velocity = Column(Integer, nullable=False)
    hours_since_creation = Column(Float, nullable=False)
    authenticity_probability = Column(Float, nullable=False)
    is_authentic = Column(Boolean, nullable=False)
    flags = Column(String, nullable=True) # Comma-separated list of flags
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
