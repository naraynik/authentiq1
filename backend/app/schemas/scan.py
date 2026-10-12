import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel

class ScanBase(BaseModel):
    product_id: str
    location: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    device_id: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None

class ScanCreate(ScanBase):
    scan_velocity: int = 1
    hours_since_creation: float = 0.0
    raw_scan_data: Optional[Dict[str, Any]] = None

class ScanResponse(ScanBase):
    id: int
    scanned_at: datetime.datetime
    scan_velocity: int
    hours_since_creation: float
    authenticity_probability: float
    anomaly_score: float
    ai_verdict: Optional[str] = None
    blockchain_verdict: Optional[str] = None
    final_verdict: str
    flags: Optional[str] = None
    created_at: datetime.datetime

    class Config:
        from_attributes = True
