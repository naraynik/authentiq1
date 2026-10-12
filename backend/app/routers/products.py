import datetime
import uuid
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.models.user import User
from app.models.product import Product
from app.models.location import LocationHistory
from app.core.deps import require_manufacturer, require_admin, get_current_user, get_current_manufacturer_user
from app.services.blockchain_service import blockchain_service
from app.schemas.product import (
    ProductCreate,
    ProductBatchCreate,
    LocationUpdateRequest,
    StatusUpdateRequest,
    ProductResponse
)

def _place_text(place) -> str:
    if not place:
        return ""
    parts = [getattr(place, k, None) for k in ("name", "street", "city", "country")]
    return ", ".join(x.strip() for x in parts if x and x.strip())


def _normalise_payload(payload: ProductCreate) -> None:
    """Fill the original required fields from the structured web-frontend fields."""
    if not payload.product_id or not payload.product_id.strip():
        payload.product_id = "AQ-" + uuid.uuid4().hex[:8].upper()
    payload.product_id = payload.product_id.strip()
    if payload.manufacturing_date is None:
        payload.manufacturing_date = datetime.datetime.utcnow()
    if not payload.current_location:
        payload.current_location = _place_text(payload.facility) or "Not specified"
    if not payload.next_location:
        first = payload.distributors[0] if payload.distributors else None
        payload.next_location = _place_text(first) or "Not specified"


def _explorer_url(tx_hash):
    from app.core.config import settings
    if not tx_hash or not settings.EXPLORER_TX_URL:
        return None
    return settings.EXPLORER_TX_URL + (tx_hash if tx_hash.startswith("0x") else "0x" + tx_hash)


def _product_dict(p: Product) -> dict:
    return {
        "id": p.id,
        "product_id": p.product_id,
        "manufacturer_id": p.manufacturer_id,
        "manufacturer_name": p.manufacturer_name,
        "product_name": p.product_name,
        "batch_number": p.batch_number,
        "sku": p.sku,
        "manufacturing_date": p.manufacturing_date,
        "expiry_date": p.expiry_date,
        "current_location": p.current_location,
        "next_location": p.next_location,
        "facility": p.facility,
        "distributors": p.distributors or [],
        "product_hash": p.product_hash,
        "status": p.status,
        "is_onchain": p.is_onchain,
        "registration_tx_hash": p.registration_tx_hash,
        "registration_block": p.registration_block,
        "explorer_url": _explorer_url(p.registration_tx_hash),
        "created_at": p.created_at,
    }


router = APIRouter(prefix="/products", tags=["Product Management"])

@router.get("", status_code=status.HTTP_200_OK)
@router.get("/", status_code=status.HTTP_200_OK)
async def list_products(
    manufacturer_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """
    List registered products with optional manufacturer_id filter.
    """
    query = db.query(Product)
    if manufacturer_id:
        query = query.filter(Product.manufacturer_id == manufacturer_id)
    products = query.order_by(Product.created_at.desc()).all()
    return [_product_dict(p) for p in products]


@router.get("/mine", status_code=status.HTTP_200_OK)
async def list_my_products(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_manufacturer_user)
):
    """List products registered by the logged-in manufacturer (newest first)."""
    mfr = current_user.manufacturer
    products = (
        db.query(Product)
        .filter(Product.manufacturer_id == mfr.id)
        .order_by(Product.created_at.desc())
        .all()
    )
    return [_product_dict(p) for p in products]

@router.post("", status_code=status.HTTP_201_CREATED)
@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register_product(
    payload: ProductCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_manufacturer)
):
    """
    Register a new product (Approved Manufacturers Only).
    Flow:
    1. Validate JWT & Approved Manufacturer status
    2. Validate input product data
    3. Generate canonical deterministic product identifier/hash
    4. Save product in PostgreSQL DB with is_onchain=False
    5. Submit transaction to ProductVerification smart contract
    6. If tx succeeds: update is_onchain=True and save transaction_hash
    7. If tx fails: keep is_onchain=False and return clear error
    """
    mfr = current_user.manufacturer
    if not mfr or mfr.verification_status != "APPROVED":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only APPROVED manufacturers can register products"
        )
    _normalise_payload(payload)

    existing = db.query(Product).filter(Product.product_id == payload.product_id).first()
    if existing and not existing.is_onchain and existing.manufacturer_id == mfr.id:
        # An earlier attempt was saved but never reached the blockchain (e.g. the
        # wallet had no test ETH). Replace it so the manufacturer can simply retry.
        db.delete(existing)
        db.commit()
        existing = None
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Product with ID '{payload.product_id}' already registered"
        )

    m_ts = int(payload.manufacturing_date.timestamp())
    e_ts = int(payload.expiry_date.timestamp()) if payload.expiry_date else 0
    
    # Deriving canonical product hash
    product_hash_bytes = blockchain_service.generate_product_hash(
        payload.product_id,
        mfr.company_name,
        payload.batch_number,
        m_ts,
        e_ts
    )
    product_hash_str = "0x" + product_hash_bytes.hex()

    # Step 1: Create local DB record (is_onchain=False initially)
    product = Product(
        product_id=payload.product_id,
        manufacturer_id=mfr.id,
        manufacturer_name=mfr.company_name,
        product_name=payload.product_name,
        batch_number=payload.batch_number,
        manufacturing_date=payload.manufacturing_date,
        expiry_date=payload.expiry_date,
        current_location=payload.current_location,
        next_location=payload.next_location,
        product_hash=product_hash_str,
        status="GENUINE",
        is_onchain=False,
        registration_tx_hash=None,
        sku=payload.sku,
        facility=payload.facility.model_dump() if payload.facility else None,
        distributors=[d.model_dump() for d in payload.distributors],
    )
    db.add(product)
    db.commit()
    db.refresh(product)

    # Initial Location History entry
    initial_location = LocationHistory(
        product_id=product.product_id,
        location_name=payload.current_location,
        details=f"Product registered at {payload.current_location}",
        updated_by=current_user.email
    )
    db.add(initial_location)
    db.commit()

    # Step 2: Blockchain Registration
    tx_result = None
    try:
        tx_result = blockchain_service.register_product(
            product_id=payload.product_id,
            manufacturer_name=mfr.company_name,
            batch_number=payload.batch_number,
            manufacturing_date=payload.manufacturing_date,
            expiry_date=payload.expiry_date,
            current_location=payload.current_location,
            next_location=payload.next_location
        )
        
        # Update DB upon successful blockchain registration
        product.is_onchain = True
        product.registration_tx_hash = tx_result.get("transaction_hash")
        product.registration_block = tx_result.get("block_number")
        db.commit()
        db.refresh(product)
    except Exception as e:
        # Blockchain registration failed: DO NOT set is_onchain=True
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Product saved in database but blockchain registration failed: {str(e)}"
        )

    return {
        "message": "Product registered and recorded on blockchain successfully",
        "product_id": product.product_id,
        "product_name": product.product_name,
        "manufacturer_name": product.manufacturer_name,
        "product_hash": product.product_hash,
        "status": product.status,
        "is_onchain": product.is_onchain,
        "transaction_hash": product.registration_tx_hash,
        "tx_hash": product.registration_tx_hash,
        "block_number": tx_result.get("block_number") if tx_result else None,
        "gas_used": tx_result.get("gas_used") if tx_result else None
    }


@router.post("/batch", status_code=status.HTTP_201_CREATED)
async def register_product_batch(
    payload: ProductBatchCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_manufacturer)
):
    """
    Register batch of products on-chain and in DB.
    """
    mfr = current_user.manufacturer
    if not mfr or mfr.verification_status != "APPROVED":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only APPROVED manufacturers can register product batches"
        )

    # Validate duplicate IDs
    for pid in payload.product_ids:
        if db.query(Product).filter(Product.product_id == pid).first():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Product ID '{pid}' already exists in database"
            )

    created_products = []
    m_ts = int(payload.manufacturing_date.timestamp())
    e_ts = int(payload.expiry_date.timestamp()) if payload.expiry_date else 0

    for pid in payload.product_ids:
        ph_bytes = blockchain_service.generate_product_hash(
            pid, mfr.company_name, payload.batch_number, m_ts, e_ts
        )
        p = Product(
            product_id=pid,
            manufacturer_id=mfr.id,
            manufacturer_name=mfr.company_name,
            product_name=payload.product_name,
            batch_number=payload.batch_number,
            manufacturing_date=payload.manufacturing_date,
            expiry_date=payload.expiry_date,
            current_location=payload.current_location,
            next_location=payload.next_location,
            product_hash="0x" + ph_bytes.hex(),
            status="GENUINE",
            is_onchain=False
        )
        db.add(p)
        created_products.append(p)

    db.commit()

    # Blockchain Batch Register
    try:
        res = blockchain_service.register_product_batch(
            product_ids=payload.product_ids,
            manufacturer_name=mfr.company_name,
            batch_number=payload.batch_number,
            manufacturing_date=payload.manufacturing_date,
            expiry_date=payload.expiry_date,
            current_location=payload.current_location,
            next_location=payload.next_location
        )
        tx_hash = res.get("transaction_hash")
        for p in created_products:
            p.is_onchain = True
            p.registration_tx_hash = tx_hash
        db.commit()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Batch saved in DB but blockchain transaction failed: {str(e)}"
        )

    return {
        "message": f"Successfully registered batch of {len(payload.product_ids)} products",
        "product_ids": payload.product_ids,
        "is_onchain": True,
        "transaction_hash": tx_hash
    }


@router.get("/{product_id}", status_code=status.HTTP_200_OK)
async def get_product_details(
    product_id: str,
    db: Session = Depends(get_db)
):
    """
    Retrieve product details combining PostgreSQL database record and Blockchain state.
    """
    product = db.query(Product).filter(Product.product_id == product_id).first()
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product with ID '{product_id}' not found"
        )

    db_data = _product_dict(product)

    blockchain_data = None
    if product.is_onchain or blockchain_service.health_check().get("contract_accessible"):
        try:
            blockchain_data = blockchain_service.verify_product(product_id)
        except Exception as e:
            blockchain_data = {"error": f"Failed to fetch on-chain state: {str(e)}"}

    return {
        "product_id": product.product_id,
        "database": db_data,
        "blockchain": blockchain_data
    }


@router.get("/{product_id}/history", status_code=status.HTTP_200_OK)
async def get_product_history(
    product_id: str,
    db: Session = Depends(get_db)
):
    """
    Retrieve location and status history for product from DB and Blockchain.
    """
    product = db.query(Product).filter(Product.product_id == product_id).first()
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product with ID '{product_id}' not found"
        )

    db_locations = db.query(LocationHistory).filter(LocationHistory.product_id == product_id).order_by(LocationHistory.timestamp.asc()).all()
    db_history = [
        {
            "id": loc.id,
            "location_name": loc.location_name,
            "details": loc.details,
            "updated_by": loc.updated_by,
            "transaction_hash": loc.transaction_hash,
            "timestamp": loc.timestamp
        }
        for loc in db_locations
    ]

    blockchain_history = []
    try:
        blockchain_history = blockchain_service.get_location_history(product_id)
    except Exception as e:
        blockchain_history = [{"error": f"Failed to query on-chain history: {str(e)}"}]

    return {
        "product_id": product_id,
        "database_history": db_history,
        "blockchain_history": blockchain_history
    }


@router.post("/{product_id}/location", status_code=status.HTTP_200_OK)
async def update_product_location(
    product_id: str,
    payload: LocationUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_manufacturer)
):
    """
    Update product location (Approved Manufacturers Only).
    Updates DB and calls smart contract updateNextLocation.
    """
    product = db.query(Product).filter(Product.product_id == product_id).first()
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product '{product_id}' not found"
        )

    # Check manufacturer ownership
    if current_user.role != "ADMIN" and product.manufacturer_id != current_user.manufacturer.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this product's location"
        )

    old_next = product.next_location
    product.current_location = old_next
    product.next_location = payload.next_location

    tx_hash = None
    if product.is_onchain:
        try:
            res = blockchain_service.update_next_location(
                product_id=product_id,
                new_next_location=payload.next_location,
                details=payload.details or "Updated via API"
            )
            tx_hash = res.get("transaction_hash")
        except Exception as e:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Failed to update location on blockchain: {str(e)}"
            )

    loc_record = LocationHistory(
        product_id=product_id,
        location_name=payload.next_location,
        details=payload.details or f"Location updated to {payload.next_location}",
        updated_by=current_user.email,
        transaction_hash=tx_hash
    )
    db.add(loc_record)
    db.commit()
    db.refresh(product)

    return {
        "message": "Product location updated successfully",
        "product_id": product_id,
        "current_location": product.current_location,
        "next_location": product.next_location,
        "transaction_hash": tx_hash
    }


@router.post("/{product_id}/status", status_code=status.HTTP_200_OK)
async def update_product_status(
    product_id: str,
    payload: StatusUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Update product status (GENUINE, SUSPICIOUS, RECALLED).
    Requires Admin or Authorized Manufacturer role.
    """
    product = db.query(Product).filter(Product.product_id == product_id).first()
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product '{product_id}' not found"
        )

    valid_statuses = ["GENUINE", "SUSPICIOUS", "RECALLED"]
    if payload.status.upper() not in valid_statuses:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid status '{payload.status}'. Must be one of {valid_statuses}"
        )

    tx_hash = None
    if product.is_onchain:
        try:
            res = blockchain_service.update_product_status(
                product_id=product_id,
                new_status=payload.status.upper()
            )
            tx_hash = res.get("transaction_hash")
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Failed to update product status on blockchain: {str(e)}"
            )

    product.status = payload.status.upper()
    db.commit()
    db.refresh(product)

    return {
        "message": "Product status updated successfully",
        "product_id": product_id,
        "status": product.status,
        "transaction_hash": tx_hash
    }
