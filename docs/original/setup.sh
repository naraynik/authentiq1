#!/bin/bash
# AuthentiQ Quick Start Script (Linux/macOS)
# This script sets up the entire development environment

set -e  # Exit on error

echo "🚀 AuthentiQ Quick Start Setup"
echo "========================================"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check prerequisites
echo -e "${YELLOW}[1/6] Checking prerequisites...${NC}"
if ! command -v git &> /dev/null; then
    echo -e "${RED}❌ Git not found${NC}"
    exit 1
fi
if ! command -v docker &> /dev/null; then
    echo -e "${RED}❌ Docker not found${NC}"
    exit 1
fi
if ! command -v npm &> /dev/null; then
    echo -e "${RED}❌ Node.js/npm not found${NC}"
    exit 1
fi
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python not found${NC}"
    exit 1
fi
echo -e "${GREEN}✓ All prerequisites found${NC}"

# Install Python Dependencies
echo -e "${YELLOW}[2/6] Installing Python dependencies...${NC}"
cd ai-engine
python3 -m venv venv
source venv/bin/activate
pip install -q -r requirements.txt
echo -e "${GREEN}✓ AI engine dependencies installed${NC}"

cd ../backend
pip install -q -r requirements.txt
echo -e "${GREEN}✓ Backend dependencies installed${NC}"
cd ..

# Install Node Dependencies
echo -e "${YELLOW}[3/6] Installing Node.js dependencies...${NC}"
if [ -d "../AuthentiQ-Blockchain-main" ]; then
    cd ../AuthentiQ-Blockchain-main
    npm install -q
    cd ../AUTHENIQ-AI-main
    echo -e "${GREEN}✓ Blockchain dependencies installed${NC}"
fi

cd frontend
npm install -q
echo -e "${GREEN}✓ Frontend dependencies installed${NC}"
cd ..

# Start PostgreSQL
echo -e "${YELLOW}[4/6] Starting PostgreSQL database...${NC}"
if docker ps -a --format '{{.Names}}' | grep -q "authentiq-postgres-dev"; then
    docker rm -f authentiq-postgres-dev 2>/dev/null || true
fi
docker-compose -f docker-compose.dev.yml up -d
echo -e "${GREEN}✓ PostgreSQL started${NC}"

# Train AI Models
echo -e "${YELLOW}[5/6] Training AI models...${NC}"
cd ai-engine
source venv/bin/activate
python3 train.py
echo -e "${GREEN}✓ Models trained and saved${NC}"
cd ..

# Start Blockchain
echo -e "${YELLOW}[6/6] Starting Hardhat blockchain...${NC}"
echo ""
echo -e "${GREEN}✓ Setup complete!${NC}"
echo ""
echo "========================================"
echo "📋 Next Steps (in separate terminals):"
echo "========================================"
echo ""
echo "1. Start Blockchain (Terminal 1):"
echo "   cd ../AuthentiQ-Blockchain-main && npm run node"
echo ""
echo "2. Deploy Contracts (Terminal 2):"
echo "   cd ../AuthentiQ-Blockchain-main && npm run deploy:local"
echo ""
echo "3. Start Backend (Terminal 3):"
echo "   cd backend && uvicorn app.main:app --reload"
echo ""
echo "4. Start Frontend (Terminal 4):"
echo "   cd frontend && npm run dev"
echo ""
echo "========================================"
echo "🌐 Access:"
echo "========================================"
echo "Frontend:  http://localhost:3000"
echo "API Docs:  http://localhost:8000/docs"
echo "Database:  localhost:5432"
echo ""
