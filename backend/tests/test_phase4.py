import datetime
import pytest
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient

from app.core.config import settings
from app.services.blockchain_service import blockchain_service, BlockchainService

def get_admin_token(client: TestClient) -> str:
    res = client.post("/api/auth/login", json={
        "email": settings.ADMIN_EMAIL,
        "password": settings.ADMIN_PASSWORD
    })
    assert res.status_code == 200, f"Admin login failed: {res.text}"
    return res.json()["access_token"]

def register_and_approve_manufacturer(client: TestClient, email: str, gstin: str):
    admin_token = get_admin_token(client)
    
    # Register manufacturer
    reg_res = client.post("/api/auth/manufacturer/register", data={
        "company_name": f"Co_{gstin}",
        "GSTIN": gstin,
        "company_address": "123 Industrial Park",
        "phone": "+919876543210",
        "email": email,
        "password": "Password@123"
    }, files={
        "verification_document": ("cert.pdf", b"%PDF-1.4 test file", "application/pdf")
    })
    assert reg_res.status_code == 201, f"Reg failed: {reg_res.text}"
    mfr_id = reg_res.json()["manufacturer_id"]

    # Admin Approve via PUT /api/admin/manufacturers/{id}/status
    app_res = client.put(
        f"/api/admin/manufacturers/{mfr_id}/status",
        json={"status": "APPROVED"},
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert app_res.status_code == 200, f"Approve failed: {app_res.text}"

    # Login Manufacturer
    mfr_login = client.post("/api/auth/login", json={
        "email": email,
        "password": "Password@123"
    })
    assert mfr_login.status_code == 200, f"Mfr login failed: {mfr_login.text}"
    return mfr_login.json()["access_token"], mfr_id


# ==========================================
# TEST 1 — BLOCKCHAIN HEALTH
# ==========================================
def test_blockchain_health_check(client: TestClient):
    """Test 1: Blockchain health endpoint returns structured health object."""
    res = client.get("/api/health/blockchain")
    assert res.status_code == 200
    data = res.json()
    assert "status" in data
    assert "blockchain" in data
    assert "contract_address" in data["blockchain"]


# ==========================================
# TEST 2 — CONTRACT READ FUNCTION
# ==========================================
def test_contract_read_only_call():
    """Test 2: Call read-only contract utility functions or generate hash."""
    h = blockchain_service.generate_product_hash(
        "PROD-TEST-100", "Acme Pharma", "BATCH-001", 1600000000, 1700000000
    )
    assert isinstance(h, bytes)
    assert len(h) == 32


# ==========================================
# TEST 3 — PRODUCT REGISTRATION
# ==========================================
def test_product_registration(client: TestClient):
    """Test 3: Register a product with mocked Web3 execution & DB state check."""
    token, _ = register_and_approve_manufacturer(client, "mfr_p4_1@test.com", "27AAAAA0000A1Z1")

    with patch.object(blockchain_service, "register_product") as mock_reg:
        mock_reg.return_value = {
            "success": True,
            "transaction_hash": "0x1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef",
            "block_number": 101,
            "is_onchain": True
        }

        payload = {
            "product_id": "PROD-P4-001",
            "product_name": "Authentic Vaccine A",
            "batch_number": "BATCH-P4-1",
            "manufacturing_date": "2026-01-01T00:00:00",
            "expiry_date": "2028-01-01T00:00:00",
            "current_location": "Plant Alpha",
            "next_location": "Distributor Beta"
        }

        res = client.post(
            "/api/products/register",
            json=payload,
            headers={"Authorization": f"Bearer {token}"}
        )
        assert res.status_code == 201, f"Product register failed: {res.text}"
        data = res.json()
        assert data["is_onchain"] is True
        assert data["transaction_hash"].startswith("0x")
        assert data["product_id"] == "PROD-P4-001"


# ==========================================
# TEST 4 — DUPLICATE PRODUCT REJECTION
# ==========================================
def test_duplicate_product_registration(client: TestClient):
    """Test 4: Attempt to register duplicate product ID."""
    token, _ = register_and_approve_manufacturer(client, "mfr_p4_dup@test.com", "27AAAAA0000A1Z2")

    with patch.object(blockchain_service, "register_product") as mock_reg:
        mock_reg.return_value = {
            "success": True,
            "transaction_hash": "0xd1",
            "is_onchain": True
        }
        payload = {
            "product_id": "PROD-P4-DUP",
            "product_name": "Test Prod",
            "batch_number": "B1",
            "manufacturing_date": "2026-01-01T00:00:00",
            "current_location": "L1",
            "next_location": "L2"
        }
        res1 = client.post("/api/products/register", json=payload, headers={"Authorization": f"Bearer {token}"})
        assert res1.status_code == 201

        res2 = client.post("/api/products/register", json=payload, headers={"Authorization": f"Bearer {token}"})
        assert res2.status_code == 400
        assert "already registered" in res2.json()["detail"]


# ==========================================
# TEST 5 — PRODUCT VERIFICATION
# ==========================================
def test_product_verification(client: TestClient):
    """Test 5: Verify registered product details."""
    token, _ = register_and_approve_manufacturer(client, "mfr_p4_v@test.com", "27AAAAA0000A1Z3")

    with patch.object(blockchain_service, "register_product") as mock_reg, \
         patch.object(blockchain_service, "verify_product") as mock_verify:
        
        mock_reg.return_value = {"success": True, "transaction_hash": "0xv1", "is_onchain": True}
        mock_verify.return_value = {
            "product_id": "PROD-P4-VERIFY",
            "manufacturer_name": "Co_27AAAAA0000A1Z3",
            "batch_number": "B1",
            "status": "GENUINE",
            "is_onchain": True
        }

        payload = {
            "product_id": "PROD-P4-VERIFY",
            "product_name": "Verify Medicine",
            "batch_number": "B1",
            "manufacturing_date": "2026-01-01T00:00:00",
            "current_location": "L1",
            "next_location": "L2"
        }
        client.post("/api/products/register", json=payload, headers={"Authorization": f"Bearer {token}"})

        res = client.get("/api/products/PROD-P4-VERIFY")
        assert res.status_code == 200
        data = res.json()
        assert data["database"]["product_id"] == "PROD-P4-VERIFY"
        assert data["blockchain"]["status"] == "GENUINE"


# ==========================================
# TEST 6 — PRODUCT STATUS UPDATE
# ==========================================
def test_product_status_update(client: TestClient):
    """Test 6: Update product status on-chain and in DB."""
    token, _ = register_and_approve_manufacturer(client, "mfr_p4_s@test.com", "27AAAAA0000A1Z4")

    with patch.object(blockchain_service, "register_product") as mock_reg, \
         patch.object(blockchain_service, "update_product_status") as mock_stat:

        mock_reg.return_value = {"success": True, "transaction_hash": "0xs1", "is_onchain": True}
        mock_stat.return_value = {"success": True, "transaction_hash": "0xs2"}

        payload = {
            "product_id": "PROD-P4-STAT",
            "product_name": "Status Medicine",
            "batch_number": "B1",
            "manufacturing_date": "2026-01-01T00:00:00",
            "current_location": "L1",
            "next_location": "L2"
        }
        client.post("/api/products/register", json=payload, headers={"Authorization": f"Bearer {token}"})

        stat_res = client.post(
            "/api/products/PROD-P4-STAT/status",
            json={"status": "RECALLED"},
            headers={"Authorization": f"Bearer {token}"}
        )
        assert stat_res.status_code == 200
        assert stat_res.json()["status"] == "RECALLED"


# ==========================================
# TEST 7 — PRODUCT LOCATION & HISTORY
# ==========================================
def test_product_location_and_history(client: TestClient):
    """Test 7: Update location and check history."""
    token, _ = register_and_approve_manufacturer(client, "mfr_p4_loc@test.com", "27AAAAA0000A1Z5")

    with patch.object(blockchain_service, "register_product") as mock_reg, \
         patch.object(blockchain_service, "update_next_location") as mock_loc, \
         patch.object(blockchain_service, "get_location_history") as mock_hist:

        mock_reg.return_value = {"success": True, "transaction_hash": "0xl1", "is_onchain": True}
        mock_loc.return_value = {"success": True, "transaction_hash": "0xl2"}
        mock_hist.return_value = [{"location_name": "Warehouse Gamma", "details": "Moved", "updated_by": "0x1"}]

        payload = {
            "product_id": "PROD-P4-LOC",
            "product_name": "Loc Medicine",
            "batch_number": "B1",
            "manufacturing_date": "2026-01-01T00:00:00",
            "current_location": "Plant Alpha",
            "next_location": "Distributor Beta"
        }
        client.post("/api/products/register", json=payload, headers={"Authorization": f"Bearer {token}"})

        loc_res = client.post(
            "/api/products/PROD-P4-LOC/location",
            json={"next_location": "Pharmacy Delta", "details": "In Transit"},
            headers={"Authorization": f"Bearer {token}"}
        )
        assert loc_res.status_code == 200
        assert loc_res.json()["next_location"] == "Pharmacy Delta"

        hist_res = client.get("/api/products/PROD-P4-LOC/history")
        assert hist_res.status_code == 200
        assert len(hist_res.json()["database_history"]) >= 2


# ==========================================
# TEST 8 — AUTHORIZATION DENIED
# ==========================================
def test_authorization_denied(client: TestClient):
    """Test 8: Unapproved manufacturer or unauthenticated user denied."""
    # Register pending manufacturer
    client.post("/api/auth/manufacturer/register", data={
        "company_name": "Unapproved Co",
        "GSTIN": "27AAAAA0000A1Z6",
        "company_address": "Address",
        "phone": "+919876543210",
        "email": "pending_mfr@test.com",
        "password": "Password@123"
    }, files={"verification_document": ("c.pdf", b"%PDF", "application/pdf")})

    pending_login = client.post("/api/auth/login", json={
        "email": "pending_mfr@test.com",
        "password": "Password@123"
    }).json()["access_token"]

    payload = {
        "product_id": "PROD-P4-UNAUTH",
        "product_name": "Forbidden Medicine",
        "batch_number": "B1",
        "manufacturing_date": "2026-01-01T00:00:00",
        "current_location": "L1",
        "next_location": "L2"
    }

    res = client.post(
        "/api/products/register",
        json=payload,
        headers={"Authorization": f"Bearer {pending_login}"}
    )
    assert res.status_code == 403


# ==========================================
# TEST 9 — DATABASE CONSISTENCY ON BLOCKCHAIN FAILURE
# ==========================================
def test_database_consistency_on_failure(client: TestClient):
    """Test 9: Blockchain failure retains DB state with is_onchain=False."""
    token, _ = register_and_approve_manufacturer(client, "mfr_p4_fail@test.com", "27AAAAA0000A1Z7")

    with patch.object(blockchain_service, "register_product") as mock_reg:
        mock_reg.side_effect = RuntimeError("Blockchain connection timed out")

        payload = {
            "product_id": "PROD-P4-FAIL",
            "product_name": "Failed Tx Medicine",
            "batch_number": "B1",
            "manufacturing_date": "2026-01-01T00:00:00",
            "current_location": "L1",
            "next_location": "L2"
        }

        res = client.post(
            "/api/products/register",
            json=payload,
            headers={"Authorization": f"Bearer {token}"}
        )
        assert res.status_code == 502
        assert "blockchain registration failed" in res.json()["detail"]

        # Check DB record
        prod_res = client.get("/api/products/PROD-P4-FAIL")
        assert prod_res.status_code == 200
        assert prod_res.json()["database"]["is_onchain"] is False
        assert prod_res.json()["database"]["registration_tx_hash"] is None


# ==========================================
# TEST 10 — PHASE 1-3 REGRESSION
# ==========================================
def test_phase_1_3_regression(client: TestClient):
    """Test 10: Verify Phase 1-3 core health & auth endpoints work seamlessly."""
    health_res = client.get("/api/health")
    assert health_res.status_code == 200
    assert health_res.json()["status"] == "healthy"


# ==========================================
# TEST 11 — RECEIPT METADATA IN REGISTRATION
# ==========================================
def test_product_registration_receipt_metadata(client: TestClient):
    """Test 11: Registration response exposes tx_hash, block_number, gas_used, product_hash, and is_onchain."""
    token, _ = register_and_approve_manufacturer(client, "mfr_p4_meta@test.com", "27AAAAA0000A1Z8")

    with patch.object(blockchain_service, "register_product") as mock_reg:
        mock_reg.return_value = {
            "success": True,
            "transaction_hash": "0xabc123def4567890abc123def4567890abc123def4567890abc123def4567890",
            "block_number": 42,
            "gas_used": 210000,
            "product_hash": "0x1111222233334444555566667777888899990000111122223333444455556666",
            "is_onchain": True
        }

        payload = {
            "product_id": "PROD-P4-META",
            "product_name": "Metadata Medicine",
            "batch_number": "BATCH-META",
            "manufacturing_date": "2026-01-01T00:00:00",
            "current_location": "Plant Alpha",
            "next_location": "Distributor Beta"
        }

        res = client.post(
            "/api/products/register",
            json=payload,
            headers={"Authorization": f"Bearer {token}"}
        )
        assert res.status_code == 201, f"Product register failed: {res.text}"
        data = res.json()
        assert data["is_onchain"] is True
        assert data["transaction_hash"].startswith("0x")
        assert data["tx_hash"] == data["transaction_hash"]
        assert data["block_number"] == 42
        assert data["gas_used"] == 210000
        assert data["product_hash"].startswith("0x")


# ==========================================
# TEST 12 — HYBRID PUBLIC QR VERIFICATION
# ==========================================
def test_hybrid_public_qr_verification(client: TestClient):
    """Test 12: Hybrid QR verification performs on-chain check for on-chain products."""
    token, _ = register_and_approve_manufacturer(client, "mfr_p4_hyb@test.com", "27AAAAA0000A1Z9")

    with patch.object(blockchain_service, "register_product") as mock_reg, \
         patch.object(blockchain_service, "verify_product") as mock_verify:

        mock_reg.return_value = {
            "success": True,
            "transaction_hash": "0xhyb123",
            "block_number": 15,
            "gas_used": 150000,
            "product_hash": "0x1234567890123456789012345678901234567890123456789012345678901234",
            "is_onchain": True
        }

        payload = {
            "product_id": "PROD-P4-HYBRID",
            "product_name": "Hybrid Vaccine",
            "batch_number": "BATCH-HYB",
            "manufacturing_date": "2026-01-01T00:00:00",
            "current_location": "Plant Alpha",
            "next_location": "Distributor Beta"
        }

        reg_res = client.post("/api/products/register", json=payload, headers={"Authorization": f"Bearer {token}"})
        assert reg_res.status_code == 201
        prod_hash = reg_res.json()["product_hash"]

        # Mock matching on-chain data
        mock_verify.return_value = {
            "product_id": "PROD-P4-HYBRID",
            "manufacturer_name": "Co_27AAAAA0000A1Z9",
            "batch_number": "BATCH-HYB",
            "product_hash": prod_hash,
            "status": "GENUINE",
            "is_onchain": True
        }

        # Verify via QR endpoint
        v_res = client.get("/api/verify/PROD-P4-HYBRID")
        assert v_res.status_code == 200
        data = v_res.json()
        assert data["is_valid"] is True
        assert data["verified"] is True
        assert data["verification_source"] == "database_and_blockchain"
        assert data["blockchain_verified"] is True


# ==========================================
# TEST 13 — HYBRID VERIFICATION MISMATCH AND FAILURE SAFETY
# ==========================================
def test_hybrid_verification_mismatch_and_failure(client: TestClient):
    """Test 13: Handle DB/blockchain mismatch and live read failure safely."""
    token, _ = register_and_approve_manufacturer(client, "mfr_p4_mis@test.com", "27AAAAA0000B1Z1")

    with patch.object(blockchain_service, "register_product") as mock_reg, \
         patch.object(blockchain_service, "verify_product") as mock_verify:

        mock_reg.return_value = {
            "success": True,
            "transaction_hash": "0xmis123",
            "block_number": 20,
            "gas_used": 180000,
            "is_onchain": True
        }

        payload = {
            "product_id": "PROD-P4-MISMATCH",
            "product_name": "Mismatch Med",
            "batch_number": "BATCH-MIS",
            "manufacturing_date": "2026-01-01T00:00:00",
            "current_location": "Plant Alpha",
            "next_location": "Distributor Beta"
        }

        client.post("/api/products/register", json=payload, headers={"Authorization": f"Bearer {token}"})

        # Scenario A: Status Mismatch (DB: GENUINE, On-chain: RECALLED)
        mock_verify.return_value = {
            "product_id": "PROD-P4-MISMATCH",
            "manufacturer_name": "Co_27AAAAA0000B1Z1",
            "batch_number": "BATCH-MIS",
            "product_hash": "0x0000000000000000000000000000000000000000000000000000000000000000",
            "status": "RECALLED",
            "is_onchain": True
        }

        mis_res = client.get("/api/verify/PROD-P4-MISMATCH")
        assert mis_res.status_code == 200
        mis_data = mis_res.json()
        assert mis_data["is_valid"] is False
        assert mis_data["verified"] is False
        assert mis_data["blockchain_verified"] is False
        assert mis_data["tampered"] is True
        assert len(mis_data["mismatches"]) > 0

        # Scenario B: Live Blockchain Read Exception
        mock_verify.side_effect = RuntimeError("RPC endpoint connection refused")

        err_res = client.get("/api/verify/PROD-P4-MISMATCH")
        assert err_res.status_code == 200
        err_data = err_res.json()
        assert err_data["is_valid"] is False
        assert err_data["verified"] is False
        assert err_data["blockchain_verified"] is False
        assert "blockchain_error" in err_data
        assert "connection refused" in err_data["blockchain_error"]


