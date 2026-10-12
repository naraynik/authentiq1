# 🎯 AuthentiQ Quick Reference

## ⚡ Fastest Way to Get Started

### Windows
```cmd
.\setup.bat
```

### macOS/Linux
```bash
bash setup.sh
```

### With Docker (Any OS)
```bash
docker-compose -f docker-compose.full.yml up --build
```

---

## 🔧 Common Commands

### Project Setup
| Command | Purpose |
|---------|---------|
| `make install` | Install all dependencies |
| `make train-models` | Train RF + GNN models |
| `make db-up` | Start PostgreSQL |
| `make docker-up` | Start entire Docker stack |
| `make clean` | Remove node_modules, venv, etc. |

### Development Services
| Command | Purpose |
|---------|---------|
| `make start-backend` | Run FastAPI (port 8000) |
| `make start-frontend` | Run Next.js (port 3000) |
| `make start-blockchain` | Run Hardhat node (port 8545) |

### Database
| Command | Purpose |
|---------|---------|
| `make db-up` | Start PostgreSQL (port 5432) |
| `make db-down` | Stop PostgreSQL |

---

## 🌐 Access Points

| Service | URL | Purpose |
|---------|-----|---------|
| Frontend | http://localhost:3000 | Register & scan products |
| API Docs | http://localhost:8000/docs | Swagger UI |
| Database | localhost:5432 | PostgreSQL |
| Blockchain | http://localhost:8545 | Hardhat node |

---

## 📝 Environment Setup

### First Time: Create `.env` in root
```bash
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/authentiq
RPC_URL=http://localhost:8545
CONTRACT_ADDRESS=0x9fE46736679d2D9a65F0992F2272dE9f3c7fa6e0
RF_MODEL_PATH=app/models/rf_model.joblib
GNN_MODEL_PATH=app/models/gnn_model.pt
API_PORT=8000
FRONTEND_URL=http://localhost:3000
```

---

## 🚀 First Deployment Steps

### 1. Install Dependencies
```bash
cd ai-engine && pip install -r requirements.txt && cd ..
cd backend && pip install -r requirements.txt && cd ..
cd blockchain && npm install && cd ..
cd frontend && npm install && cd ..
```

### 2. Start Database
```bash
docker-compose -f docker-compose.dev.yml up -d
```

### 3. Train Models
```bash
cd ai-engine
python train.py
```

### 4. Start Services (in separate terminals)
```bash
# Terminal 1: Blockchain
cd blockchain && npm run node

# Terminal 2: Deploy Contracts
cd blockchain && npm run deploy:local

# Terminal 3: Backend
cd backend && uvicorn app.main:app --reload

# Terminal 4: Frontend
cd frontend && npm run dev
```

---

## 🧪 Quick Test

```bash
# Register a product
curl -X POST http://localhost:8000/api/register \
  -H "Content-Type: application/json" \
  -d '{
    "product_id": "TEST-001",
    "name": "Test Product",
    "batch_number": "TEST-BATCH",
    "production_location": "Test Lab"
  }'

# Verify the product
curl -X POST http://localhost:8000/api/verify \
  -H "Content-Type: application/json" \
  -d '{
    "product_id": "TEST-001",
    "location": "Test Location",
    "scan_velocity": 1,
    "hours_since_creation": 24
  }'
```

---

## 📂 Key Files to Edit

| File | Purpose |
|------|---------|
| `backend/app/main.py` | Add API endpoints |
| `backend/app/ai_client.py` | Modify ML inference logic |
| `frontend/src/app/page.tsx` | Edit homepage UI |
| `AuthentiQ-Blockchain-main/contracts/ProductVerification.sol` | Update smart contract |
| `ai-engine/train.py` | Retrain models |

---

## 🐛 Troubleshooting

| Problem | Solution |
|---------|----------|
| **Port 3000/8000 in use** | `make clean` or change port in .env |
| **Database won't connect** | `make db-up` to start PostgreSQL |
| **Models not loading** | `cd ai-engine && python train.py` |
| **Contract not deployed** | `cd ../AuthentiQ-Blockchain-main && npm run deploy:local` |
| **CORS errors** | Check FRONTEND_URL in backend .env |
| **Fresh start** | `make clean && make install` |

---

## 📊 Project Structure Cheat Sheet

```
ai-engine/        → Train RF + GNN models
backend/          → FastAPI (main logic)
  ├── app/
  │   ├── main.py → Routes
  │   ├── ai_client.py → Model inference (RF + GNN)
  │   ├── blockchain_client.py → Web3
  │   ├── database.py → SQLAlchemy ORM
  │   └── models.py → DB models
AuthentiQ-Blockchain-main/ → Canonical smart contract workspace
  ├── contracts/ProductVerification.sol → AccessControl & Provenance
frontend/         → Next.js UI
  └── src/app/ → Pages
infrastructure/   → Docker configs
```

---

## 🔑 Key Concepts

### Random Forest Model
- **When**: Real-time individual product verification
- **Input**: scan_velocity, hours_since_creation, is_location_anomaly
- **Output**: authenticity_probability (0-1)
- **Speed**: ~8ms
- **Use**: First-pass quick check

### GNN Model
- **When**: Network-level counterfeiting detection
- **Input**: Product network (nodes, edges, features)
- **Output**: Network authenticity scores, ring detection
- **Speed**: ~50ms
- **Use**: Catch organized counterfeiting operations

### Smart Contract
- **Type**: ERC-721 NFT
- **Function**: Store immutable product record on blockchain
- **Update**: Records scans, updates status (Secured→Suspicious→Compromised)
- **Chain**: Local Hardhat (development) or Polygon/Ethereum (production)

---

## 🚢 Production Checklist

- [ ] Set `ENVIRONMENT=production` in `.env`
- [ ] Use managed PostgreSQL (AWS RDS, etc.)
- [ ] Deploy to public blockchain (Polygon, Ethereum)
- [ ] Set restrictive CORS policy
- [ ] Enable HTTPS/TLS
- [ ] Setup monitoring & alerting
- [ ] Database backups enabled
- [ ] Environment variables secured (not in code)
- [ ] Smart contract audited
- [ ] Load tested backend

---

## 📚 Documentation Files

| File | Read For |
|------|----------|
| `README.md` | Project overview |
| `SETUP.md` | Detailed setup instructions |
| `TESTING.md` | API examples & testing |
| `DEPENDENCIES.md` | All packages used |
| `Makefile` | Available commands |

---

## 💡 Tips & Tricks

### View API in Browser
```
http://localhost:8000/docs
```
(Auto-generated Swagger documentation)

### Check Database Directly
```bash
psql -U postgres -d authentiq -h localhost
SELECT * FROM products;
SELECT * FROM scan_history;
```

### Clear Everything & Start Fresh
```bash
make clean
docker-compose -f docker-compose.dev.yml down -v
rm -rf blockchain/artifacts blockchain/cache
```

### Fast Model Retraining
```bash
cd ai-engine
python train.py  # Takes ~35 seconds
```

### Deploy Contract Locally
```bash
cd blockchain
npm run deploy:local  # Outputs contract address
```

---

## 🎓 Learning Resources

- **FastAPI**: https://fastapi.tiangolo.com/
- **PyTorch Geometric**: https://pytorch-geometric.readthedocs.io/
- **Hardhat**: https://hardhat.org/
- **Next.js**: https://nextjs.org/
- **Solidity**: https://docs.soliditylang.org/
- **SQLAlchemy**: https://docs.sqlalchemy.org/

---

## ✨ Pro Tips

1. **Keep three terminals open**: Blockchain + Backend + Frontend
2. **Use Swagger UI for quick testing**: http://localhost:8000/docs
3. **Watch model inference in logs**: Shows RF vs GNN scores
4. **Test with different `scan_velocity` values**: To see detection in action
5. **Monitor blockchain transactions**: https://hardhat.org/geth-methods

---

**Need help?** Check main [README.md](README.md)

