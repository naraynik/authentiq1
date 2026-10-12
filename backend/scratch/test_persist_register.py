import sys
import os
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database.database import SessionLocal
from app.models.product import Product
from app.models.manufacturer import Manufacturer
from app.services.blockchain_service import blockchain_service

def test_register():
    print("Testing persistent blockchain product registration...")
    health = blockchain_service.health_check()
    print("Health check:", health)

    if not health.get("contract_accessible"):
        print("FAIL: Contract not accessible!")
        sys.exit(1)

    db = SessionLocal()
    try:
        # Get first manufacturer from DB
        mfr = db.query(Manufacturer).first()
        mfr_id = mfr.id if mfr else 1

        # Check if PERSIST-TEST-001 exists in DB, clean up if needed for clean test
        existing = db.query(Product).filter(Product.product_id == "PERSIST-TEST-001").first()
        if existing:
            db.delete(existing)
            db.commit()

        # Check if registered on-chain
        exists_onchain = blockchain_service.product_exists("PERSIST-TEST-001")
        print("Exists on-chain before registration attempt:", exists_onchain)

        if not exists_onchain:
            # Register product on-chain via blockchain_service
            receipt = blockchain_service.register_product(
                product_id="PERSIST-TEST-001",
                manufacturer_name="AuthentiQ Persistent Factory",
                batch_number="PERSIST-BATCH-01",
                manufacturing_date=datetime.utcnow(),
                expiry_date=None,
                current_location="Mumbai Plant",
                next_location="Delhi Hub"
            )
            print("SUCCESS: Product registered on-chain!")
            print("Tx Hash:", receipt.get("transaction_hash"))
            print("Block Number:", receipt.get("block_number"))
            print("Gas Used:", receipt.get("gas_used"))
            prod_hash = receipt.get("product_hash")
        else:
            print("Product PERSIST-TEST-001 already registered on-chain!")
            onchain_info = blockchain_service.verify_product("PERSIST-TEST-001")
            prod_hash = onchain_info.get("product_hash")

        # Save in PostgreSQL
        prod = Product(
            product_id="PERSIST-TEST-001",
            manufacturer_id=mfr_id,
            product_name="Persistent Ledger Test Unit",
            manufacturer_name="AuthentiQ Persistent Factory",
            batch_number="PERSIST-BATCH-01",
            manufacturing_date=datetime.utcnow(),
            current_location="Mumbai Plant",
            next_location="Delhi Hub",
            status="REGISTERED",
            is_onchain=True,
            product_hash=prod_hash
        )
        db.add(prod)
        db.commit()

        # Verify on-chain data
        onchain_data = blockchain_service.verify_product("PERSIST-TEST-001")
        print("VERIFY ON-CHAIN DATA:", onchain_data)

    finally:
        db.close()

if __name__ == "__main__":
    test_register()
