# PHASE 3 — MANUFACTURER VERIFICATION & MANAGEMENT DOCUMENTATION

## 1. Overview & Purpose

Phase 3 implements an Admin-controlled governance workflow for validating and managing pharmaceutical & brand manufacturer accounts within the AuthentiQ Anti-Counterfeit Platform. 

To maintain supply chain integrity, registered manufacturers must be thoroughly vetted by platform Administrators before they are granted permission to create product passports or register items on the EVM blockchain.

---

## 2. Manufacturer Status Workflow

```
[ New Registration ]
         │
         ▼
    ( PENDING ) ──► Cannot access protected manufacturer endpoints
         │
    Admin Review
     ┌───┴───┐
     ▼       ▼
( APPROVED )  ( REJECTED ) ──► Access permanently blocked (with reason)
     │
Admin Audit
     ▼
( SUSPENDED ) ──► Access temporarily frozen pending investigation
```

### Status Definitions & Permissions

1. **`PENDING`**: Initial state upon registration. User can log in and view their company profile (`GET /api/manufacturer/profile`), but calls to protected manufacturer operations (`POST /api/products/register` or protected business routes) are rejected with `HTTP 403 Forbidden`.
2. **`APPROVED`**: Granted after explicit Admin review. Full access to protected manufacturer operations and product registration.
3. **`REJECTED`**: Set by Admin if verification documents or GSTIN details fail compliance checks. Requires storing an explicit `rejection_reason`. All protected manufacturer access is blocked (`HTTP 403 Forbidden`).
4. **`SUSPENDED`**: Set by Admin if an approved manufacturer is flagged for audit or supply chain anomalies. Protected operations are immediately blocked (`HTTP 403 Forbidden`). Re-review back to `APPROVED` or `REJECTED` is supported by explicit Admin action.

---

## 3. API Endpoints Reference

### Admin Governance APIs (`/api/admin`)

* **`GET /api/admin/manufacturers`**: Returns list of all registered manufacturers. Supports query filters: `status`, `company_name`, `gstin`, `email`.
* **`GET /api/admin/manufacturers/{manufacturer_id}`**: Retrieves comprehensive manufacturer profile for Admin inspection.
* **`GET /api/admin/manufacturers/{manufacturer_id}/document`**: Secure Admin-only file stream/download for viewing compliance documents. Protected against path traversal attacks (`HTTP 403`).
* **`PUT /api/admin/manufacturers/{manufacturer_id}/status`**: Approves, rejects, or suspends a manufacturer. Records timestamp (`verified_at`), reviewer ID (`verified_by`), rejection reason, and writes an immutable audit log entry.

### Manufacturer Self-Service APIs (`/api/manufacturer`)

* **`GET /api/manufacturer/profile`**: Allows an authenticated manufacturer to view ONLY their own company profile and status. Enforces strict IDOR protection and excludes password hashes/secrets.

---

## 4. Security & Audit Logging

* **Document Storage Security**: Uploaded files (`.pdf`, `.png`, `.jpg`, `.jpeg`, <= 5MB) are assigned UUID filenames and stored in `uploads/documents/` outside public web directories. File access requires Admin authentication.
* **Audit Logging**: Every status transition automatically writes an entry to the `audit_logs` table (`MANUFACTURER_APPROVED`, `MANUFACTURER_REJECTED`, `MANUFACTURER_SUSPENDED`), capturing the action, Admin ID, target manufacturer ID, description, and client IP address.

---

## 5. Automated Testing

Run the full Phase 1, Phase 2, and Phase 3 test suite:

```bash
cd backend
python -m pytest -v
```

All 33 automated tests pass cleanly covering status transitions, filter queries, document security, IDOR protection, and audit logging.
