from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database.database import get_db
from app.schemas.scan import ScanCreate, ScanResponse
from app.services.scan_service import scan_service

router = APIRouter(prefix="/scans", tags=["Scan History & AI Verification"])

@router.post("", status_code=status.HTTP_201_CREATED)
@router.post("/evaluate", status_code=status.HTTP_201_CREATED)
async def evaluate_and_record_scan(
    payload: ScanCreate,
    db: Session = Depends(get_db)
):
    """
    Public Endpoint: Submit a QR product scan for AI behavioral & anti-counterfeit evaluation.
    Calculates velocity, time delta, geographic distance, and travel speed relative to prior scans.
    Detects duplicated/copied QR codes, executes AI inference, records entry in PostgreSQL scan_history.
    """
    result = scan_service.record_and_evaluate_scan(db, payload)
    return result

@router.get("/history/{product_id}", status_code=status.HTTP_200_OK)
async def get_product_scan_history(
    product_id: str,
    db: Session = Depends(get_db)
):
    """
    Retrieve PostgreSQL scan history for a product.
    """
    history = scan_service.get_scan_history(db, product_id)
    return {
        "product_id": product_id,
        "count": len(history),
        "history": [
            {
                "id": s.id,
                "product_id": s.product_id,
                "scanned_at": s.scanned_at,
                "location": s.location,
                "latitude": s.latitude,
                "longitude": s.longitude,
                "scan_velocity": s.scan_velocity,
                "hours_since_creation": s.hours_since_creation,
                "authenticity_probability": s.authenticity_probability,
                "anomaly_score": s.anomaly_score,
                "ai_verdict": s.ai_verdict,
                "blockchain_verdict": s.blockchain_verdict,
                "final_verdict": s.final_verdict,
                "flags": s.flags.split("; ") if s.flags else []
            }
            for s in history
        ]
    }

@router.get("/stats", status_code=status.HTTP_200_OK)
async def get_scan_statistics(
    db: Session = Depends(get_db)
):
    """
    Retrieve summary scan statistics.
    """
    return scan_service.get_scan_stats(db)
