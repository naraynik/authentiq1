#!/bin/bash
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}===============================================${NC}"
echo -e "${GREEN}      AuthentiQ Multi-Container System          ${NC}"
echo -e "${BLUE}===============================================${NC}"

echo -e "Booting services via Docker Compose..."
docker-compose up --build
