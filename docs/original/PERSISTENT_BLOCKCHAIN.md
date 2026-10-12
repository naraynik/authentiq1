# ⛓️ AuthentiQ Persistent Local Blockchain Setup & Operations

This document explains how AuthentiQ's persistent local blockchain operates, ensuring that registered products, smart contract bytecode, and transaction history persist across terminal closes and computer restarts.

---

## 💡 Overview & Technical Background

### Why Old Hardhat State Disappeared
By default, standard `npx hardhat node` creates an **in-memory** EVM blockchain instance. When the terminal is closed or the computer restarts, the memory is cleared, causing deployed smart contracts and registered products to disappear.

### How Persistent Blockchain Works
AuthentiQ uses **Ganache** with disk-backed database storage (`--db ./chain_data`). All EVM state transitions, block headers, account balances, transaction receipts, and smart-contract bytecodes are written directly to disk.

---

## 📁 Storage Location & Configuration

* **Persistent Storage Directory**: [`AuthentiQ-Blockchain-main/chain_data/`](file:///d:/eng%203rd%20sem/sem%207/final%20project/AuthentiQ-Blockchain-main/chain_data)
* **RPC URL**: `http://127.0.0.1:8545`
* **Chain ID**: `1337`
* **Network Name**: `ganache`
* **Environment Variable Mnemonic**: `GANACHE_MNEMONIC` (configured via environment / `.env`)

> [!NOTE]
> Closing the terminal running the persistent blockchain node or restarting your computer **does NOT delete** stored blockchain data.
> The stored blockchain state is only cleared if you manually delete the `chain_data/` folder.

---

## 🚀 Quick Startup & Shutdown Commands

### Option A — One-Click PowerShell Orchestrator
To start all services safely (PostgreSQL + Persistent Ganache + Smart Contract Bytecode Check + FastAPI + Frontend):

```powershell
.\start-project.ps1
```

To stop all running background processes **without losing any blockchain data or database records**:

```powershell
.\stop-project.ps1
```

---

### Option B — Manual Step-by-Step Operations

#### 1. Start Persistent Blockchain Node
```cmd
cd "d:\eng 3rd sem\sem 7\final project\AuthentiQ-Blockchain-main"
npm run chain:start
```
*Runs `ganache --db ./chain_data --port 8545 --chainId 1337`.*

#### 2. Deploy or Verify Smart Contract
```cmd
cd "d:\eng 3rd sem\sem 7\final project\AuthentiQ-Blockchain-main"
npm run deploy:ganache
```
*`scripts/deploy.js` inspects `provider.getCode(CONTRACT_ADDRESS)`. If contract bytecode exists on the persistent chain, **redeployment is skipped**. If bytecode does not exist, `ProductVerification.sol` is deployed.*

#### 3. Start FastAPI Backend Gateway
```cmd
cd "d:\eng 3rd sem\sem 7\final project\AUTHENIQ-AI-main\backend"
uvicorn app.main:app --reload --port 8000
```

#### 4. Start Next.js Frontend
```cmd
cd "d:\eng 3rd sem\sem 7\final project\AUTHENIQ-AI-main\frontend"
npm run dev
```

---

## 🔄 Dataset Reconciliation Utility

If PostgreSQL contains historical products from a prior setup, run the safe reconciliation script:

### Dry-Run Audit (Default - Does NOT mutate database or chain):
```cmd
cd "d:\eng 3rd sem\sem 7\final project\AUTHENIQ-AI-main\backend"
python scratch/reconcile_onchain_products.py
```

### Active On-Chain Re-Registration:
```cmd
cd "d:\eng 3rd sem\sem 7\final project\AUTHENIQ-AI-main\backend"
python scratch/reconcile_onchain_products.py --reconcile
```
*Only registers missing products on the persistent chain and issues genuine new transaction receipts.*
