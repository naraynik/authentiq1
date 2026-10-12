import io
import pytest
import jwt
from app.core.config import settings
from app.models.user import User

# Test 1: Admin login
def test_1_admin_login(client):
    response = client.post("/api/auth/login", json={
        "email": settings.ADMIN_EMAIL,
        "password": settings.ADMIN_PASSWORD
    })
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["role"] == "ADMIN"
    assert data["user"]["email"] == settings.ADMIN_EMAIL

# Test 2: Manufacturer registration
def test_2_manufacturer_registration(client):
    file_data = io.BytesIO(b"Fake PDF Document Content")
    response = client.post(
        "/api/auth/manufacturer/register",
        data={
            "company_name": "Acme Pharma Ltd",
            "GSTIN": "27AAACA1234A1Z5",
            "company_address": "123 Industrial Estate, Mumbai",
            "phone": "+919876543210",
            "email": "mfr@acmepharma.com",
            "password": "Password123!"
        },
        files={
            "verification_document": ("doc.pdf", file_data, "application/pdf")
        }
    )
    assert response.status_code == 201
    data = response.json()
    assert data["verification_status"] == "PENDING"
    assert data["company_name"] == "Acme Pharma Ltd"

# Test 3: Manufacturer login
def test_3_manufacturer_login(client):
    file_data = io.BytesIO(b"Fake PDF Content")
    client.post(
        "/api/auth/manufacturer/register",
        data={
            "company_name": "Acme Pharma Ltd",
            "GSTIN": "27AAACA1234A1Z5",
            "company_address": "123 Industrial Estate, Mumbai",
            "phone": "+919876543210",
            "email": "mfr@acmepharma.com",
            "password": "Password123!"
        },
        files={"verification_document": ("doc.pdf", file_data, "application/pdf")}
    )

    response = client.post("/api/auth/login", json={
        "email": "mfr@acmepharma.com",
        "password": "Password123!"
    })
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["role"] == "MANUFACTURER"
    assert data["user"]["verification_status"] == "PENDING"

# Test 4: Invalid password
def test_4_invalid_password(client):
    response = client.post("/api/auth/login", json={
        "email": settings.ADMIN_EMAIL,
        "password": "WrongPassword999!"
    })
    assert response.status_code == 401
    data = response.json()
    assert data["detail"] == "Invalid email or password"

# Test 5: Pending manufacturer (blocked from protected operations)
def test_5_pending_manufacturer(client):
    file_data = io.BytesIO(b"Fake PDF Content")
    client.post(
        "/api/auth/manufacturer/register",
        data={
            "company_name": "Pending Mfr Ltd",
            "GSTIN": "29ABCDE1234F1Z5",
            "company_address": "456 Tech Park, Bangalore",
            "phone": "+919876543211",
            "email": "pending@mfr.com",
            "password": "Password123!"
        },
        files={"verification_document": ("doc.pdf", file_data, "application/pdf")}
    )

    login_resp = client.post("/api/auth/login", json={
        "email": "pending@mfr.com",
        "password": "Password123!"
    })
    assert login_resp.status_code == 200
    token = login_resp.json()["access_token"]

    # Calling protected manufacturer test endpoint returns 403 Forbidden
    test_resp = client.get("/api/manufacturer/test", headers={"Authorization": f"Bearer {token}"})
    assert test_resp.status_code == 403

# Test 6: Approved manufacturer
def test_6_approved_manufacturer(client):
    file_data = io.BytesIO(b"Fake PDF Content")
    reg_resp = client.post(
        "/api/auth/manufacturer/register",
        data={
            "company_name": "Approved Mfr Ltd",
            "GSTIN": "33XYZDE1234F1Z5",
            "company_address": "789 Trade Zone, Chennai",
            "phone": "+919876543212",
            "email": "approved@mfr.com",
            "password": "Password123!"
        },
        files={"verification_document": ("doc.pdf", file_data, "application/pdf")}
    )
    mfr_id = reg_resp.json()["manufacturer_id"]

    # Admin login and approval
    admin_login = client.post("/api/auth/login", json={
        "email": settings.ADMIN_EMAIL,
        "password": settings.ADMIN_PASSWORD
    })
    admin_token = admin_login.json()["access_token"]
    client.put(
        f"/api/admin/manufacturers/{mfr_id}/status",
        json={"status": "APPROVED"},
        headers={"Authorization": f"Bearer {admin_token}"}
    )

    # Approved manufacturer login and endpoint access
    mfr_login = client.post("/api/auth/login", json={
        "email": "approved@mfr.com",
        "password": "Password123!"
    })
    token = mfr_login.json()["access_token"]
    test_resp = client.get("/api/manufacturer/test", headers={"Authorization": f"Bearer {token}"})
    assert test_resp.status_code == 200
    assert test_resp.json()["user"]["verification_status"] == "APPROVED"

# Test 7: Rejected manufacturer
def test_7_rejected_manufacturer(client):
    file_data = io.BytesIO(b"Fake PDF Content")
    reg_resp = client.post(
        "/api/auth/manufacturer/register",
        data={
            "company_name": "Rejected Mfr Ltd",
            "GSTIN": "27ABCDE1234F1Z5",
            "company_address": "Pune",
            "phone": "+919876543219",
            "email": "rejected@mfr.com",
            "password": "Password123!"
        },
        files={"verification_document": ("doc.pdf", file_data, "application/pdf")}
    )
    mfr_id = reg_resp.json()["manufacturer_id"]

    # Admin rejects manufacturer
    admin_token = client.post("/api/auth/login", json={
        "email": settings.ADMIN_EMAIL,
        "password": settings.ADMIN_PASSWORD
    }).json()["access_token"]
    client.put(
        f"/api/admin/manufacturers/{mfr_id}/status",
        json={"status": "REJECTED", "rejection_reason": "Incomplete documentation"},
        headers={"Authorization": f"Bearer {admin_token}"}
    )

    # Rejected manufacturer login
    mfr_token = client.post("/api/auth/login", json={
        "email": "rejected@mfr.com",
        "password": "Password123!"
    }).json()["access_token"]

    test_resp = client.get("/api/manufacturer/test", headers={"Authorization": f"Bearer {mfr_token}"})
    assert test_resp.status_code == 403

# Test 8: Suspended manufacturer
def test_8_suspended_manufacturer(client):
    file_data = io.BytesIO(b"Fake PDF Content")
    reg_resp = client.post(
        "/api/auth/manufacturer/register",
        data={
            "company_name": "Suspended Mfr Ltd",
            "GSTIN": "27AAACA9999A1Z5",
            "company_address": "Nagpur",
            "phone": "+919876543220",
            "email": "suspended@mfr.com",
            "password": "Password123!"
        },
        files={"verification_document": ("doc.pdf", file_data, "application/pdf")}
    )
    mfr_id = reg_resp.json()["manufacturer_id"]

    # Admin suspends manufacturer
    admin_token = client.post("/api/auth/login", json={
        "email": settings.ADMIN_EMAIL,
        "password": settings.ADMIN_PASSWORD
    }).json()["access_token"]
    client.put(
        f"/api/admin/manufacturers/{mfr_id}/status",
        json={"status": "SUSPENDED"},
        headers={"Authorization": f"Bearer {admin_token}"}
    )

    # Suspended manufacturer login attempt on protected endpoint -> 403
    mfr_token = client.post("/api/auth/login", json={
        "email": "suspended@mfr.com",
        "password": "Password123!"
    }).json()["access_token"]

    test_resp = client.get("/api/manufacturer/test", headers={"Authorization": f"Bearer {mfr_token}"})
    assert test_resp.status_code == 403

# Test 9: Admin-only endpoint protection
def test_9_admin_only_endpoint_protection(client):
    # Unauthenticated -> 401
    assert client.get("/api/admin/test").status_code == 401

    # Manufacturer -> 403
    file_data = io.BytesIO(b"Fake PDF Content")
    client.post(
        "/api/auth/manufacturer/register",
        data={
            "company_name": "Mfr For Admin Check",
            "GSTIN": "07AAACA1234A1Z5",
            "company_address": "Delhi",
            "phone": "+919876543213",
            "email": "mfr_admin_check@test.com",
            "password": "Password123!"
        },
        files={"verification_document": ("doc.pdf", file_data, "application/pdf")}
    )
    mfr_token = client.post("/api/auth/login", json={
        "email": "mfr_admin_check@test.com",
        "password": "Password123!"
    }).json()["access_token"]
    assert client.get("/api/admin/test", headers={"Authorization": f"Bearer {mfr_token}"}).status_code == 403

    # Admin -> 200
    admin_token = client.post("/api/auth/login", json={
        "email": settings.ADMIN_EMAIL,
        "password": settings.ADMIN_PASSWORD
    }).json()["access_token"]
    assert client.get("/api/admin/test", headers={"Authorization": f"Bearer {admin_token}"}).status_code == 200

# Test 10: Manufacturer-only endpoint protection
def test_10_manufacturer_only_endpoint_protection(client):
    # Unauthenticated -> 401
    assert client.get("/api/manufacturer/test").status_code == 401

    # Admin cannot access manufacturer-only endpoint -> 403
    admin_token = client.post("/api/auth/login", json={
        "email": settings.ADMIN_EMAIL,
        "password": settings.ADMIN_PASSWORD
    }).json()["access_token"]
    assert client.get("/api/manufacturer/test", headers={"Authorization": f"Bearer {admin_token}"}).status_code == 403

# Test 11: Public endpoint without JWT
def test_11_public_endpoint_without_jwt(client):
    resp = client.get("/api/public/test")
    assert resp.status_code == 200
    assert resp.json()["authenticated"] is False

# Test 12: Invalid / Expired JWT
def test_12_invalid_or_expired_jwt(client):
    resp = client.get("/api/auth/me", headers={"Authorization": "Bearer invalid_jwt_token_xyz_123"})
    assert resp.status_code == 401

# Test 13: Inactive user
def test_13_inactive_user(client):
    from tests.conftest import TestingSessionLocal
    # Deactivate admin user
    db = TestingSessionLocal()
    admin_user = db.query(User).filter(User.email == settings.ADMIN_EMAIL).first()
    admin_user.is_active = False
    db.commit()
    db.close()

    # Attempt login -> 401
    resp = client.post("/api/auth/login", json={
        "email": settings.ADMIN_EMAIL,
        "password": settings.ADMIN_PASSWORD
    })
    assert resp.status_code == 401

# Test 14: Duplicate email
def test_14_duplicate_email(client):
    file_data = io.BytesIO(b"Fake PDF Content")
    payload = {
        "company_name": "Dup Email Mfr",
        "GSTIN": "27AAACA5555A1Z5",
        "company_address": "Mumbai",
        "phone": "+919876543215",
        "email": "dupemail@test.com",
        "password": "Password123!"
    }
    resp1 = client.post("/api/auth/manufacturer/register", data=payload, files={"verification_document": ("doc.pdf", file_data, "application/pdf")})
    assert resp1.status_code == 201

    payload["GSTIN"] = "27AAACA6666A1Z5" # Different GSTIN, same email
    file_data_2 = io.BytesIO(b"Fake PDF Content")
    resp2 = client.post("/api/auth/manufacturer/register", data=payload, files={"verification_document": ("doc.pdf", file_data_2, "application/pdf")})
    assert resp2.status_code == 400
    assert "already registered" in resp2.json()["detail"]

# Test 15: Duplicate GSTIN
def test_15_duplicate_gstin(client):
    file_data = io.BytesIO(b"Fake PDF Content")
    payload = {
        "company_name": "Dup GSTIN Mfr",
        "GSTIN": "27AAACA7777A1Z5",
        "company_address": "Mumbai",
        "phone": "+919876543216",
        "email": "mfr_gstin1@test.com",
        "password": "Password123!"
    }
    resp1 = client.post("/api/auth/manufacturer/register", data=payload, files={"verification_document": ("doc.pdf", file_data, "application/pdf")})
    assert resp1.status_code == 201

    payload["email"] = "mfr_gstin2@test.com" # Different email, same GSTIN
    file_data_2 = io.BytesIO(b"Fake PDF Content")
    resp2 = client.post("/api/auth/manufacturer/register", data=payload, files={"verification_document": ("doc.pdf", file_data_2, "application/pdf")})
    assert resp2.status_code == 400
    assert "GSTIN" in resp2.json()["detail"]

# Test 16: Invalid GSTIN
def test_16_invalid_gstin(client):
    file_data = io.BytesIO(b"Fake PDF Content")
    resp = client.post(
        "/api/auth/manufacturer/register",
        data={
            "company_name": "Bad GSTIN Ltd",
            "GSTIN": "INVALID_GSTIN_123",
            "company_address": "Mumbai",
            "phone": "+919876543217",
            "email": "badgstin@test.com",
            "password": "Password123!"
        },
        files={"verification_document": ("doc.pdf", file_data, "application/pdf")}
    )
    assert resp.status_code == 400
    assert "Invalid GSTIN format" in resp.json()["detail"]

# Test 17: Invalid document type
def test_17_invalid_document_type(client):
    file_data = io.BytesIO(b"Executable Binary Content")
    resp = client.post(
        "/api/auth/manufacturer/register",
        data={
            "company_name": "Bad File Mfr",
            "GSTIN": "27AAACA8888A1Z5",
            "company_address": "Mumbai",
            "phone": "+919876543218",
            "email": "badfile@test.com",
            "password": "Password123!"
        },
        files={"verification_document": ("malicious.exe", file_data, "application/octet-stream")}
    )
    assert resp.status_code == 400
    assert "Allowed document types" in resp.json()["detail"]

# Test 18: Oversized document
def test_18_oversized_document(client):
    large_file_data = io.BytesIO(b"0" * (6 * 1024 * 1024)) # 6MB
    resp = client.post(
        "/api/auth/manufacturer/register",
        data={
            "company_name": "Large File Mfr",
            "GSTIN": "27AAACA1111A1Z5",
            "company_address": "Mumbai",
            "phone": "+919876543221",
            "email": "largefile@test.com",
            "password": "Password123!"
        },
        files={"verification_document": ("big_doc.pdf", large_file_data, "application/pdf")}
    )
    assert resp.status_code == 400
    assert "exceeds maximum limit" in resp.json()["detail"]
