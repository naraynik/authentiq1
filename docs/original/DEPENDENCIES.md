# AuthentiQ Project Dependencies

## Summary

| Component | Type | Dependencies |
|-----------|------|--------------|
| AI Engine | Python | TensorFlow, PyTorch Geometric, scikit-learn |
| Backend | Python | FastAPI, SQLAlchemy, Web3 |
| Frontend | JavaScript | React, Next.js, Tailwind CSS |
| Blockchain | JavaScript | Hardhat, Solidity, OpenZeppelin |

---

## Detailed Breakdown

### 🤖 AI Engine (`ai-engine/requirements.txt`)

**Machine Learning:**
- `torch==2.1.2` - Deep learning framework (PyTorch)
- `torch-geometric==2.4.0` - Graph Neural Networks
- `scikit-learn==1.5.0` - Classical ML (Random Forest, preprocessing)
- `joblib==1.4.2` - Model serialization

**Data Processing:**
- `pandas==2.2.2` - Data manipulation
- `numpy==1.26.4` - Numerical computing

**Utilities:**
- `networkx==3.2` - Graph operations

---

### 🔧 Backend (`backend/requirements.txt`)

**Web Framework:**
- `fastapi==0.111.0` - Modern async API framework
- `uvicorn==0.30.1` - ASGI server (runs FastAPI)

**Database:**
- `sqlalchemy==2.0.31` - ORM for database operations
- `psycopg2-binary==2.9.9` - PostgreSQL adapter

**Blockchain:**
- `web3>=7.0.0` - Connect to Ethereum-compatible blockchains
- Ethers.js integration (via Web3.py)

**Data Validation:**
- `pydantic==2.7.4` - Data validation with type hints
- `pydantic-settings==2.3.4` - Environment configuration

**AI Models:**
- `torch==2.1.2` - For GNN inference
- `torch-geometric==2.4.0` - GNN layers
- `scikit-learn==1.5.0` - RF model loading
- `joblib==1.4.2` - Model deserialization
- `pandas==2.2.2` - Data processing
- `numpy==1.26.4` - Numerical ops

---

### 🎨 Frontend (`frontend/package.json`)

**Core:**
- `next@16.2.10` - React framework with SSR
- `react@19.2.4` - UI library
- `react-dom@19.2.4` - React DOM renderer

**Styling:**
- `tailwindcss@4` - Utility-first CSS
- `@tailwindcss/postcss@4` - PostCSS plugin
- `postcss@^4` - CSS transformation

**Features:**
- `html5-qrcode@2.3.8` - QR code scanner

**Development:**
- `typescript@5` - Type safety
- `eslint@9` - Code linting
- `eslint-config-next@16.2.10` - Next.js linting rules

**Build:**
- `@types/react@19` - Type definitions
- `@types/react-dom@19` - DOM types
- `@types/node@20` - Node types

---

### ⛓️ Blockchain (`blockchain/package.json`)

**Smart Contract Development:**
- `hardhat@2.22.5` - Ethereum dev environment
- `@nomicfoundation/hardhat-toolbox@5.0.0` - Tooling bundle
- `@openzeppelin/contracts@5.6.1` - Audited smart contract library

**Ethereum Interaction:**
- `ethers@6.13.0` - Web3 library (blockchain interaction)

---

## Installation Commands

### Install All
```bash
# Combined single-line install (from root)
pip install -r backend/requirements.txt && \
pip install -r ai-engine/requirements.txt && \
cd blockchain && npm install && \
cd ../frontend && npm install
```

### Install by Component
```bash
# AI Engine
cd ai-engine && pip install -r requirements.txt

# Backend
cd backend && pip install -r requirements.txt

# Blockchain
cd blockchain && npm install

# Frontend
cd frontend && npm install
```

### Virtual Environment (Recommended)
```bash
# Create Python venv
python3 -m venv venv
source venv/bin/activate  # macOS/Linux
# or: venv\Scripts\activate  # Windows

# Install Python dependencies
pip install -r backend/requirements.txt
pip install -r ai-engine/requirements.txt
```

---

## Package Statistics

| Metric | Value |
|--------|-------|
| Total Python Packages | 16 |
| Total JS Packages | 20+ |
| Total Dependencies (transitive) | 500+ |
| Combined Size (node_modules + venv) | ~2GB |

---

## Version Compatibility

- **Node.js:** ≥18.0.0
- **Python:** ≥3.10
- **PostgreSQL:** ≥12
- **Solidity:** 0.8.24

---

## Optional Dependencies

### For Production
- `gunicorn` - Production ASGI server
- `nginx` - Reverse proxy
- `postgresql` - Database server

### For Development
- `pytest` - Testing framework
- `black` - Code formatter
- `mypy` - Static type checker

### For Deployment
- Docker & Docker Compose
- AWS CLI / GCP CLI (optional)
- Terraform (optional)

---

## Security Notes

- All dependencies are from PyPI and npm (official registries)
- No private forks or beta versions used
- Regular updates recommended for security patches
- See individual package docs for security advisories

---

## Troubleshooting

### Python Package Issues
```bash
# Clear pip cache
pip cache purge

# Upgrade pip
pip install --upgrade pip

# Install with verbose output
pip install -v -r requirements.txt
```

### Node Package Issues
```bash
# Clear npm cache
npm cache clean --force

# Reinstall node_modules
rm -rf node_modules package-lock.json
npm install
```

### Dependency Conflicts
```bash
# Check for conflicts
npm audit
pip check

# Fix conflicts
npm audit fix
```

---

For detailed package documentation, see:
- PyPI: https://pypi.org/
- NPM: https://www.npmjs.com/
- OpenZeppelin Docs: https://docs.openzeppelin.com/
