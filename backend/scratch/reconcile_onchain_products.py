"""
AuthentiQ Safe Dataset Reconciliation Utility
Audits PostgreSQL products against current persistent blockchain state.
Supports --dry-run (default) and --reconcile flags.
"""

import sys
import os
import argparse
import logging
from datetime import datetime

# Add parent backend directory to sys.path
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from app.database.database import SessionLocal
from app.models.product import Product
from app.services.blockchain_service import blockchain_service

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

def reconcile_products(dry_run: bool = True):
    db = SessionLocal()
    try:
        products = db.query(Product).all()
        logger.info(f"Loaded {len(products)} product records from PostgreSQL.")

        # Check blockchain connection
        health = blockchain_service.health_check()
        if not health.get("rpc_reachable") or not health.get("contract_accessible"):
            logger.error(f"Persistent blockchain is unreachable or contract inaccessible: {health.get('error')}")
            sys.exit(1)

        logger.info(f"Connected to persistent blockchain at {blockchain_service.rpc_url} (Chain ID: {health.get('chain_id')})")
        logger.info(f"Contract Address: {blockchain_service.contract_address}")
        logger.info(f"Mode: {'DRY-RUN (Audit only)' if dry_run else 'RECONCILE (Active re-registration)'}")
        logger.info("=" * 70)

        report = []
        for p in products:
            exists_onchain = False
            try:
                exists_onchain = blockchain_service.product_exists(p.product_id)
            except Exception as e:
                logger.warning(f"Could not query on-chain existence for product {p.product_id}: {e}")

            status = "UNKNOWN"
            if exists_onchain and p.is_onchain:
                status = "PRESENT (Consistent on DB & Chain)"
            elif exists_onchain and not p.is_onchain:
                status = "PRESENT_ON_CHAIN (DB flag needs update)"
                if not dry_run:
                    p.is_onchain = True
            elif not exists_onchain and p.is_onchain:
                status = "INCONSISTENT (DB says is_onchain=True but missing on new chain)"
            elif not exists_onchain and not p.is_onchain:
                status = "UNREGISTERED (DB only)"

            item_res = {
                "product_id": p.product_id,
                "product_name": p.product_name,
                "db_is_onchain": p.is_onchain,
                "onchain_exists": exists_onchain,
                "status": status
            }
            report.append(item_res)

            logger.info(f"Product [{p.product_id}] '{p.product_name}': {status}")

            # Reconcile if requested and missing on-chain
            if not dry_run and not exists_onchain:
                logger.info(f"   -> Reconciling product [{p.product_id}] on persistent blockchain...")
                try:
                    mfg_date = p.manufacturing_date or datetime.utcnow()
                    exp_date = p.expiry_date
                    receipt = blockchain_service.register_product(
                        product_id=p.product_id,
                        manufacturer_name=p.manufacturer_name or "AuthentiQ Manufacturer",
                        batch_number=p.batch_number or "BATCH-001",
                        manufacturing_date=mfg_date,
                        expiry_date=exp_date,
                        current_location=p.current_location or "Origin Factory",
                        next_location=p.next_location or "Distribution Hub"
                    )
                    p.is_onchain = True
                    p.product_hash = receipt.get("product_hash")
                    p.transaction_hash = receipt.get("transaction_hash")
                    logger.info(f"   ✓ Reconciled! New Tx Hash: {receipt.get('transaction_hash')} (Block #{receipt.get('block_number')})")
                except Exception as reg_err:
                    logger.error(f"   ✗ Reconciliation failed for [{p.product_id}]: {reg_err}")

        if not dry_run:
            db.commit()
            logger.info("PostgreSQL updates committed.")

        logger.info("=" * 70)
        logger.info("RECONCILIATION SUMMARY:")
        consistent_count = sum(1 for r in report if "PRESENT" in r["status"])
        inconsistent_count = sum(1 for r in report if "INCONSISTENT" in r["status"])
        unregistered_count = sum(1 for r in report if "UNREGISTERED" in r["status"])
        logger.info(f"  Consistent: {consistent_count}")
        logger.info(f"  Inconsistent (Missing on Chain): {inconsistent_count}")
        logger.info(f"  Unregistered: {unregistered_count}")

    finally:
        db.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="AuthentiQ Product Blockchain Reconciliation Utility")
    parser.add_argument("--reconcile", action="store_true", help="Execute real on-chain re-registration for missing products")
    args = parser.parse_args()

    reconcile_products(dry_run=not args.reconcile)
