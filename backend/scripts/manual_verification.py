import os
import sys
import io
import uuid
import random
from fastapi.testclient import TestClient

from app.main import app
from app.core.config import settings
from app.seed_admin import seed_admin

def run_manual_verification():
    print("=== MANUAL VERIFICATION WORKFLOW ===")
    
    client = TestClient(app)
    
    # 1. Verify GET /api/health
    resp_health = client.get("/api/health")
    print(f"1 & 2. GET /api/health Status: {resp_health.status_code}, Response: {resp_health.json()['status']}")
    assert resp_health.status_code == 200
    
    # 3. Seed Admin Command
    print("3. Executing admin seed mechanism...")
    seed_admin()
    
    # 4. Verify Admin Login
    resp_admin_login = client.post("/api/auth/login", json={
        "email": settings.ADMIN_EMAIL,
        "password": settings.ADMIN_PASSWORD
    })
    admin_token = resp_admin_login.json().get("access_token")
    print(f"4. Admin Login Status: {resp_admin_login.status_code}, Role: {resp_admin_login.json().get('role')}")
    assert resp_admin_login.status_code == 200 and admin_token is not None
    
    # 5 & 6. Register Manufacturer & Verify PENDING Status
    uid = uuid.uuid4().hex[:6]
    digits_4 = f"{random.randint(1000, 9999)}"
    test_email = f"mfr_{uid}@testpharma.com"
    test_gstin = f"27AAAAA{digits_4}A1Z5"
    
    doc_file = io.BytesIO(b"Verification Document Data PDF")
    reg_resp = client.post(
        "/api/auth/manufacturer/register",
        data={
            "company_name": f"Manual Test Pharma {uid}",
            "GSTIN": test_gstin,
            "company_address": "45 Corporate Park, Mumbai",
            "phone": "+919988776655",
            "email": test_email,
            "password": "Password123!"
        },
        files={"verification_document": ("compliance_doc.pdf", doc_file, "application/pdf")}
    )
    if reg_resp.status_code != 201:
        print(f"Registration Error Detail: {reg_resp.json()}")
    mfr_id = reg_resp.json().get("manufacturer_id")
    status_pending = reg_resp.json().get("verification_status")
    print(f"5 & 6. Manufacturer Registration Status: {reg_resp.status_code}, Initial verification_status: {status_pending}")
    assert reg_resp.status_code == 201 and status_pending == "PENDING"
    
    # Login as Pending Manufacturer
    mfr_login = client.post("/api/auth/login", json={
        "email": test_email,
        "password": "Password123!"
    })
    pending_token = mfr_login.json().get("access_token")
    
    # 7. Verify PENDING Manufacturer cannot access protected functionality
    protected_resp = client.get("/api/manufacturer/test", headers={"Authorization": f"Bearer {pending_token}"})
    print(f"7. Pending Manufacturer Protected Endpoint Access Status: {protected_resp.status_code} (Blocked as Expected)")
    assert protected_resp.status_code == 403
    
    # 8. Approve Manufacturer via Admin API
    approve_resp = client.put(
        f"/api/admin/manufacturers/{mfr_id}/status",
        json={"status": "APPROVED"},
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    print(f"8. Admin Approval Status: {approve_resp.status_code}, Updated Status: {approve_resp.json().get('verification_status')}")
    assert approve_resp.status_code == 200
    
    # 9. Verify Approved Manufacturer Login
    app_login = client.post("/api/auth/login", json={
        "email": test_email,
        "password": "Password123!"
    })
    approved_token = app_login.json().get("access_token")
    print(f"9. Approved Manufacturer Login Status: {app_login.status_code}, Token Issued: {approved_token is not None}")
    assert app_login.status_code == 200
    
    # 10. Verify Approved Manufacturer Endpoint Access
    mfr_endpoint_resp = client.get("/api/manufacturer/test", headers={"Authorization": f"Bearer {approved_token}"})
    print(f"10. Approved Manufacturer Endpoint Access Status: {mfr_endpoint_resp.status_code}, Message: {mfr_endpoint_resp.json().get('message')}")
    assert mfr_endpoint_resp.status_code == 200
    
    # 11. Verify Manufacturer cannot access Admin Endpoint
    admin_endpoint_resp = client.get("/api/admin/test", headers={"Authorization": f"Bearer {approved_token}"})
    print(f"11. Manufacturer Attempting Admin Endpoint Status: {admin_endpoint_resp.status_code} (Forbidden as Expected)")
    assert admin_endpoint_resp.status_code == 403
    
    # 12. Verify Public Endpoint Access Without Auth
    public_resp = client.get("/api/public/test")
    print(f"12. Public Endpoint Unauthenticated Access Status: {public_resp.status_code}, Auth State: {public_resp.json().get('authenticated')}")
    assert public_resp.status_code == 200
    
    print("=== MANUAL VERIFICATION SUCCESSFUL ===")

if __name__ == "__main__":
    run_manual_verification()
