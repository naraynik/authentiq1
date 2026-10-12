from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database.database import get_db
from app.models.product import Product
from app.services.blockchain_service import blockchain_service

router = APIRouter(prefix="/verify", tags=["Public Verification"])

@router.get("/{qr_code}")
async def verify_product_qr(
    qr_code: str,
    db: Session = Depends(get_db)
):
    """
    Public Endpoint: Verify product authenticity via QR code string or Product ID.
    Performs hybrid Database + Blockchain verification when product is registered on-chain.
    No account or JWT token required.
    """
    product = db.query(Product).filter(
        (Product.product_id == qr_code) | (Product.product_hash == qr_code)
    ).first()

    if not product:
        return {
            "qr_code": qr_code,
            "status": "UNREGISTERED",
            "is_valid": False,
            "verified": False,
            "message": "Product QR code not found in system registry."
        }

    base_res = {
        "qr_code": qr_code,
        "product_id": product.product_id,
        "product_name": product.product_name,
        "manufacturer_name": product.manufacturer_name,
        "batch_number": product.batch_number,
        "current_location": product.current_location,
        "status": product.status,
    }

    # If product is not on-chain, perform DB-only verification
    if not product.is_onchain:
        return {
            **base_res,
            "is_valid": True,
            "verified": True,
            "verification_source": "database_only",
            "blockchain_verified": False,
            "message": "Product is authentic and registered in database."
        }

    # Product is on-chain: perform live hybrid blockchain check
    try:
        onchain_data = blockchain_service.verify_product(product.product_id)

        # Normalize product hashes for comparison
        db_hash = (product.product_hash or "").lower()
        onchain_hash = (onchain_data.get("product_hash") or "").lower()
        if db_hash and not db_hash.startswith("0x"):
            db_hash = "0x" + db_hash
        if onchain_hash and not onchain_hash.startswith("0x"):
            onchain_hash = "0x" + onchain_hash

        # Normalize status values for comparison
        db_status = (product.status or "").upper()
        onchain_status = (onchain_data.get("status") or "").upper()

        id_matches = (product.product_id == onchain_data.get("product_id"))
        hash_matches = (db_hash == onchain_hash)
        status_matches = (db_status == onchain_status)

        is_consistent = id_matches and hash_matches and status_matches

        if is_consistent:
            return {
                **base_res,
                "is_valid": True,
                "verified": True,
                "verification_source": "database_and_blockchain",
                "blockchain_verified": True,
                "onchain_data": {
                    "product_id": onchain_data.get("product_id"),
                    "product_hash": onchain_data.get("product_hash"),
                    "status": onchain_data.get("status")
                },
                "message": "Product is authentic and verified on both Database and Blockchain."
            }
        else:
            mismatches = []
            if not id_matches:
                mismatches.append(f"Product ID mismatch (DB: {product.product_id}, On-chain: {onchain_data.get('product_id')})")
            if not hash_matches:
                mismatches.append(f"Product hash mismatch (DB: {product.product_hash}, On-chain: {onchain_data.get('product_hash')})")
            if not status_matches:
                mismatches.append(f"Status mismatch (DB: {product.status}, On-chain: {onchain_data.get('status')})")

            return {
                **base_res,
                "is_valid": False,
                "verified": False,
                "verification_source": "database_and_blockchain",
                "blockchain_verified": False,
                "tampered": True,
                "mismatches": mismatches,
                "message": f"Product verification FAILED: Database and Blockchain data mismatch. {'; '.join(mismatches)}"
            }

    except Exception as e:
        # Live blockchain read failure: return safe verification-failure result
        return {
            **base_res,
            "is_valid": False,
            "verified": False,
            "verification_source": "database_and_blockchain",
            "blockchain_verified": False,
            "blockchain_error": str(e),
            "message": f"Product is registered on-chain, but live blockchain verification failed: {str(e)}"
        }


from app.schemas.scan import ScanCreate
from app.services.scan_service import scan_service

@router.post("/scan", status_code=status.HTTP_200_OK)
async def verify_scan_full(
    payload: ScanCreate,
    db: Session = Depends(get_db)
):
    """
    Public Endpoint: Combined verification combining DB, Blockchain, and AI Behavioral Analysis.
    Evaluates scan history patterns, velocity, speed, and location anomalies for copied QR detection.
    """
    return scan_service.record_and_evaluate_scan(db, payload)




# ---------------------------------------------------------------------------
# Web frontend: one call that records the scan and returns the full scan report
# ---------------------------------------------------------------------------
from fastapi import Request
from pydantic import BaseModel
from sqlalchemy import func
from app.models.scan import ScanHistory


class ReportRequest(BaseModel):
    product_id: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    location: Optional[str] = None


@router.post("/report", status_code=status.HTTP_200_OK)
async def scan_report(payload: ReportRequest, request: Request, db: Session = Depends(get_db)):
    """
    Public: record a customer scan and return everything the scan report shows:
    product + distributors, blockchain check, this scan's AI verdict and the scan history.
    Product IDs are matched exactly first, then case-insensitively (typed IDs).
    """
    from app.routers.products import _product_dict

    code = payload.product_id.strip()
    product = db.query(Product).filter(
        (Product.product_id == code) | (Product.product_hash == code)
    ).first()
    if not product:
        product = db.query(Product).filter(func.lower(Product.product_id) == code.lower()).first()
    if not product:
        return {"found": False, "product_id": code, "message": "This code is not registered with AuthentiQ."}

    has_coords = payload.latitude is not None and payload.longitude is not None
    location = payload.location or (
        f"{payload.latitude:.4f}, {payload.longitude:.4f}" if has_coords else "Location not shared"
    )
    scan = scan_service.record_and_evaluate_scan(
        db,
        ScanCreate(
            product_id=product.product_id,
            location=location,
            latitude=payload.latitude,
            longitude=payload.longitude,
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
        ),
    )
    verification = await verify_product_qr(product.product_id, db)
    history = (
        db.query(ScanHistory)
        .filter(ScanHistory.product_id == product.product_id)
        .order_by(ScanHistory.scanned_at.asc())
        .limit(100)
        .all()
    )
    return {
        "found": True,
        "product": _product_dict(product),
        "verification": {
            k: verification.get(k)
            for k in ("is_valid", "verified", "blockchain_verified", "verification_source", "tampered", "message")
        },
        "scan": scan,
        "history": [
            {
                "scanned_at": s.scanned_at,
                "location": s.location,
                "latitude": s.latitude,
                "longitude": s.longitude,
                "final_verdict": s.final_verdict,
                "flags": s.flags.split("; ") if s.flags else [],
            }
            for s in history
        ],
    }
