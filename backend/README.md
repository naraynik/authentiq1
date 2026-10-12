# 🚀 AuthentiQ Unified Backend Gateway

The **AuthentiQ Unified Backend** is a high-performance, asynchronous FastAPI application that unifies Relational Persistence, Role-Based Access Control, Manufacturer Verification Governance, AI Anomaly Detection, and EVM Blockchain Provenance.

---

## 🏗️ Architectural Overview

```
backend/
├── app/
│   ├── main.py                  # FastAPI Application Gateway
│   ├── core/                    # Settings & Hashing Security & Dependencies
│   ├── database/                # Database Engine & ORM Base
│   ├── models/                  # 6 Core SQLAlchemy Models
│   ├── schemas/                 # Pydantic Request/Response Schemas
│   ├── routers/                 # API Endpoints (Health, Auth, Admin, Mfr, Products, Verify, Public)
│   └── services/                # Audit Logging & Business Logic Services
├── alembic/                     # Database Migrations Management
├── uploads/                     # Secure Non-Public Verification Document Storage
├── scripts/                     # Operational & Verification Scripts
├── tests/                       # Automated Pytest Suite (33 Test Cases)
├── requirements.txt
├── .env.example
└── README.md
```

---

## 💾 Database Schema

1. **`users`**: Platform accounts (`ADMIN`, `MANUFACTURER`).
2. **`manufacturers`**: Company profile, GSTIN, verification status (`PENDING`, `APPROVED`, `REJECTED`, `SUSPENDED`), verifier details, and timestamps.
3. **`products`**: Product passports, supply chain target route, on-chain hash.
4. **`scan_history`**: Audit trail of every public QR verification with AI anomaly scores & location metrics.
5. **`location_history`**: Immutable supply chain provenance audit log.
6. **`audit_logs`**: Platform security & administrative action logs (`MANUFACTURER_APPROVED`, `MANUFACTURER_REJECTED`, `MANUFACTURER_SUSPENDED`).

---

## 🛠️ Quick Start & Testing

```bash
# 1. Install Dependencies
pip install -r requirements.txt

# 2. Run Database Migrations
python -m alembic upgrade head

# 3. Seed Admin Credentials
python -m app.seed_admin

# 4. Run Automated Test Suite (33 Tests)
python -m pytest -v

# 5. Start Backend Server
python -m uvicorn app.main:app --reload --port 8000
```

* **Interactive API Docs**: http://localhost:8000/docs
* **Health Check**: http://localhost:8000/api/health
