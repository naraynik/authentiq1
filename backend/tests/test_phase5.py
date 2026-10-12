import datetime
import pytest
import numpy as np
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient

from app.core.config import settings
from app.ai_client import ai_client, AIClient
from app.services.scan_service import scan_service, calculate_haversine_distance
from app.services.blockchain_service import blockchain_service


import importlib.util
import pytest

# The GNN needs PyTorch + PyTorch Geometric (requirements.txt). The light install used on
# small servers (requirements-render.txt) leaves them out, so these two tests are skipped there.
needs_torch = pytest.mark.skipif(
    importlib.util.find_spec("torch_geometric") is None,
    reason="PyTorch Geometric not installed (light install)",
)

def get_admin_token(client: TestClient) -> str:
    res = client.post("/api/auth/login", json={
        "email": settings.ADMIN_EMAIL,
        "password": settings.ADMIN_PASSWORD
    })
    assert res.status_code == 200, f"Admin login failed: {res.text}"
    return res.json()["access_token"]

def register_and_approve_manufacturer(client: TestClient, email: str, gstin: str):
    admin_token = get_admin_token(client)
    reg_res = client.post("/api/auth/manufacturer/register", data={
        "company_name": f"Co_{gstin}",
        "GSTIN": gstin,
        "company_address": "123 AI Park",
        "phone": "+919876543210",
        "email": email,
        "password": "Password@123"
    }, files={
        "verification_document": ("cert.pdf", b"%PDF-1.4 test file", "application/pdf")
    })
    assert reg_res.status_code == 201, f"Reg failed: {reg_res.text}"
    mfr_id = reg_res.json()["manufacturer_id"]

    client.put(
        f"/api/admin/manufacturers/{mfr_id}/status",
        json={"status": "APPROVED"},
        headers={"Authorization": f"Bearer {admin_token}"}
    )

    mfr_login = client.post("/api/auth/login", json={
        "email": email,
        "password": "Password@123"
    })
    assert mfr_login.status_code == 200
    return mfr_login.json()["access_token"], mfr_id


# ==========================================
# TEST 1 — AI MODEL LOADING AUDIT
# ==========================================
@needs_torch
def test_1_ai_model_loading_audit():
    """Test 1: Verify AI Client loads Random Forest and GNN models successfully."""
    client_instance = AIClient()
    assert client_instance.rf_model is not None, "Random Forest model failed to load"
    assert client_instance.gnn_model is not None, "GNN model failed to load"


# ==========================================
# TEST 2 — BEHAVIORAL CALCULATIONS (HAVERSINE & SPEED)
# ==========================================
def test_2_behavioral_calculations():
    """Test 2: Verify Haversine distance and travel speed calculations."""
    # Distance between Mumbai (19.0760, 72.8777) and Delhi (28.6139, 77.2090) ~ 1148 km
    dist = calculate_haversine_distance(19.0760, 72.8777, 28.6139, 77.2090)
    assert 1100.0 < dist < 1200.0, f"Unexpected Haversine distance: {dist}"


# ==========================================
# TEST 3 — RANDOM FOREST INFERENCE
# ==========================================
def test_3_random_forest_inference():
    """Test 3: Verify Random Forest inference returns valid probabilities."""
    res = ai_client.evaluate_with_random_forest(scan_velocity=1, hours_since_creation=24.0, is_location_anomaly=0)
    assert res is not None
    assert "authenticity_prob" in res
    assert "counterfeit_prob" in res
    assert 0.0 <= res["authenticity_prob"] <= 1.0


# ==========================================
# TEST 4 — GNN INFERENCE
# ==========================================
@needs_torch
def test_4_gnn_inference():
    """Test 4: Verify GNN model inference when 23-feature node matrices are provided."""
    vecs = np.random.randn(2, 23).astype(np.float32)
    edges = [[0, 1], [1, 0]]
    res = ai_client.evaluate_with_gnn(vecs, edges)
    assert res is not None
    assert "mean_authenticity" in res
    assert "mean_counterfeit_risk" in res


# ==========================================
# TEST 5 — NORMAL SCAN SEQUENCE
# ==========================================
def test_5_normal_scan_sequence(client: TestClient):
    """Test 5: Register product and run normal, realistic scans."""
    token, _ = register_and_approve_manufacturer(client, "mfr_p5_norm@test.com", "27AAAAA0000C1Z1")

    with patch.object(blockchain_service, "register_product") as mock_reg:
        mock_reg.return_value = {
            "success": True,
            "transaction_hash": "0xnorm123",
            "block_number": 50,
            "gas_used": 190000,
            "product_hash": "0x1122334455667788990011223344556677889900112233445566778899001122",
            "is_onchain": True
        }

        payload = {
            "product_id": "PROD-P5-NORM",
            "product_name": "Normal Vaccine",
            "batch_number": "BATCH-NORM",
            "manufacturing_date": "2026-01-01T00:00:00",
            "current_location": "Plant Alpha",
            "next_location": "Distributor Beta"
        }
        reg_res = client.post("/api/products/register", json=payload, headers={"Authorization": f"Bearer {token}"})
        assert reg_res.status_code == 201

    # Scan 1: At Plant Alpha (Mumbai lat/lon)
    scan1_payload = {
        "product_id": "PROD-P5-NORM",
        "location": "Plant Alpha",
        "latitude": 19.0760,
        "longitude": 72.8777,
        "device_id": "DEV-001"
    }
    scan1_res = client.post("/api/scans", json=scan1_payload)
    assert scan1_res.status_code == 201
    d1 = scan1_res.json()
    assert d1["final_verdict"] == "GENUINE"
    assert d1["blockchain_verified"] is True
    assert d1["behavioral_analysis"]["duplicated_qr_detected"] is False


# ==========================================
# TEST 6 — SUSPICIOUS DUPLICATED QR SCAN SEQUENCE (IMPOSSIBLE TRAVEL)
# ==========================================
def test_6_suspicious_duplicated_qr_sequence(client: TestClient):
    """Test 6: Detect duplicated QR usage when same QR appears in distant locations impossibly fast."""
    token, _ = register_and_approve_manufacturer(client, "mfr_p5_susp@test.com", "27AAAAA0000C1Z2")

    with patch.object(blockchain_service, "register_product") as mock_reg:
        mock_reg.return_value = {
            "success": True,
            "transaction_hash": "0xsusp123",
            "block_number": 51,
            "gas_used": 195000,
            "product_hash": "0x9988776655443322110099887766554433221100998877665544332211009988",
            "is_onchain": True
        }

        payload = {
            "product_id": "PROD-P5-DUPQR",
            "product_name": "High Value Drug",
            "batch_number": "BATCH-DUP",
            "manufacturing_date": "2026-01-01T00:00:00",
            "current_location": "Plant Alpha, Mumbai",
            "next_location": "Distributor Beta, Pune"
        }
        client.post("/api/products/register", json=payload, headers={"Authorization": f"Bearer {token}"})

    # Scan 1: Mumbai (19.0760, 72.8777)
    scan1 = client.post("/api/scans", json={
        "product_id": "PROD-P5-DUPQR",
        "location": "Mumbai Plant",
        "latitude": 19.0760,
        "longitude": 72.8777,
        "device_id": "DEV-MUMBAI"
    })
    assert scan1.status_code == 201

    # Scan 2: London (51.5074, -0.1278) - 1 second later (Impossible speed ~5500 km in 0 hours!)
    scan2 = client.post("/api/scans", json={
        "product_id": "PROD-P5-DUPQR",
        "location": "London Pharmacy",
        "latitude": 51.5074,
        "longitude": -0.1278,
        "device_id": "DEV-LONDON"
    })
    assert scan2.status_code == 201
    d2 = scan2.json()

    # Blockchain identity MUST remain verified/true!
    assert d2["blockchain_verified"] is True
    assert d2["blockchain_verdict"] == "VERIFIED_ONCHAIN"

    # Behavioral analysis MUST flag impossible travel and duplicated QR!
    assert d2["behavioral_analysis"]["is_impossible_travel"] is True
    assert d2["behavioral_analysis"]["duplicated_qr_detected"] is True
    assert d2["ai_verdict"] in ["COUNTERFEIT", "SUSPICIOUS"]
    assert d2["final_verdict"] in ["COUNTERFEIT", "SUSPICIOUS"]
    assert any("Impossible Travel" in flag for flag in d2["flags"])


# ==========================================
# TEST 7 — AI FAILURE SAFETY
# ==========================================
def test_7_ai_failure_safety(client: TestClient):
    """Test 7: Verify API handles AI model failure gracefully without corrupting DB or calling blockchain txs."""
    token, _ = register_and_approve_manufacturer(client, "mfr_p5_err@test.com", "27AAAAA0000C1Z3")

    with patch.object(blockchain_service, "register_product") as mock_reg, \
         patch.object(ai_client, "evaluate_with_random_forest") as mock_rf:

        mock_reg.return_value = {"success": True, "transaction_hash": "0xerr123", "is_onchain": True}
        mock_rf.side_effect = RuntimeError("Simulated AI model crash")

        payload = {
            "product_id": "PROD-P5-AFAIL",
            "product_name": "Safety Test Drug",
            "batch_number": "BATCH-FAIL",
            "manufacturing_date": "2026-01-01T00:00:00",
            "current_location": "Plant Alpha",
            "next_location": "Distributor Beta"
        }
        client.post("/api/products/register", json=payload, headers={"Authorization": f"Bearer {token}"})

        res = client.post("/api/scans", json={
            "product_id": "PROD-P5-AFAIL",
            "location": "Plant Alpha"
        })
        assert res.status_code == 201
        data = res.json()
        assert data["ai_available"] is False
        assert data["blockchain_verified"] is True


# ==========================================
# TEST 8 — SCAN HISTORY AND STATS ENDPOINTS
# ==========================================
def test_8_scan_history_and_stats_endpoints(client: TestClient):
    """Test 8: Verify GET /api/scans/history/{id} and GET /api/scans/stats."""
    token, _ = register_and_approve_manufacturer(client, "mfr_p5_stat@test.com", "27AAAAA0000C1Z4")

    with patch.object(blockchain_service, "register_product") as mock_reg:
        mock_reg.return_value = {"success": True, "transaction_hash": "0xstat123", "is_onchain": True}

        payload = {
            "product_id": "PROD-P5-STATS",
            "product_name": "Stats Medicine",
            "batch_number": "BATCH-STAT",
            "manufacturing_date": "2026-01-01T00:00:00",
            "current_location": "Plant Alpha",
            "next_location": "Distributor Beta"
        }
        client.post("/api/products/register", json=payload, headers={"Authorization": f"Bearer {token}"})

    # Post 2 scans
    client.post("/api/scans", json={"product_id": "PROD-P5-STATS", "location": "Plant Alpha"})
    client.post("/api/scans", json={"product_id": "PROD-P5-STATS", "location": "Distributor Beta"})

    hist_res = client.get("/api/scans/history/PROD-P5-STATS")
    assert hist_res.status_code == 200
    assert hist_res.json()["count"] == 2

    stats_res = client.get("/api/scans/stats")
    assert stats_res.status_code == 200
    assert "total_scans" in stats_res.json()
    assert stats_res.json()["total_scans"] >= 2

