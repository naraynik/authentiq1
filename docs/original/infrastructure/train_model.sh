#!/bin/bash
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}===============================================${NC}"
echo -e "${GREEN}      AuthentiQ Model Training Invoker         ${NC}"
echo -e "${BLUE}===============================================${NC}"

if [ -f "../ai-engine/train.py" ]; then
    echo -e "Executing Random Forest training pipeline..."
    python3 ../ai-engine/train.py
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}Model trained and exported successfully.${NC}"
    else
        echo -e "${RED}Error: Model training run failed!${NC}"
        exit 1
    fi
else
    echo -e "${RED}Error: train.py not found in /ai-engine!${NC}"
    exit 1
fi
