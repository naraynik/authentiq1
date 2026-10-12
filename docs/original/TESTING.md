# 🧪 AuthentiQ Testing & Development Guide

## Testing Strategy

### Unit Tests
```bash
# Run backend tests
cd backend
pytest tests/ -v

# Run blockchain tests
cd ../blockchain
npm run test
```

### Integration Tests
```bash
# Test full register → verify flow
bash test-integration.sh
```

### Manual Testing (Postman/cURL)

---

## API Testing Examples

### 1. Register a Product

**cURL:**
```bash
curl -X POST http://localhost:8000/api/register \
  -H "Content-Type: application/json" \
  -d '{
    "product_id": "PROD-2026-001",
    "name": "Premium Leather Bag",
    "batch_number": "PLB-Q1-2026",
    "production_location": "Italy"
  }'
```

**Python:**
```python
import requests

response = requests.post(
    "http://localhost:8000/api/register",
    json={
        "product_id": "PROD-2026-001",
        "name": "Premium Leather Bag",
        "batch_number": "PLB-Q1-2026",
        "production_location": "Italy"
    }
)
print(response.json())
```

**Expected Response:**
```json
{
  "message": "Product successfully cataloged and registered.",
  "db_record": {
    "id": 1,
    "product_id": "PROD-2026-001",
    "name": "Premium Leather Bag",
    "registered_at": "2026-07-13T10:30:00"
  },
  "blockchain_receipt": {
    "transaction_hash": "0x...",
    "block_number": 5,
    "status": "success"
  }
}
```

---

### 2. Verify a Product (Authentic)

**cURL:**
```bash
curl -X POST http://localhost:8000/api/verify \
  -H "Content-Type: application/json" \
  -d '{
    "product_id": "PROD-2026-001",
    "location": "Fifth Avenue Boutique, NYC",
    "scan_velocity": 1,
    "hours_since_creation": 72,
    "product_network": null
  }'
```

**Expected Response (Authentic):**
```json
{
  "status": "authentic",
  "message": "AUTHENTIC: Product is verified on-chain and scan patterns are standard.",
  "ai_metrics": {
    "authenticity_probability": 0.96,
    "anomaly_score": 0.04,
    "flags": [],
    "model_scores": {
      "random_forest": {
        "authenticity_prob": 0.96,
        "counterfeit_prob": 0.04
      },
      "gnn_network": null
    }
  },
  "blockchain_receipt": {
    "status": "authentic",
    "scan_count": 1,
    "last_scan_location": "Fifth Avenue Boutique, NYC",
    "transaction_hash": "0x..."
  }
}
```

---

### 3. Verify a Product (Counterfeit - High Velocity)

**cURL:**
```bash
curl -X POST http://localhost:8000/api/verify \
  -H "Content-Type: application/json" \
  -d '{
    "product_id": "PROD-2026-001",
    "location": "Street Market, Tokyo",
    "scan_velocity": 15,
    "hours_since_creation": 24,
    "product_network": null
  }'
```

**Expected Response (Counterfeit):**
```json
{
  "status": "counterfeit",
  "message": "SUSPICIOUS: Verification matches blockchain keys, but scan metrics flag anomaly. Potential cloned QR code.",
  "ai_metrics": {
    "authenticity_probability": 0.22,
    "anomaly_score": 0.78,
    "flags": [
      "High Scan Frequency",
      "Pre-mature Scan Sequence",
      "Geographical Velocity Violation"
    ],
    "model_scores": {
      "random_forest": {
        "authenticity_prob": 0.22,
        "counterfeit_prob": 0.78
      },
      "gnn_network": null
    }
  },
  "blockchain_receipt": {
    "status": "suspicious",
    "status_verdict": 1,
    "scan_count": 2,
    "transaction_hash": "0x..."
  }
}
```

---

### 4. Network-Level Detection (GNN)

**cURL with Product Network:**
```bash
curl -X POST http://localhost:8000/api/verify \
  -H "Content-Type: application/json" \
  -d '{
    "product_id": "PROD-2026-001",
    "location": "Warehouse",
    "scan_velocity": 8,
    "hours_since_creation": 48,
    "product_network": {
      "product_vectors": [
        [8, 48, 1],
        [12, 50, 1],
        [9, 45, 1],
        [2, 100, 0]
      ],
      "edge_connections": [
        [0, 1],
        [1, 2],
        [0, 2],
        [2, 3]
      ]
    }
  }'
```

**Expected Response (Network Anomaly Detected):**
```json
{
  "status": "counterfeit",
  "message": "SUSPICIOUS: Verification matches blockchain keys, but scan metrics flag anomaly. Potential cloned QR code.",
  "ai_metrics": {
    "authenticity_probability": 0.31,
    "anomaly_score": 0.69,
    "flags": [
      "High Scan Frequency",
      "Geographical Velocity Violation",
      "Counterfeiting Network Detected"  ← GNN caught the ring!
    ],
    "model_scores": {
      "random_forest": {
        "authenticity_prob": 0.42,
        "counterfeit_prob": 0.58
      },
      "gnn_network": {
        "mean_authenticity": 0.15,
        "mean_counterfeit_risk": 0.85,
        "network_scores": [0.18, 0.22, 0.12, 0.82]
      }
    }
  }
}
```

---

### 5. Get Product History

**cURL:**
```bash
curl -X GET http://localhost:8000/api/product/PROD-2026-001
```

**Expected Response:**
```json
{
  "id": 1,
  "product_id": "PROD-2026-001",
  "name": "Premium Leather Bag",
  "scan_history": [
    {
      "id": 1,
      "location": "Fifth Avenue Boutique, NYC",
      "scan_velocity": 1,
      "authenticity_probability": 0.96,
      "is_authentic": true,
      "timestamp": "2026-07-13T10:35:00"
    },
    {
      "id": 2,
      "location": "Street Market, Tokyo",
      "scan_velocity": 15,
      "authenticity_probability": 0.22,
      "is_authentic": false,
      "timestamp": "2026-07-13T10:40:00"
    }
  ]
}
```

---

## Development Workflows

### Adding a New Feature

1. **Create feature branch**
   ```bash
   git checkout -b feature/new-feature
   ```

2. **Update backend** (if needed)
   ```bash
   cd backend
   # Edit app/main.py, app/schemas.py, etc.
   # Test: http://localhost:8000/docs
   ```

3. **Update frontend** (if needed)
   ```bash
   cd frontend
   # Edit src/app files
   # Test: http://localhost:3000
   ```

4. **Update AI models** (if needed)
   ```bash
   cd ai-engine
   # Edit train.py
   python train.py  # Retrain
   ```

5. **Test end-to-end**
   ```bash
   # Run integration tests
   bash test-integration.sh
   ```

6. **Commit & submit PR**
   ```bash
   git add .
   git commit -m "feat: description"
   git push origin feature/new-feature
   ```

---

## Performance Profiling

### Backend Profiling
```python
# In app/main.py, add profiling middleware
from fastapi_profiler import FastAPIProfiler
FastAPIProfiler(app)

# View results at: http://localhost:8000/metrics
```

### AI Model Profiling
```bash
cd ai-engine
python -m cProfile -s cumulative train.py
```

### Blockchain Gas Profiling
```bash
cd blockchain
npm run test:gas-reporter
```

---

## Debugging

### Backend Debugging with Python
```python
# Add debugger breakpoint in code
import pdb; pdb.set_trace()

# Or use IDE debugger (VSCode, PyCharm)
```

### Frontend Debugging
```javascript
// Browser DevTools (Chrome/Firefox)
// F12 → Sources/Debugger tab
// Add breakpoints in Next.js code
```

### Blockchain Debugging
```bash
# Hardhat debugging
npx hardhat run scripts/deploy.js --network localhost --log-level debug

# View transaction details
hardhat console --network localhost
// Check tx: await ethers.provider.getTransaction('0x...')
```

---

## Load Testing

### Load test backend
```bash
# Install locust
pip install locust

# Create locust file
# locustfile.py
from locust import HttpUser, task

class APIUser(HttpUser):
    @task
    def verify_product(self):
        self.client.post("/api/verify", json={...})

# Run
locust -f locustfile.py --host=http://localhost:8000
```

### Stress test database
```bash
# Using pgbench
pgbench -i -s 10 authentiq
pgbench -c 10 -j 2 -T 60 authentiq
```

---

## Monitoring & Logging

### View Backend Logs
```bash
docker-compose logs -f backend
```

### View Database Logs
```bash
docker-compose logs -f postgres
```

### View Blockchain Logs
```bash
docker-compose logs -f hardhat
```

### Structured Logging
```python
# In backend code
import logging
logger = logging.getLogger(__name__)
logger.info(f"Product registered: {product_id}")
```

---

## Common Development Tasks

### Generate API Client
```bash
# Install OpenAPI generator
npm install -g @openapitools/openapi-generator-cli

# Generate Python client
openapi-generator-cli generate \
  -i http://localhost:8000/openapi.json \
  -g python \
  -o ./generated-client
```

### Database Migrations
```bash
# Using Alembic (SQLAlchemy)
cd backend
alembic init migrations
alembic revision --autogenerate -m "add_new_column"
alembic upgrade head
```

### Environment Variables Management
```bash
# Development
source .env.development

# Production
source .env.production
```

---

## Testing Checklist

- [ ] All endpoints respond with correct status codes
- [ ] Database transactions are consistent
- [ ] Smart contracts can register and scan products
- [ ] Models load and make predictions
- [ ] GNN detects counterfeiting networks
- [ ] Frontend QR scanner works
- [ ] Cross-origin requests handled by CORS
- [ ] Error handling and validation work
- [ ] Database backups work
- [ ] All logs are clean (no critical errors)

---

## Performance Targets

| Component | Target | Current |
|-----------|--------|---------|
| API response time | <500ms | ~200ms |
| Model inference | <100ms | RF: 8ms, GNN: 50ms |
| Database query | <50ms | ~10ms |
| Frontend load | <2s | ~1s |
| Smart contract gas | <300k | ~200k |

---

## Troubleshooting Development Issues

| Issue | Solution |
|-------|----------|
| Port already in use | Change `API_PORT` in `.env` or kill process |
| Database locked | Restart PostgreSQL container |
| Models not loading | Run `python ai-engine/train.py` |
| TypeScript errors | Run `npm run lint --fix` in frontend |
| Hardhat fork issues | Clear cache: `rm -rf blockchain/.hardhat` |

---

For more help, see main [README.md](README.md) or [SETUP.md](SETUP.md)
