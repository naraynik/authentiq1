import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, Float
from app.database.database import Base


class Issue(Base):
    """A problem a customer reported from a scan report (public, no account needed)."""

    __tablename__ = "issues"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(String, index=True, nullable=False)
    message = Column(Text, nullable=False)
    contact = Column(String, nullable=True)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    status = Column(String, default="OPEN", nullable=False)  # OPEN, REVIEWED, CLOSED
    created_at = Column(DateTime(timezone=True), default=datetime.datetime.utcnow, nullable=False)
