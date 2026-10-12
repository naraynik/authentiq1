import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel

class ProductBase(BaseModel):
    product_id: str
    product_name: str
    batch_number: str
    manufacturing_date: datetime.datetime
    expiry_date: Optional[datetime.datetime] = None
    current_location: str
    next_location: str

class PlaceIn(BaseModel):
    """A distributor or facility address. lat/lon are optional but enable the distance check."""
    name: Optional[str] = None
    street: Optional[str] = None
    city: Optional[str] = None
    country: Optional[str] = None
    lat: Optional[float] = None
    lon: Optional[float] = None


class ProductCreate(BaseModel):
    """Register one product.

    The original fields still work exactly as before. The web frontend sends the
    extra structured fields (sku, facility, distributors) and may leave out
    product_id (generated), manufacturing_date (defaults to now) and
    current_location / next_location (derived from facility / first distributor).
    """
    product_id: Optional[str] = None
    product_name: str
    batch_number: str
    manufacturing_date: Optional[datetime.datetime] = None
    expiry_date: Optional[datetime.datetime] = None
    current_location: Optional[str] = None
    next_location: Optional[str] = None
    sku: Optional[str] = None
    facility: Optional[PlaceIn] = None
    distributors: List[PlaceIn] = []

class ProductBatchCreate(BaseModel):
    product_ids: List[str]
    product_name: str
    batch_number: str
    manufacturing_date: datetime.datetime
    expiry_date: Optional[datetime.datetime] = None
    current_location: str
    next_location: str

class ProductUpdate(BaseModel):
    next_location: Optional[str] = None
    status: Optional[str] = None

class LocationUpdateRequest(BaseModel):
    next_location: str
    details: Optional[str] = "Location updated via API"

class StatusUpdateRequest(BaseModel):
    status: str  # GENUINE, SUSPICIOUS, RECALLED

class ProductResponse(ProductBase):
    id: int
    manufacturer_id: int
    manufacturer_name: str
    product_hash: str
    status: str
    is_onchain: bool
    registration_tx_hash: Optional[str] = None
    created_at: datetime.datetime
    updated_at: datetime.datetime

    class Config:
        from_attributes = True

class ProductDetailResponse(BaseModel):
    database: Dict[str, Any]
    blockchain: Optional[Dict[str, Any]] = None
