import datetime
import math
import logging
import json
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from app.models.product import Product
from app.models.scan import ScanHistory
from app.schemas.scan import ScanCreate, ScanResponse
from app.ai_client import ai_client
from app.services.blockchain_service import blockchain_service

logger = logging.getLogger(__name__)

# A scan further than this from every registered distributor/facility is flagged.
DISTRIBUTOR_RADIUS_KM = 150.0

def calculate_haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate Great Circle distance between two points on Earth in kilometers."""
    R = 6371.0  # Earth radius in km
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (math.sin(dlat / 2.0) ** 2 +
         math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2.0) ** 2)
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return R * c

def _is_named_place(value: Optional[str]) -> bool:
    return bool(value and value.strip() and value.strip().lower() not in {"location not shared", "unknown", "n/a"})


class ScanService:
    def record_and_evaluate_scan(
        self,
        db: Session,
        payload: ScanCreate
    ) -> Dict[str, Any]:
        """
        Behavioral QR Scan Analysis Pipeline:
        1. Find product in DB.
        2. Query historical scan records for same product.
        3. Calculate velocity, time delta, geographic distance, and implied travel speed.
        4. Detect duplicated QR usage & impossible travel anomalies.
        5. Run AI inference (Random Forest + GNN if applicable).
        6. Store scan record in PostgreSQL scan_history table.
        7. Return structured verification & behavioral result.
        """
        now = datetime.datetime.utcnow()

        # 1. Product Lookup
        product = db.query(Product).filter(
            (Product.product_id == payload.product_id) | (Product.product_hash == payload.product_id)
        ).first()

        if not product:
            return {
                "product_id": payload.product_id,
                "status": "UNREGISTERED",
                "is_valid": False,
                "verified": False,
                "blockchain_verified": False,
                "ai_verdict": "UNREGISTERED",
                "final_verdict": "UNREGISTERED",
                "authenticity_probability": 0.0,
                "anomaly_score": 1.0,
                "flags": ["Product QR code not found in system registry."],
                "behavioral_analysis": {
                    "total_scans": 0,
                    "scan_velocity_24h": 0,
                    "duplicated_qr_detected": False
                },
                "scanned_at": now.isoformat()
            }

        # 2. Historical Scans & Behavioral Metrics Calculation
        history = db.query(ScanHistory).filter(
            ScanHistory.product_id == product.product_id
        ).order_by(ScanHistory.scanned_at.desc()).all()

        total_scans = len(history) + 1
        cutoff_24h = now - datetime.timedelta(hours=24)
        scans_24h = sum(
            1 for s in history 
            if s.scanned_at and (s.scanned_at.replace(tzinfo=None) if hasattr(s.scanned_at, "tzinfo") and s.scanned_at.tzinfo else s.scanned_at) >= cutoff_24h
        ) + 1

        hours_since_creation = 0.0
        if product.manufacturing_date:
            mfg_dt = product.manufacturing_date
            if hasattr(mfg_dt, "tzinfo") and mfg_dt.tzinfo:
                mfg_dt = mfg_dt.replace(tzinfo=None)
            hours_since_creation = max(0.0, (now - mfg_dt).total_seconds() / 3600.0)

        time_diff_hours = None
        geographic_distance_km = 0.0
        implied_speed_kmh = 0.0
        is_impossible_travel = False
        location_changed = False

        if history:
            last_scan = history[0]
            if payload.latitude is not None and payload.longitude is not None:
                # Compare against the most recent scan that has coordinates, so a scan
                # without shared location in between does not hide a copied code.
                last_scan = next((h for h in history if h.latitude is not None and h.longitude is not None), last_scan)
            last_dt = last_scan.scanned_at
            if hasattr(last_dt, "tzinfo") and last_dt.tzinfo:
                last_dt = last_dt.replace(tzinfo=None)
            time_diff_hours = max(0.0001, (now - last_dt).total_seconds() / 3600.0)

            # Geographic Distance Calculation
            if (payload.latitude is not None and payload.longitude is not None and
                last_scan.latitude is not None and last_scan.longitude is not None):
                geographic_distance_km = calculate_haversine_distance(
                    last_scan.latitude, last_scan.longitude,
                    payload.latitude, payload.longitude
                )
            elif (
                # Only compare place names when neither scan has coordinates and both
                # actually named a place (a scan without shared location is unknown,
                # not a different place).
                payload.latitude is None and last_scan.latitude is None
                and _is_named_place(last_scan.location) and _is_named_place(payload.location)
            ):
                if last_scan.location.strip().lower() != payload.location.strip().lower():
                    location_changed = True
                    geographic_distance_km = 500.0  # Default proxy distance for distinct named locations

            if location_changed or geographic_distance_km > 0:
                implied_speed_kmh = geographic_distance_km / time_diff_hours

            # Impossible Travel Speed / Duplicated QR Detection
            # e.g., speed > 800 km/h (faster than commercial air transit) or distinct location in < 5 mins
            if (implied_speed_kmh > 800.0) or (location_changed and time_diff_hours < 0.1):
                is_impossible_travel = True

        # Location Anomaly Check
        is_location_anomaly = 1 if (
            is_impossible_travel or
            (payload.location and product.current_location and
             payload.location.strip().lower() != product.current_location.strip().lower() and
             payload.location.strip().lower() != (product.next_location or "").strip().lower() and
             any(x in payload.location.lower() for x in ["tokyo", "japan", "suspicious", "unknown"]))
        ) else 0

        # Distributor match check (web frontend): if the customer shared their
        # location and the manufacturer gave coordinates for its distributors /
        # facility, flag scans far from every registered place.
        distributor_mismatch = False
        nearest_known_km = None
        if payload.latitude is not None and payload.longitude is not None:
            known = [d for d in (product.distributors or []) if isinstance(d, dict)]
            if isinstance(product.facility, dict):
                known.append(product.facility)
            points = [
                (float(k["lat"]), float(k["lon"]))
                for k in known
                if k.get("lat") is not None and k.get("lon") is not None
            ]
            if points:
                nearest_known_km = min(
                    calculate_haversine_distance(lat, lon, payload.latitude, payload.longitude)
                    for lat, lon in points
                )
                if nearest_known_km > DISTRIBUTOR_RADIUS_KM:
                    distributor_mismatch = True
                    is_location_anomaly = 1

        flags: List[str] = []
        if distributor_mismatch:
            flags.append("Scan Location Does Not Match Registered Distributor")
        if is_impossible_travel:
            flags.append("Impossible Travel Speed / Duplicated QR Code Detected")
        if scans_24h > 5:
            flags.append("High Scan Frequency")
        if is_location_anomaly and not distributor_mismatch and "Impossible Travel" not in "".join(flags):
            flags.append("Geographical Velocity Violation")
        if hours_since_creation < 0.5:
            flags.append("Pre-mature Scan Sequence")

        # 3. AI Model Inference
        ai_available = True
        rf_result = None
        gnn_result = None
        auth_prob = 0.95
        anomaly_score = 0.05

        try:
            rf_result = ai_client.evaluate_with_random_forest(
                scan_velocity=scans_24h,
                hours_since_creation=hours_since_creation,
                is_location_anomaly=is_location_anomaly
            )
            if rf_result:
                auth_prob = float(rf_result.get("authenticity_prob", 0.95))
                anomaly_score = float(rf_result.get("counterfeit_prob", 0.05))

            # Advanced RF evaluation if raw scan optical data provided
            if payload.raw_scan_data:
                adv_data = dict(payload.raw_scan_data)
                adv_data.setdefault("hours_since_creation", hours_since_creation)
                adv_data.setdefault("scan_velocity", scans_24h)
                adv_data.setdefault("is_location_anomaly", is_location_anomaly)
                adv_res = ai_client.evaluate_scan_advanced(adv_data)
                if adv_res:
                    auth_prob = min(auth_prob, adv_res.get("authenticity_probability", auth_prob))
                    anomaly_score = max(anomaly_score, adv_res.get("anomaly_score", anomaly_score))
                    for f in adv_res.get("flags", []):
                        if f not in flags:
                            flags.append(f)

            # GNN over this product's scan history (current scan last)
            def _anomalous(h) -> int:
                return 1 if (h.flags and any(k in h.flags for k in ("Impossible Travel", "Distributor", "Geographical"))) else 0
            graph_nodes = [
                (h.scan_velocity or 1, h.hours_since_creation or 0.0, _anomalous(h))
                for h in reversed(history[:49])
            ] + [(scans_24h, hours_since_creation, is_location_anomaly)]
            gnn_result = ai_client.evaluate_scan_graph(graph_nodes)
            if gnn_result:
                anomaly_score = 0.6 * anomaly_score + 0.4 * gnn_result["counterfeit_prob"]
                auth_prob = 1.0 - anomaly_score

        except Exception as e:
            logger.error(f"AI Model Inference error: {e}")
            ai_available = False

        # Override probabilities if impossible travel / duplicated QR detected
        if is_impossible_travel:
            auth_prob = min(auth_prob, 0.15)
            anomaly_score = max(anomaly_score, 0.85)

        if distributor_mismatch:
            anomaly_score = max(anomaly_score, 0.40)  # at least SUSPICIOUS
            auth_prob = min(auth_prob, 0.60)

        # Map AI Verdict
        if anomaly_score >= 0.60 or is_impossible_travel:
            ai_verdict = "COUNTERFEIT"
        elif anomaly_score >= 0.35 or len(flags) >= 2:
            ai_verdict = "SUSPICIOUS"
        else:
            ai_verdict = "GENUINE"

        # 4. Blockchain Verification Status
        blockchain_verified = product.is_onchain
        blockchain_verdict = "VERIFIED_ONCHAIN" if product.is_onchain else "NOT_ONCHAIN"

        # 5. Combined Final Verdict (Preserving Blockchain Identity)
        if not product.is_onchain:
            final_verdict = "UNREGISTERED"
        elif ai_verdict in ["COUNTERFEIT", "SUSPICIOUS"]:
            final_verdict = ai_verdict
        else:
            final_verdict = "GENUINE"

        # 6. Save Scan Record in PostgreSQL scan_history
        flags_str = "; ".join(flags) if flags else None
        scan_record = ScanHistory(
            product_id=product.product_id,
            scanned_at=now,
            latitude=payload.latitude,
            longitude=payload.longitude,
            location=payload.location,
            device_id=payload.device_id,
            ip_address=payload.ip_address,
            user_agent=payload.user_agent,
            scan_velocity=scans_24h,
            hours_since_creation=hours_since_creation,
            authenticity_probability=auth_prob,
            anomaly_score=anomaly_score,
            ai_verdict=ai_verdict,
            blockchain_verdict=blockchain_verdict,
            final_verdict=final_verdict,
            flags=flags_str,
            raw_scan_data=payload.raw_scan_data
        )

        db.add(scan_record)
        db.commit()
        db.refresh(scan_record)

        # 7. Construct Response
        return {
            "id": scan_record.id,
            "product_id": product.product_id,
            "product_name": product.product_name,
            "manufacturer_name": product.manufacturer_name,
            "location": payload.location,
            "scanned_at": now.isoformat(),
            "scan_velocity": scans_24h,
            "hours_since_creation": hours_since_creation,
            "authenticity_probability": auth_prob,
            "anomaly_score": anomaly_score,
            "ai_verdict": ai_verdict,
            "blockchain_verdict": blockchain_verdict,
            "blockchain_verified": blockchain_verified,
            "final_verdict": final_verdict,
            "is_valid": (final_verdict == "GENUINE"),
            "flags": flags,
            "ai_available": ai_available,
            "models_used": {
                "random_forest": rf_result is not None,
                "gnn": gnn_result is not None,
            },
            "behavioral_analysis": {
                "total_scans": total_scans,
                "scan_velocity_24h": scans_24h,
                "time_diff_hours": round(time_diff_hours, 4) if time_diff_hours is not None else None,
                "geographic_distance_km": round(geographic_distance_km, 2),
                "implied_speed_kmh": round(implied_speed_kmh, 2),
                "is_impossible_travel": is_impossible_travel,
                "duplicated_qr_detected": is_impossible_travel,
                "distributor_mismatch": distributor_mismatch,
                "nearest_registered_place_km": round(nearest_known_km, 1) if nearest_known_km is not None else None
            }
        }

    def get_scan_history(self, db: Session, product_id: str, limit: int = 50) -> List[ScanHistory]:
        """Fetch scan history records for a product ordered by scanned_at desc."""
        return db.query(ScanHistory).filter(
            ScanHistory.product_id == product_id
        ).order_by(ScanHistory.scanned_at.desc()).limit(limit).all()

    def get_scan_stats(self, db: Session) -> Dict[str, Any]:
        """Get summary stats of recorded scans."""
        total = db.query(ScanHistory).count()
        genuine = db.query(ScanHistory).filter(ScanHistory.final_verdict == "GENUINE").count()
        suspicious = db.query(ScanHistory).filter(ScanHistory.final_verdict == "SUSPICIOUS").count()
        counterfeit = db.query(ScanHistory).filter(ScanHistory.final_verdict == "COUNTERFEIT").count()
        return {
            "total_scans": total,
            "genuine_count": genuine,
            "suspicious_count": suspicious,
            "counterfeit_count": counterfeit
        }

scan_service = ScanService()
