"""Tests for the endpoints added for the AuthentiQ web frontend (see CHANGES.md)."""
import importlib.util
from unittest.mock import patch

from fastapi.testclient import TestClient

from app.services.blockchain_service import blockchain_service
from tests.test_phase4 import get_admin_token, register_and_approve_manufacturer

NASHIK = {"lat": 20.0, "lon": 73.78}
PRODUCT = {
    "product_name": "Herbal Green Tea 100 g",
    "batch_number": "B-0427",
    "sku": "HGT-100",
    "manufacturing_date": "2026-01-01T00:00:00",
    "facility": {"street": "MIDC Satpur", "city": "Nashik", "country": "India", **NASHIK},
    "distributors": [
        {"name": "Godavari Traders", "street": "College Road", "city": "Nashik", "country": "India", **NASHIK}
    ],
}


def _register(client: TestClient, token: str, **extra) -> dict:
    with patch.object(blockchain_service, "register_product") as mock_reg, patch.object(
        blockchain_service, "verify_product"
    ) as mock_verify:
        mock_reg.return_value = {"success": True, "transaction_hash": "0xabc", "block_number": 7}
        res = client.post(
            "/api/products/register",
            json={**PRODUCT, **extra},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert res.status_code == 201, res.text
        body = res.json()
        mock_verify.return_value = {
            "product_id": body["product_id"],
            "product_hash": body["product_hash"],
            "status": "GENUINE",
        }
    return body


def _report(client: TestClient, product_hash: str, **payload) -> dict:
    with patch.object(blockchain_service, "verify_product") as mock_verify:
        mock_verify.side_effect = lambda pid: {"product_id": pid, "product_hash": product_hash, "status": "GENUINE"}
        res = client.post("/api/verify/report", json=payload)
    assert res.status_code == 200, res.text
    return res.json()


def test_register_with_structured_fields_and_list_mine(client: TestClient):
    token, _ = register_and_approve_manufacturer(client, "web1@example.com", "27AAACA1234A1Z5")
    body = _register(client, token)
    assert body["product_id"].startswith("AQ-")  # generated when not given

    mine = client.get("/api/products/mine", headers={"Authorization": f"Bearer {token}"})
    assert mine.status_code == 200
    [p] = mine.json()
    assert p["sku"] == "HGT-100"
    assert p["distributors"][0]["name"] == "Godavari Traders"
    assert p["registration_block"] == 7
    assert "Nashik" in p["current_location"] and "Godavari Traders" in p["next_location"]


def test_original_payload_still_works(client: TestClient):
    token, _ = register_and_approve_manufacturer(client, "web2@example.com", "27AAACA1234A1Z6")
    legacy = {
        "product_id": "LEGACY-1",
        "product_name": "Widget",
        "batch_number": "B1",
        "manufacturing_date": "2026-01-01T00:00:00",
        "current_location": "Factory",
        "next_location": "Warehouse",
    }
    with patch.object(blockchain_service, "register_product") as mock_reg:
        mock_reg.return_value = {"success": True, "transaction_hash": "0x1"}
        res = client.post("/api/products/register", json=legacy, headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 201, res.text
    assert res.json()["product_id"] == "LEGACY-1"


def test_report_genuine_then_copied_code(client: TestClient):
    token, _ = register_and_approve_manufacturer(client, "web3@example.com", "27AAACA1234A1Z7")
    body = _register(client, token, product_id="AQ-TEST-1")

    first = _report(client, body["product_hash"], product_id="aq-test-1", latitude=20.0, longitude=73.79)
    assert first["found"] is True
    assert first["product"]["product_id"] == "AQ-TEST-1"  # case-insensitive match
    assert first["verification"]["blockchain_verified"] is True
    assert first["scan"]["final_verdict"] == "GENUINE"
    assert first["scan"]["models_used"]["random_forest"] is True
    if importlib.util.find_spec("torch_geometric"):
        assert first["scan"]["models_used"]["gnn"] is True

    # Same code a moment later in London: impossible travel and far from the distributor.
    second = _report(client, body["product_hash"], product_id="AQ-TEST-1", latitude=51.5, longitude=-0.12)
    assert second["scan"]["final_verdict"] == "COUNTERFEIT"
    flags = second["scan"]["flags"]
    assert any("Impossible Travel" in f for f in flags)
    assert any("Registered Distributor" in f for f in flags)
    assert len(second["history"]) == 2


def test_report_unshared_location_is_not_a_different_place(client: TestClient):
    token, _ = register_and_approve_manufacturer(client, "web4@example.com", "27AAACA1234A1Z8")
    body = _register(client, token, product_id="AQ-TEST-2")
    _report(client, body["product_hash"], product_id="AQ-TEST-2", latitude=20.0, longitude=73.79)
    again = _report(client, body["product_hash"], product_id="AQ-TEST-2")
    assert not any("Impossible Travel" in f for f in again["scan"]["flags"])


def test_report_unknown_code(client: TestClient):
    res = client.post("/api/verify/report", json={"product_id": "NOT-A-CODE"})
    assert res.status_code == 200
    assert res.json()["found"] is False


def test_issues_public_create_and_admin_list(client: TestClient):
    res = client.post("/api/issues", json={"product_id": "NOT-A-CODE", "message": "Seal was broken"})
    assert res.status_code == 201, res.text
    assert res.json()["registered_product"] is False

    assert client.get("/api/admin/issues").status_code == 401
    admin = get_admin_token(client)
    listed = client.get("/api/admin/issues", headers={"Authorization": f"Bearer {admin}"})
    assert listed.status_code == 200
    assert listed.json()[0]["message"] == "Seal was broken"


def test_aadhaar_document_is_served_from_the_database(client: TestClient):
    """Hosts like Render wipe the disk on restart, so the file must come from the DB."""
    import os

    from app.core.config import settings

    _, mfr_id = register_and_approve_manufacturer(client, "web5@example.com", "27AAACA1234A1Z9")
    for name in os.listdir(settings.UPLOAD_DIR):  # simulate a wiped disk
        os.remove(os.path.join(settings.UPLOAD_DIR, name))
    admin = get_admin_token(client)
    res = client.get(f"/api/admin/manufacturers/{mfr_id}/document", headers={"Authorization": f"Bearer {admin}"})
    assert res.status_code == 200
    assert res.headers["content-type"] == "application/pdf"
    assert res.content.startswith(b"%PDF")
