import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel

class HealthCheckDatabase(BaseModel):
    connected: bool
    dialect: str
    url: Optional[str] = None

class HealthCheckResponse(BaseModel):
    status: str
    version: str
    database: HealthCheckDatabase
    timestamp: str

class VerificationRequest(BaseModel):
    product_id: str
    location: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    device_id: Optional[str] = None
    raw_optical_data: Optional[Dict[str, Any]] = None

class VerificationResponse(BaseModel):
    product_id: str
    final_verdict: str  # GENUINE, SUSPICIOUS, COUNTERFEIT, UNREGISTERED
    authenticity_probability: float
    anomaly_score: float
    flags: List[str]
    blockchain_registered: bool
    scan_recorded_at: datetime.datetime
