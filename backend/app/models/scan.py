import datetime
from sqlalchemy import Column, Integer, String, Float, Text, DateTime, JSON, ForeignKey
from sqlalchemy.orm import relationship
from app.database.database import Base

class ScanHistory(Base):
    __tablename__ = "scan_history"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(String, ForeignKey("products.product_id"), index=True, nullable=False)
    scanned_at = Column(DateTime(timezone=True), default=datetime.datetime.utcnow, index=True, nullable=False)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    location = Column(String, nullable=False)
    device_id = Column(String, nullable=True)
    ip_address = Column(String, nullable=True)
    user_agent = Column(String, nullable=True)
    scan_velocity = Column(Integer, default=1, nullable=False)
    hours_since_creation = Column(Float, default=0.0, nullable=False)
    authenticity_probability = Column(Float, default=0.0, nullable=False)
    anomaly_score = Column(Float, default=0.0, nullable=False)
    ai_verdict = Column(String, nullable=True)
    blockchain_verdict = Column(String, nullable=True)
    final_verdict = Column(String, nullable=False)
    flags = Column(Text, nullable=True)
    raw_scan_data = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), default=datetime.datetime.utcnow, nullable=False)

    # Relationships
    product = relationship("Product", back_populates="scans")
