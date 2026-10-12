#!/bin/bash
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}===============================================${NC}"
echo -e "${GREEN}      AuthentiQ Smart Contract Deployer         ${NC}"
echo -e "${BLUE}===============================================${NC}"

cd ../blockchain

echo -e "Compiling contracts..."
npx hardhat compile

if [ $? -eq 0 ]; then
    echo -e "${GREEN}Solidity contracts compiled successfully.${NC}"
else
    echo -e "${RED}Error: Solidity compilation failed!${NC}"
    exit 1
fi

# Run deployment script (Targeting localhost nodes or defaults)
echo -e "Deploying contracts to blockchain..."
npx hardhat run scripts/deploy.js --network localhost

if [ $? -eq 0 ]; then
    echo -e "${GREEN}Smart contracts deployed and ABIs synced.${NC}"
else
    echo -e "${RED}Warning: Local deployment failed. Make sure a local Hardhat node is running (npm run node).${NC}"
    echo -e "Falling back to running a standalone deployment check..."
    npx hardhat run scripts/deploy.js
fi

cd ../infrastructure
