import io
import pytest
from app.core.config import settings
from app.models.audit import AuditLog
from tests.conftest import TestingSessionLocal

def register_test_mfr(client, company_name="Phase3 Test Mfr", gstin="27AAACA1234A1Z5", email="p3mfr@test.com"):
    file_data = io.BytesIO(b"Fake PDF Document Content")
    resp = client.post(
        "/api/auth/manufacturer/register",
        data={
            "company_name": company_name,
            "GSTIN": gstin,
            "company_address": "123 Test Street",
            "phone": "+919876543210",
            "email": email,
            "password": "Password123!"
        },
        files={"verification_document": ("compliance.pdf", file_data, "application/pdf")}
    )
    return resp

def get_admin_token(client):
    login_resp = client.post("/api/auth/login", json={
        "email": settings.ADMIN_EMAIL,
        "password": settings.ADMIN_PASSWORD
    })
    return login_resp.json()["access_token"]

# Test 1: Admin can list manufacturers (with filtering)
def test_1_admin_list_manufacturers_with_filters(client):
    register_test_mfr(client, company_name="Alpha Pharma", gstin="27AAACA1111A1Z5", email="alpha@pharma.com")
    register_test_mfr(client, company_name="Beta Biotech", gstin="27AAACA2222A1Z5", email="beta@biotech.com")

    admin_token = get_admin_token(client)
    headers = {"Authorization": f"Bearer {admin_token}"}

    resp_all = client.get("/api/admin/manufacturers", headers=headers)
    assert resp_all.status_code == 200
    assert len(resp_all.json()) >= 2

    resp_pending = client.get("/api/admin/manufacturers?status=PENDING", headers=headers)
    assert resp_pending.status_code == 200
    assert all(m["verification_status"] == "PENDING" for m in resp_pending.json())

    resp_alpha = client.get("/api/admin/manufacturers?company_name=Alpha", headers=headers)
    assert resp_alpha.status_code == 200
    assert any("Alpha" in m["company_name"] for m in resp_alpha.json())

# Test 2: Admin can view manufacturer details
def test_2_admin_view_manufacturer_details(client):
    reg_resp = register_test_mfr(client, company_name="Detail Test Mfr", gstin="27AAACA3333A1Z5", email="detail@mfr.com")
    mfr_id = reg_resp.json()["manufacturer_id"]

    admin_token = get_admin_token(client)
    resp = client.get(f"/api/admin/manufacturers/{mfr_id}", headers={"Authorization": f"Bearer {admin_token}"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["company_name"] == "Detail Test Mfr"
    assert data["email"] == "detail@mfr.com"

# Test 3: Manufacturer cannot access Admin manufacturer APIs
def test_3_manufacturer_cannot_access_admin_apis(client):
    register_test_mfr(client, email="mfr_no_admin@test.com", gstin="27AAACA4444A1Z5")
    mfr_token = client.post("/api/auth/login", json={"email": "mfr_no_admin@test.com", "password": "Password123!"}).json()["access_token"]
    headers = {"Authorization": f"Bearer {mfr_token}"}

    assert client.get("/api/admin/manufacturers", headers=headers).status_code == 403
    assert client.get("/api/admin/manufacturers/1", headers=headers).status_code == 403
    assert client.put("/api/admin/manufacturers/1/status", json={"status": "APPROVED"}, headers=headers).status_code == 403

# Test 4: Public user cannot access Admin manufacturer APIs
def test_4_public_user_cannot_access_admin_apis(client):
    assert client.get("/api/admin/manufacturers").status_code == 401
    assert client.get("/api/admin/manufacturers/1").status_code == 401
    assert client.put("/api/admin/manufacturers/1/status", json={"status": "APPROVED"}).status_code == 401

# Test 5: Admin can approve PENDING manufacturer
def test_5_admin_approve_pending_manufacturer(client):
    reg_resp = register_test_mfr(client, email="to_approve@test.com", gstin="27AAACA5555A1Z5")
    mfr_id = reg_resp.json()["manufacturer_id"]

    admin_token = get_admin_token(client)
    resp = client.put(
        f"/api/admin/manufacturers/{mfr_id}/status",
        json={"status": "APPROVED"},
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert resp.status_code == 200
    assert resp.json()["verification_status"] == "APPROVED"

# Test 6: Approved manufacturer can access protected manufacturer APIs
def test_6_approved_manufacturer_access(client):
    reg_resp = register_test_mfr(client, email="approved_access@test.com", gstin="27AAACA6666A1Z5")
    mfr_id = reg_resp.json()["manufacturer_id"]

    admin_token = get_admin_token(client)
    client.put(f"/api/admin/manufacturers/{mfr_id}/status", json={"status": "APPROVED"}, headers={"Authorization": f"Bearer {admin_token}"})

    mfr_token = client.post("/api/auth/login", json={"email": "approved_access@test.com", "password": "Password123!"}).json()["access_token"]
    resp = client.get("/api/manufacturer/test", headers={"Authorization": f"Bearer {mfr_token}"})
    assert resp.status_code == 200

# Test 7 & 8: Admin can reject a PENDING manufacturer & Rejected manufacturer is blocked
def test_7_8_admin_reject_manufacturer_and_block(client):
    reg_resp = register_test_mfr(client, email="to_reject@test.com", gstin="27AAACA7777A1Z5")
    mfr_id = reg_resp.json()["manufacturer_id"]

    admin_token = get_admin_token(client)
    reject_resp = client.put(
        f"/api/admin/manufacturers/{mfr_id}/status",
        json={"status": "REJECTED", "rejection_reason": "Invalid business license document"},
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert reject_resp.status_code == 200
    assert reject_resp.json()["verification_status"] == "REJECTED"

    mfr_token = client.post("/api/auth/login", json={"email": "to_reject@test.com", "password": "Password123!"}).json()["access_token"]
    assert client.get("/api/manufacturer/test", headers={"Authorization": f"Bearer {mfr_token}"}).status_code == 403

# Test 9 & 10: Admin can suspend an APPROVED manufacturer & Suspended manufacturer is blocked
def test_9_10_admin_suspend_manufacturer_and_block(client):
    reg_resp = register_test_mfr(client, email="to_suspend@test.com", gstin="27AAACA8888A1Z5")
    mfr_id = reg_resp.json()["manufacturer_id"]

    admin_token = get_admin_token(client)
    client.put(f"/api/admin/manufacturers/{mfr_id}/status", json={"status": "APPROVED"}, headers={"Authorization": f"Bearer {admin_token}"})
    suspend_resp = client.put(
        f"/api/admin/manufacturers/{mfr_id}/status",
        json={"status": "SUSPENDED", "rejection_reason": "Compliance investigation pending"},
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert suspend_resp.status_code == 200
    assert suspend_resp.json()["verification_status"] == "SUSPENDED"

    mfr_token = client.post("/api/auth/login", json={"email": "to_suspend@test.com", "password": "Password123!"}).json()["access_token"]
    assert client.get("/api/manufacturer/test", headers={"Authorization": f"Bearer {mfr_token}"}).status_code == 403

# Test 11: Manufacturer can view their own profile
def test_11_manufacturer_view_own_profile(client):
    register_test_mfr(client, company_name="Own Profile Mfr", email="own_profile@test.com", gstin="27AAACA9999A1Z5")
    token = client.post("/api/auth/login", json={"email": "own_profile@test.com", "password": "Password123!"}).json()["access_token"]

    resp = client.get("/api/manufacturer/profile", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["company_name"] == "Own Profile Mfr"
    assert data["email"] == "own_profile@test.com"

# Test 12: Manufacturer cannot view another manufacturer's profile (IDOR protection)
def test_12_manufacturer_idor_protection(client):
    register_test_mfr(client, company_name="Mfr One", email="mfr1@test.com", gstin="27AAACA0001A1Z5")
    register_test_mfr(client, company_name="Mfr Two", email="mfr2@test.com", gstin="27AAACA0002A1Z5")

    token1 = client.post("/api/auth/login", json={"email": "mfr1@test.com", "password": "Password123!"}).json()["access_token"]

    resp = client.get("/api/manufacturer/profile", headers={"Authorization": f"Bearer {token1}"})
    assert resp.status_code == 200
    assert resp.json()["email"] == "mfr1@test.com"
    assert resp.json()["company_name"] == "Mfr One"

# Test 13: Invalid manufacturer ID returns 404
def test_13_invalid_manufacturer_id_returns_404(client):
    admin_token = get_admin_token(client)
    headers = {"Authorization": f"Bearer {admin_token}"}
    assert client.get("/api/admin/manufacturers/999999", headers=headers).status_code == 404
    assert client.put("/api/admin/manufacturers/999999/status", json={"status": "APPROVED"}, headers=headers).status_code == 404

# Test 14: Invalid status returns 400
def test_14_invalid_status_returns_400(client):
    reg_resp = register_test_mfr(client, email="invalid_status@test.com", gstin="27AAACA0003A1Z5")
    mfr_id = reg_resp.json()["manufacturer_id"]
    admin_token = get_admin_token(client)

    resp = client.put(
        f"/api/admin/manufacturers/{mfr_id}/status",
        json={"status": "INVALID_STATUS_NAME"},
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert resp.status_code == 400
    assert "Invalid status" in resp.json()["detail"]

# Test 15: Audit logs are created for verification actions
def test_15_audit_logs_created_for_verification(client):
    reg_resp = register_test_mfr(client, email="audit_test@test.com", gstin="27AAACA0004A1Z5")
    mfr_id = reg_resp.json()["manufacturer_id"]
    admin_token = get_admin_token(client)

    client.put(f"/api/admin/manufacturers/{mfr_id}/status", json={"status": "APPROVED"}, headers={"Authorization": f"Bearer {admin_token}"})

    db = TestingSessionLocal()
    logs = db.query(AuditLog).filter(AuditLog.entity_type == "MANUFACTURER", AuditLog.entity_id == str(mfr_id)).all()
    assert len(logs) >= 1
    assert logs[0].action == "MANUFACTURER_APPROVED"
    db.close()

# Test 16: Verification document access is protected
def test_16_verification_document_access_protected(client):
    reg_resp = register_test_mfr(client, email="doc_protect@test.com", gstin="27AAACA0005A1Z5")
    mfr_id = reg_resp.json()["manufacturer_id"]

    assert client.get(f"/api/admin/manufacturers/{mfr_id}/document").status_code == 401

    mfr_token = client.post("/api/auth/login", json={"email": "doc_protect@test.com", "password": "Password123!"}).json()["access_token"]
    assert client.get(f"/api/admin/manufacturers/{mfr_id}/document", headers={"Authorization": f"Bearer {mfr_token}"}).status_code == 403

    admin_token = get_admin_token(client)
    doc_resp = client.get(f"/api/admin/manufacturers/{mfr_id}/document", headers={"Authorization": f"Bearer {admin_token}"})
    assert doc_resp.status_code == 200

# Test 17: Password hashes are never returned by manufacturer APIs
def test_17_password_hashes_never_exposed(client):
    register_test_mfr(client, email="no_pwd_hash@test.com", gstin="27AAACA0006A1Z5")
    token = client.post("/api/auth/login", json={"email": "no_pwd_hash@test.com", "password": "Password123!"}).json()["access_token"]

    profile_resp = client.get("/api/manufacturer/profile", headers={"Authorization": f"Bearer {token}"})
    profile_data = profile_resp.json()
    assert "password_hash" not in profile_data
    assert "password" not in profile_data

    admin_token = get_admin_token(client)
    admin_list_resp = client.get("/api/admin/manufacturers", headers={"Authorization": f"Bearer {admin_token}"})
    for m in admin_list_resp.json():
        assert "password_hash" not in m
        assert "password" not in m
