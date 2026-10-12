from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import datetime

# Product schemas
class ProductCreate(BaseModel):
    product_id: str
    name: str
    batch_number: str
    production_location: str

class ProductResponse(BaseModel):
    id: int
    product_id: str
    name: str
    batch_number: str
    production_location: str
    registered_at: datetime.datetime

    class Config:
        from_attributes = True

# Verification schemas
class VerifyRequest(BaseModel):
    product_id: str
    manufacturing_location: str
    origin: str
    weather_conditions: str
    temperature: float
    humidity: float
    micro_textures: float
    color_printing_patterns: float
    geometric_alignment: float
    surface_features: float
    printing_artifacts: float
    frequency_features: float
    color_space_metrics: float
    spectral_metrics: float
    deep_learning_latent_features: float
    qr_code_integrity: float
    barcode_integrity: float
    product_network: Optional[Dict[str, Any]] = None

class ModelScores(BaseModel):
    """Scores from individual models."""
    random_forest: Optional[Dict[str, float]] = None
    gnn_network: Optional[Dict[str, Any]] = None

class AIMetrics(BaseModel):
    authenticity_probability: float
    anomaly_score: float
    flags: List[str]
    model_scores: Optional[ModelScores] = None

class BlockchainReceipt(BaseModel):
    registered: bool
    product_id: str
    token_id: Optional[str] = None
    manufacturer: str
    block_timestamp: str
    mint_timestamp: Optional[str] = None
    scan_count: Optional[int] = 0
    last_scan_timestamp: Optional[str] = ""
    last_scan_location: Optional[str] = ""
    status_verdict: Optional[int] = 0
    transaction_hash: str
    block_number: int

class VerifyResponse(BaseModel):
    status: str # authentic, counterfeit, unregistered
    message: str
    ai_metrics: Optional[AIMetrics] = None
    blockchain_receipt: Optional[BlockchainReceipt] = None
