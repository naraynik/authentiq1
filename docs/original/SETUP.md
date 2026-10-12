# 🚀 AuthentiQ Setup Guide

## Quick Start (5 minutes with Docker)

### Prerequisites
- Docker & Docker Compose installed
- Node.js 18+ (for blockchain compilation)
- Python 3.10+ (for AI training)

### Option A: Full Stack (Docker)
```bash
docker-compose -f docker-compose.full.yml up --build
```
This starts: PostgreSQL + Backend + Blockchain + Frontend (all services)

### Option B: Local Development Setup

#### 1. Start Database
```bash
docker-compose -f docker-compose.dev.yml up
# Or use local PostgreSQL
```

#### 2. Install Dependencies
```bash
# AI Engine
cd ai-engine
pip install -r requirements.txt

# Backend
cd ../backend
pip install -r requirements.txt

# Blockchain
cd ../blockchain
npm install

# Frontend
cd ../frontend
npm install
```

#### 3. Train AI Models
```bash
cd ai-engine
python train.py
# Output: rf_model.joblib and gnn_model.pt in backend/app/models/
```

#### 4. Start Blockchain Locally
```bash
cd blockchain
npm run node
# Runs Hardhat node at http://localhost:8545
```

#### 5. Deploy Contracts (in new terminal)
```bash
cd ../AuthentiQ-Blockchain-main
npm run deploy:local
# Deploys ProductVerification.sol, exports ABI & address
```

#### 6. Start Backend API (in new terminal)
```bash
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
# UI: http://localhost:8000/docs (Swagger)
```

#### 7. Start Frontend (in new terminal)
```bash
cd frontend
npm run dev
# Opens http://localhost:3000
```

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                     FRONTEND (Next.js)                          │
│  - Register products (form)                                     │
│  - Scan QR codes (html5-qrcode)                                 │
│  - View verification results                                    │
└────────────────────┬──────────────────────────────────────────┘
                     │ HTTP/REST
┌────────────────────▼──────────────────────────────────────────┐
│                  BACKEND (FastAPI)                             │
│  ┌─────────────────────────────────────────────────────────┐  │
│  │ POST /api/register     → DB + Blockchain               │  │
│  │ POST /api/verify       → AI (RF+GNN) + Blockchain      │  │
│  │ GET  /api/product/:id  → Product history               │  │
│  └─────────────────────────────────────────────────────────┘  │
│           ▲                          ▲                         │
│           │                          │                         │
│    ┌──────┴─────┐           ┌────────┴──────────┐             │
│    │             │           │                   │             │
└────┼─────────────┼───────────┼───────────────────┼─────────────┘
     │             │           │                   │
┌────▼────┐  ┌─────▼──┐  ┌────▼─────┐      ┌─────▼──────┐
│ PostgreSQL   Random Forest   GNN       Smart Contracts
│ Database     Model       Network Model  Blockchain
│              (RF)        (PyTorch)      (Solidity)
└──────────┘  └─────────┘  └───────────┘      └───────────┘
```

---

## Environment Variables

Root `.env` file contains:
- `DATABASE_URL` - PostgreSQL connection
- `RPC_URL` - Blockchain node (Hardhat)
- `CONTRACT_ADDRESS` - Deployed smart contract
- `RF_MODEL_PATH` - Random Forest model
- `GNN_MODEL_PATH` - GNN model
- `API_PORT` - Backend port (default: 8000)

---

## Testing the System

### 1. Register a Product
```bash
curl -X POST http://localhost:8000/api/register \
  -H "Content-Type: application/json" \
  -d '{
    "product_id": "PROD-001",
    "name": "Luxury Watch",
    "batch_number": "LW-2026-001",
    "production_location": "Switzerland"
  }'
```

### 2. Verify a Scan
```bash
curl -X POST http://localhost:8000/api/verify \
  -H "Content-Type: application/json" \
  -d '{
    "product_id": "PROD-001",
    "location": "Retail Store NYC",
    "scan_velocity": 2,
    "hours_since_creation": 48,
    "product_network": null
  }'
```

### 3. Check Swagger UI
Visit: http://localhost:8000/docs

---

## Common Issues & Solutions

### ❌ "ModuleNotFoundError: No module named 'torch_geometric'"
**Fix:** Run `pip install torch-geometric` in backend folder

### ❌ "Connection refused: localhost:5432"
**Fix:** Start PostgreSQL: `docker-compose -f docker-compose.dev.yml up`

### ❌ "Contract not found at 0x..."
**Fix:** Deploy: `cd blockchain && npm run deploy:local`

### ❌ Models not loading
**Fix:** Train: `cd ai-engine && python train.py`

---

## File Structure After Setup

```
AUTHENIC/
├── .env                          ← Root config
├── ai-engine/
│   ├── train.py                  ← Run this to train models
│   └── requirements.txt           ← AI dependencies
├── backend/
│   ├── app/
│   │   ├── models/               ← Trained models stored here
│   │   ├── main.py               ← FastAPI app
│   │   ├── ai_client.py          ← Dual model inference
│   │   └── blockchain_client.py  ← Web3 integration
│   └── requirements.txt           ← Backend dependencies
├── AuthentiQ-Blockchain-main/     ← Canonical smart contract workspace
│   ├── contracts/
│   │   └── ProductVerification.sol← Smart contract (AccessControl & Batching)
│   ├── scripts/
│   │   ├── deploy.js              ← Deployment script
│   │   └── exportArtifacts.js     ← ABI export to backend
│   └── package.json               ← Hardhat dependencies
├── frontend/
│   ├── src/
│   │   ├── app/page.tsx          ← Home page
│   │   ├── app/register/         ← Registration
│   │   └── app/globals.css       ← Styling
│   ├── package.json              ← Frontend dependencies
│   └── .env.local                ← Frontend config
└── infrastructure/
    ├── Dockerfile.backend        ← Backend container
    ├── Dockerfile.frontend       ← Frontend container
    └── Dockerfile.hardhat        ← Blockchain container
```

---

## Production Deployment

### Using Docker Compose
```bash
# Build all images
docker-compose -f docker-compose.full.yml build

# Start all services
docker-compose -f docker-compose.full.yml up -d

# View logs
docker-compose -f docker-compose.full.yml logs -f backend
```

### Manual Deployment
1. Set production environment variables in `.env.production`
2. Deploy PostgreSQL to managed service (AWS RDS, etc.)
3. Deploy smart contracts to public blockchain (Ethereum, Polygon)
4. Deploy backend to cloud (AWS, GCP, Azure)
5. Deploy frontend to Vercel or similar

---

## API Endpoints Reference

| Method | Endpoint | Purpose |
|--------|----------|---------|
| GET | `/` | Health check |
| POST | `/api/register` | Register product on blockchain |
| POST | `/api/verify` | Verify product authenticity |
| GET | `/api/product/{id}` | Get product history |
| GET | `/docs` | Swagger documentation |

---

## Next Steps

- [ ] Start with Option A or B above
- [ ] Register a test product
- [ ] Scan and verify
- [ ] Check blockchain transaction
- [ ] Review AI model scores in response
- [ ] Deploy to production

**Questions?** Check the backend logs: `docker-compose logs backend`

