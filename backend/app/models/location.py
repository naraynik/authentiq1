import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.database.database import Base

class LocationHistory(Base):
    __tablename__ = "location_history"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(String, ForeignKey("products.product_id"), index=True, nullable=False)
    location_name = Column(String, nullable=False)
    details = Column(String, nullable=True)
    updated_by = Column(String, nullable=False)
    transaction_hash = Column(String, nullable=True)
    timestamp = Column(DateTime(timezone=True), default=datetime.datetime.utcnow, nullable=False)

    # Relationships
    product = relationship("Product", back_populates="locations")
