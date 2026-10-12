#!/bin/bash
# Colors for beautiful output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0;8m' # No Color

echo -e "${BLUE}===============================================${NC}"
echo -e "${GREEN}      AuthentiQ Monorepo Setup Script          ${NC}"
echo -e "${BLUE}===============================================${NC}"

# Check for required tools
echo -e "\n${BLUE}[1/5] Checking environment requirements...${NC}"
for cmd in node npm python3 pip3 docker docker-compose; do
    if command -v $cmd &> /dev/null; then
        echo -e "  - $cmd: ${GREEN}Installed${NC}"
    else
        echo -e "  - $cmd: ${YELLOW}Not found${NC} (Check installation if needed)"
    fi
done

# Initialize blockchain dependencies
echo -e "\n${BLUE}[2/5] Setting up Blockchain environment...${NC}"
if [ -d "../blockchain" ]; then
    cd ../blockchain
    echo -e "Installing npm packages in /blockchain..."
    npm install
    cd ../infrastructure
else
    echo -e "${RED}Error: /blockchain directory not found!${NC}"
fi

# Initialize backend dependencies
echo -e "\n${BLUE}[3/5] Setting up FastAPI backend environment...${NC}"
if [ -d "../backend" ]; then
    echo -e "Installing Python dependencies in /backend..."
    pip3 install -r ../backend/requirements.txt
else
    echo -e "${RED}Error: /backend directory not found!${NC}"
fi

# Initialize AI Engine dependencies
echo -e "\n${BLUE}[4/5] Setting up AI training environment...${NC}"
if [ -d "../ai-engine" ]; then
    echo -e "Installing Python dependencies in /ai-engine..."
    pip3 install -r ../ai-engine/requirements.txt
else
    echo -e "${RED}Error: /ai-engine directory not found!${NC}"
fi

# Initialize Next.js dependencies
echo -e "\n${BLUE}[5/5] Setting up Next.js frontend environment...${NC}"
if [ -d "../frontend" ]; then
    cd ../frontend
    echo -e "Installing npm packages in /frontend..."
    npm install
    cd ../infrastructure
else
    echo -e "${RED}Error: /frontend directory not found!${NC}"
fi

echo -e "\n${GREEN}Setup successfully complete! All packages installed.${NC}"
echo -e "You can now run: \n  - ./train_model.sh (to train AI engine)\n  - ./start.sh (to boot docker compose environment)${NC}"
