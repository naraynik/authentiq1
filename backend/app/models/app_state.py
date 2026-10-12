import datetime
from sqlalchemy import Column, String, Text, DateTime
from app.database.database import Base


class AppState(Base):
    """Small key/value store for settings the app discovers itself (e.g. deployed contract address)."""

    __tablename__ = "app_state"

    key = Column(String, primary_key=True)
    value = Column(Text, nullable=True)
    updated_at = Column(DateTime(timezone=True), default=datetime.datetime.utcnow,
                        onupdate=datetime.datetime.utcnow, nullable=False)
