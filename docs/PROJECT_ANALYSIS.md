# 🔍 AuthentiQ System Analysis & Project Specification Document

**Project Name**: AuthentiQ – Smart Product Authentication & Anti-Counterfeit System  
**Date**: September 8, 2026  
**Status**: Comprehensive Analysis Completed (Phase 0)  

---

## Executive Summary

The **AuthentiQ** Anti-Counterfeit System is a multi-tiered security platform combining **EVM Blockchain Supply Chain Provenance** with **Dual-Model AI Anomaly Detection** (Random Forest Classifier + Graph Neural Network).

This document presents a comprehensive, line-by-line inspection of both component codebases:
1. `/blockchain` (`AuthentiQ-Blockchain-main`)
2. `/ai` (`AUTHENIQ-AI-main`)

It details the existing implementation, identifies integration gaps and security risks, answers all 10 architectural questions, and outlines the target production architecture supporting **Admin Governance**, **Manufacturer Onboarding & Product Registration**, **Public Consumer Verification**, **AI Anomaly Detection**, **Blockchain Provenance**, and **Relational Database Storage**.

---

## 1. Existing Architecture & Codebase Inspection

```
┌─────────────────────────────────────────────────────────────────────────┐
│                      EXISTING CODEBASE STRUCTURE                        │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  📁 AuthentiQ-Blockchain-main/      📁 AUTHENIQ-AI-main/                │
│  ├── contracts/                     ├── ai-engine/                      │
│  │   └── ProductVerification.sol    │   ├── train.py                    │
│  ├── scripts/                       │   ├── train_advanced.py           │
│  │   ├── deploy.js                  │   └── rf_model.joblib             │
│  │   ├── exportArtifacts.js         ├── backend/                      │
│  │   └── interact.js                │   └── app/                      │
│  ├── exports/                       │       ├── main.py (Flask)       │
│  │   └── contractData.json          │       ├── ai_client.py          │
│  ├── hardhat.config.js              │       ├── blockchain_client.py  │
│  ├── server.js (Express Node)       │       ├── models.py (SQLAlchemy)│
│  └── test_ui.html                   │       └── models/ (Trained Joblib/PT)
│                                     └── blockchain/                   │
│                                         └── AuthentiQRegistry.sol     │
└─────────────────────────────────────────────────────────────────────────┘
```

### A. Blockchain Module Inspection (`AuthentiQ-Blockchain-main`)
* **Solidity Smart Contracts**:
  * Core Contract: `ProductVerification.sol` (`pragma solidity ^0.8.20`).
  * OpenZeppelin Base: `@openzeppelin/contracts/access/AccessControl.sol`.
* **Contract Name**: `ProductVerification`
* **AccessControl Roles**:
  * `DEFAULT_ADMIN_ROLE` (`keccak256("DEFAULT_ADMIN_ROLE")`): Full administrative control.
  * `MANUFACTURER_ROLE` (`keccak256("MANUFACTURER_ROLE")`): Product registration & target route management.
  * `INSPECTOR_ROLE` (`keccak256("INSPECTOR_ROLE")`): Status flagging & recall management.
* **Contract Enums & Structs**:
  * `ProductStatus`: `GENUINE (0)`, `SUSPICIOUS (1)`, `RECALLED (2)`.
  * `LocationRecord`: `locationName`, `details`, `timestamp`, `updatedBy`.
  * `Product`: `productId`, `manufacturerName`, `batchNumber`, `manufacturingDate`, `expiryDate`, `currentLocation`, `nextLocation`, `productHash`, `registrationTimestamp`, `status`, `isRegistered`.
* **Contract Functions**:
  1. `constructor(address defaultAdmin)`
  2. `registerProduct(...)`: `external onlyRole(MANUFACTURER_ROLE)`
  3. `registerProductBatch(...)`: `external onlyRole(MANUFACTURER_ROLE)`
  4. `updateNextLocation(...)`: `external onlyRole(MANUFACTURER_ROLE)`
  5. `updateProductStatus(...)`: `external onlyRole(INSPECTOR_ROLE)`
  6. `verifyProduct(string productId)`: `external view returns (Product memory)`
  7. `getLocationHistory(string productId)`: `external view returns (LocationRecord[] memory)`
  8. `productExists(string productId)`: `external view returns (bool)`
* **Events**:
  * `ProductRegistered(string indexed productId, string manufacturerName, string batchNumber, address indexed manufacturer, string currentLocation, string nextLocation, bytes32 productHash, uint256 registrationTimestamp)`
  * `LocationUpdated(string indexed productId, string previousLocation, string nextLocation, address indexed updatedBy, uint256 timestamp)`
  * `ProductStatusUpdated(string indexed productId, ProductStatus oldStatus, ProductStatus newStatus, address indexed updatedBy, uint256 timestamp)`
* **Hardhat Configuration (`hardhat.config.js`)**:
  * Compiler: Solidity `0.8.20` with `optimizer` (`runs: 200`) and `viaIR: true`.
  * Networks: `hardhat` (Chain ID `1337`), `ganache` (`http://127.0.0.1:7545`, Chain ID `5777`), `sepolia` (`SEPOLIA_RPC_URL`, Chain ID `11155111`).
* **Deployment & Helper Scripts**:
  * `scripts/deploy.js`: Deploys contract passing deployer address as initial admin.
  * `scripts/exportArtifacts.js`: Copies compiled ABI and deployed address to `exports/contractData.json`.
  * `scripts/interact.js`: Simulation script demonstrating registration, route updates, and verification.
* **Express Server (`server.js`)**:
  * Node.js Express server running on port `3000` using Ethers.js v6 (`ethers.JsonRpcProvider`, `ethers.Wallet`, `ethers.Contract`).
* **Express API Endpoints**:
  * `GET /`: Serves `test_ui.html`.
  * `GET /health`: Health check returning blockchain provider state and Chain ID.
  * `POST /api/products/register`: Registers a product on-chain.
  * `POST /api/products/update-location`: Updates product target route destination.
  * `GET /api/products/verify/:productId`: Queries product metadata and location history.
  * `GET /api/products/qr-payload/:productId`: Returns standard QR JSON payload.
* **Environment Variables**:
  * `PORT`, `RPC_URL`, `CONTRACT_ADDRESS`, `MANUFACTURER_PRIVATE_KEY`, `GANACHE_PRIVATE_KEY`, `SEPOLIA_RPC_URL`, `SEPOLIA_PRIVATE_KEY`, `ETHERSCAN_API_KEY`.
* **Wallet / Private-Key Usage**:
  * `server.js` uses `MANUFACTURER_PRIVATE_KEY` to instantiate `ethers.Wallet` for writing transactions.
* **Database Usage**:
  * **None** in the Blockchain repository.

---

### B. AI Anomaly Detection Module Inspection (`AUTHENIQ-AI-main`)
* **Python Version**: Python 3.10+
* **Frameworks & Libraries**:
  * ML: `scikit-learn` (`1.5.0`), `joblib` (`1.4.2`), `pandas` (`2.2.2`), `numpy` (`1.26.4`).
  * DL/Graph: `torch` (`2.3.1`/`2.4.0`), `torch-geometric` (`2.5.0`), `networkx` (`3.2`).
  * Web Backend: `Flask` (`3.0.3`), `Flask-Cors` (`4.0.1`), `SQLAlchemy` (`2.0.31`), `pydantic` (`2.7.4`), `pydantic-settings` (`2.3.4`).
* **Flask Backend (`backend/app/main.py`)**:
  * Flask REST API running default on port `8000` with SQLite/SQLAlchemy backend.
* **Random Forest Implementation**:
  * Basic Model (`ai-engine/train.py`): Trained on `scan_velocity`, `hours_since_creation`, `is_location_anomaly`. Configured with `n_estimators=200`, `max_depth=12`, `class_weight='balanced'`.
  * Advanced Model (`ai-engine/train_advanced.py`): Trained on 16 physical/optical/environmental parameters (`micro_textures`, `color_printing_patterns`, `geometric_alignment`, `surface_features`, `printing_artifacts`, `frequency_features`, `color_space_metrics`, `spectral_metrics`, `deep_learning_latent_features`, `qr_code_integrity`, `barcode_integrity`, `temperature`, `humidity`, `hours_since_creation`, `scan_velocity`, `is_location_anomaly`).
* **GNN Implementation**:
  * `GNNAuthenticityDetector` / `AdvancedGNN`: 2-layer Graph Convolutional Network (`GCNConv` with 32 hidden units, ReLU, Dropout `0.5`, Linear LogSoftmax). Connects products sharing origin/transit nodes to detect counterfeiting rings.
* **Model Binary Files**:
  * `ai-engine/rf_model.joblib` (23.5 MB)
  * `backend/app/models/rf_advanced_model.joblib` (540 KB)
  * `backend/app/models/rf_model.joblib` (23.5 MB)
  * `backend/app/models/gnn_model.pt` (7.7 KB)
  * `backend/app/models/gnn_advanced_model.pt` (5.6 KB)
  * `backend/app/models/gnn_model.json` (236 B)
* **Input Features**:
  * `VerifyRequest` schema accepts 17 parameters including physical optical scores (0.0 to 1.0), environment metrics, and optional graph topology (`product_network`).
* **Output Format**:
  * `authenticity_probability` (float 0.0–1.0), `anomaly_score` (float 0.0–1.0), `flags` (list of strings), `status` verdict (`authentic`, `suspicious`, `counterfeit`, `unregistered`), and detailed `model_scores`.
* **Prediction Logic (`backend/app/ai_client.py`)**:
  * Executes ensemble weighted score: $\text{Combined Authenticity} = 0.6 \times \text{RF} + 0.4 \times \text{GNN}$.
  * $\text{Anomaly Score} = 1.0 - \text{Authenticity Probability}$.
  * Thresholds: Anomaly Score $> 0.6$ or $\ge 2$ physical flags $\rightarrow$ `counterfeit` / `suspicious`; Anomaly Score $< 0.4$ and $0$ flags $\rightarrow$ `authentic`.
* **Existing Database Models (`backend/app/models.py`)**:
  * `Product`: `id`, `product_id`, `name`, `batch_number`, `production_location`, `registered_at`.
  * `ScanHistory`: `id`, `product_id`, `location`, `scan_velocity`, `hours_since_creation`, `authenticity_probability`, `is_authentic`, `flags`, `timestamp`.
* **Existing Blockchain Integration (`backend/app/blockchain_client.py`)**:
  * `web3.py` client attempting to interface with a mock ERC-721 contract (`AuthentiQRegistry.sol`). Includes simulation fallback if Web3 or node connection fails.
* **Existing Flask API Endpoints**:
  * `GET /`: Health check.
  * `POST /api/register`: Registers product in SQLite DB and calls mock blockchain.
  * `POST /api/verify`: Executes blockchain read + AI evaluation + scan logging.
  * `GET /api/product/<product_id>`: Retrieves DB record, scan history, and blockchain status.
* **Environment Variables**:
  * `APP_NAME`, `DATABASE_URL`, `RPC_URL`, `CONTRACT_ADDRESS`, `CONTRACT_ABI_PATH`, `RF_MODEL_PATH`, `GNN_MODEL_PATH`.

---

## 2. Comprehensive Analysis Findings (10 Core Questions)

### 1. What can be reused directly?
* **Smart Contract (`ProductVerification.sol`)**: Production-ready Solidity contract featuring OpenZeppelin AccessControl, batch registration, target route tracking, and custom errors.
* **Trained Model Files**: All trained binaries (`rf_advanced_model.joblib`, `rf_model.joblib`, `gnn_advanced_model.pt`, `gnn_model.pt`) in `backend/app/models/`.
* **AI Inference Core (`AIClient` in `ai_client.py`)**: Multi-model evaluation logic (RF + GNN ensemble weighting & anomaly thresholding).
* **Hardhat Project Configuration**: `hardhat.config.js`, `deploy.js`, compilation settings (`viaIR: true`, optimizer 200 runs).
* **Pydantic Verification Schemas**: `VerifyRequest`, `VerifyResponse`, `AIMetrics` in `schemas.py`.

### 2. What needs modification?
* **`blockchain_client.py`**: Must be rewritten to call `ProductVerification.sol` ABI methods (`registerProduct` with 8 parameters, `updateNextLocation`, `updateProductStatus`, `verifyProduct`, `getLocationHistory`).
* **AI Preprocessing & Imputation (`ai_client.py`)**: Needs automatic feature imputation so mobile QR scans without 16 optical features default gracefully.
* **Database ORM (`models.py`)**: Must be expanded to support Admin users, Manufacturer profiles with document uploads, audit logs, and complete supply chain provenance metadata.

### 3. What needs to be replaced?
* **Legacy ERC-721 Contract (`AuthentiQRegistry.sol`)**: Replace completely with `ProductVerification.sol`.
* **Dual Backend Fragmentation**: Replace Node.js `server.js` (port 3000) and Flask `main.py` (port 8000) with a single **Unified FastAPI Backend Gateway**.
* **Hardcoded Private Key Signing**: Replace static `.env` keys with an authenticated key vault and role-aware Web3 signer service.

### 4. What APIs already exist?
* **Blockchain Express Server**: `GET /health`, `POST /api/products/register`, `POST /api/products/update-location`, `GET /api/products/verify/:productId`, `GET /api/products/qr-payload/:productId`.
* **AI Flask Backend**: `GET /`, `POST /api/register`, `POST /api/verify`, `GET /api/product/<product_id>`.

### 5. What APIs need to be created?
* **Admin Governance APIs**:
  * `POST /api/v1/admin/login`
  * `GET /api/v1/admin/manufacturers` (Filter by PENDING, APPROVED, REJECTED, SUSPENDED)
  * `GET /api/v1/admin/manufacturers/:id/document` (View uploaded PDF/image document)
  * `PUT /api/v1/admin/manufacturers/:id/approve`
  * `PUT /api/v1/admin/manufacturers/:id/reject`
  * `PUT /api/v1/admin/manufacturers/:id/suspend`
  * `GET /api/v1/admin/products`
  * `GET /api/v1/admin/scans` (View all QR scans & AI verdicts)
  * `GET /api/v1/admin/suspicious-items`
  * `GET /api/v1/admin/audit-logs`
* **Manufacturer Portal APIs**:
  * `POST /api/v1/manufacturer/register` (Multipart form: name, GSTIN, details, document upload, email, password)
  * `POST /api/v1/manufacturer/login`
  * `POST /api/v1/manufacturer/products/register` (Single product registration)
  * `POST /api/v1/manufacturer/products/register-batch` (Batch registration)
  * `POST /api/v1/manufacturer/products/update-location` (Supply chain target location update)
  * `GET /api/v1/manufacturer/products` (List company products)
  * `GET /api/v1/manufacturer/products/:id/qr-payload`
* **Public Consumer APIs**:
  * `POST /api/v1/public/verify` (No login required: scan QR, run AI anomaly check, query blockchain)
  * `GET /api/v1/public/product/:productId` (View product golden record & location route history)

### 6. What dependencies conflict?
* **Node.js Express vs Python Flask/FastAPI**: Server duplication across ports 3000 and 8000.
* **Web3.py (Python v7+) vs Ethers.js (Node v6)**: Interoperability syntax differences when formatting BigInts and custom error reverts.
* **PyTorch CPU vs GPU**: `torch==2.3.1+cpu` requires fallback flags in environments without GPU acceleration.

### 7. What integration problems exist?
* **Contract Method Mismatch**: `blockchain_client.py` expects `getProduct()` and `recordScan()`, but `ProductVerification.sol` exposes `verifyProduct()` and `updateNextLocation()`.
* **Database Field Omission**: SQLAlchemy models omit `expiry_date`, `product_hash`, `current_location`, `next_location`, `status`, `tx_hash`.
* **Mobile QR vs Optical AI Payload**: Mobile scans only send GPS, timestamp, and product ID, whereas the trained Random Forest model requires 16 optical features.

### 8. What security problems exist?
* **Zero Authentication**: Anyone can call `/api/register` or `/api/verify` without credentials.
* **Hardcoded Signer Key**: `MANUFACTURER_PRIVATE_KEY` is statically defined in `.env`.
* **Unprotected File Uploads**: Lack of MIME-type validation, virus scanning, or access restriction on company verification documents.
* **Missing Password Hashing**: Passwords stored without `bcrypt`/`argon2` encryption.

### 9. What information must be stored in the database?
* **Users**: `id`, `email`, `password_hash`, `role` (`ADMIN`, `MANUFACTURER`, `CONSUMER`), `is_active`, `created_at`.
* **Manufacturers**: `id`, `user_id`, `company_name`, `gstin`, `company_details`, `verification_document_path`, `approval_status` (`PENDING`, `APPROVED`, `REJECTED`, `SUSPENDED`), `approved_by`, `approved_at`, `created_at`.
* **Products**: `id`, `product_id`, `manufacturer_id`, `manufacturer_name`, `batch_number`, `manufacturing_date`, `expiry_date`, `product_hash`, `current_location`, `next_location`, `status` (`GENUINE`, `SUSPICIOUS`, `RECALLED`), `is_onchain`, `registration_tx_hash`, `created_at`.
* **Location History**: `id`, `product_id`, `location_name`, `details`, `updated_by_address`, `tx_hash`, `timestamp`.
* **Scan History**: `id`, `product_id`, `scanned_by_id`, `location`, `scan_velocity`, `hours_since_creation`, `authenticity_probability`, `anomaly_score`, `status_verdict`, `flags`, `raw_metrics` (JSON), `scan_tx_hash`, `timestamp`.
* **Audit Logs**: `id`, `user_id`, `user_role`, `action`, `target_entity`, `target_id`, `ip_address`, `timestamp`.

### 10. How should the final system connect together?

```
┌─────────────────────────────────────────────────────────────────────────┐
│                     FINAL INTEGRATED SYSTEM ARCHITECTURE                │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌───────────────────────┐  ┌───────────────────────┐  ┌─────────────┐  │
│  │     Admin Portal      │  │  Manufacturer Portal  │  │ Public User │  │
│  │ (Approval, Analytics) │  │  (Product Reg, Route) │  │ (QR Scanner)│  │
│  └───────────┬───────────┘  └───────────┬───────────┘  └──────┬──────┘  │
│              │                          │                     │         │
│              └──────────────────────────┼─────────────────────┘         │
│                                         │ HTTPS / REST                  │
│                        ┌────────────────▼────────────────┐              │
│                        │     Unified FastAPI Gateway     │              │
│                        │  - JWT Bearer Authentication    │              │
│                        │  - Role-Based Access Control    │              │
│                        │  - Multipart File Upload Handler│              │
│                        └────────┬───────────────┬────────┘              │
│                                 │               │                       │
│        ┌────────────────────────┘               └───────────┐           │
│        │                                                    │           │
│ ┌──────▼──────────────────┐                      ┌──────────▼─────────┐ │
│ │  AI Inference Service   │                      │ Web3 Blockchain    │ │
│ │  - RF Optical Model     │                      │ Bridge Service     │ │
│ │  - GNN Network Model    │                      │ - ProductVerify.sol│ │
│ │  - Feature Imputer      │                      │ - Nonce & Gas Mgr  │ │
│ └──────┬──────────────────┘                      └──────────┬─────────┘ │
│        │                                                    │           │
│        └────────────────────────┬───────────────────────────┘           │
│                                 │                                       │
│                    ┌────────────▼───────────┐                           │
│                    │ PostgreSQL Relational  │                           │
│                    │ Database & Audit Logs  │                           │
│                    └────────────────────────┘                           │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Proposed Database Architecture (SQL DDL)

```sql
-- 1. Users Table
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(50) NOT NULL CHECK (role IN ('ADMIN', 'MANUFACTURER', 'CONSUMER')),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 2. Manufacturers Table (GSTIN & Verification Onboarding)
CREATE TABLE manufacturers (
    id SERIAL PRIMARY KEY,
    user_id INT UNIQUE NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    company_name VARCHAR(255) NOT NULL,
    gstin VARCHAR(15) UNIQUE NOT NULL,
    company_details TEXT,
    verification_document_path VARCHAR(512) NOT NULL,
    approval_status VARCHAR(50) DEFAULT 'PENDING' CHECK (approval_status IN ('PENDING', 'APPROVED', 'REJECTED', 'SUSPENDED')),
    approved_by INT REFERENCES users(id),
    approved_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 3. Products Table (Golden Record & On-Chain Provenance)
CREATE TABLE products (
    id SERIAL PRIMARY KEY,
    product_id VARCHAR(100) UNIQUE NOT NULL,
    manufacturer_id INT NOT NULL REFERENCES manufacturers(id),
    manufacturer_name VARCHAR(255) NOT NULL,
    batch_number VARCHAR(100) NOT NULL,
    manufacturing_date BIGINT NOT NULL,
    expiry_date BIGINT DEFAULT 0,
    product_hash VARCHAR(66) NOT NULL,
    current_location VARCHAR(255) NOT NULL,
    next_location VARCHAR(255) NOT NULL,
    status VARCHAR(50) DEFAULT 'GENUINE' CHECK (status IN ('GENUINE', 'SUSPICIOUS', 'RECALLED')),
    is_onchain BOOLEAN DEFAULT FALSE,
    registration_tx_hash VARCHAR(66),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 4. Location History Table (Supply Chain Route History Audit Log)
CREATE TABLE location_history (
    id SERIAL PRIMARY KEY,
    product_id VARCHAR(100) REFERENCES products(product_id) ON DELETE CASCADE,
    location_name VARCHAR(255) NOT NULL,
    details TEXT,
    updated_by_address VARCHAR(42) NOT NULL,
    tx_hash VARCHAR(66),
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 5. Scan History Table (AI Inspection & Consumer Verification Audit Log)
CREATE TABLE scan_history (
    id SERIAL PRIMARY KEY,
    product_id VARCHAR(100) REFERENCES products(product_id) ON DELETE CASCADE,
    scanned_by_id INT REFERENCES users(id),
    location VARCHAR(255) NOT NULL,
    scan_velocity INT DEFAULT 1,
    hours_since_creation DOUBLE PRECISION DEFAULT 0.0,
    authenticity_probability DOUBLE PRECISION NOT NULL,
    anomaly_score DOUBLE PRECISION NOT NULL,
    status_verdict VARCHAR(50) NOT NULL,
    flags TEXT,
    raw_metrics JSONB,
    scan_tx_hash VARCHAR(66),
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 6. Audit Logs Table (Administrative & Security Event Audit Trail)
CREATE TABLE audit_logs (
    id SERIAL PRIMARY KEY,
    user_id INT REFERENCES users(id),
    user_role VARCHAR(50) NOT NULL,
    action VARCHAR(255) NOT NULL,
    target_entity VARCHAR(100) NOT NULL,
    target_id VARCHAR(100),
    ip_address VARCHAR(45),
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
```

---

## 4. Proposed Authentication Architecture

```
  Client Login (Email + Password)
            │
            ▼
 ┌──────────────────────┐
 │ FastAPI /api/v1/auth │
 └──────────┬───────────┘
            │ 1. Validate Password Hash (bcrypt)
            │ 2. Read Role & Approval Status
            ▼
 ┌────────────────────────────────────────────────────────┐
 │ Issue RS256 JWT Bearer Token                           │
 │ Claims: { sub: user_id, role: role, mfr_id: mfr_id }  │
 └──────────────────────────┬─────────────────────────────┘
                            │
            ┌───────────────┴───────────────┐
            │                               │
 ┌──────────▼──────────┐         ┌──────────▼──────────┐
 │ Admin Endpoints     │         │ Manufacturer Endpt  │
 │ (Requires role=ADMIN│         │ (Requires APPROVED  │
 │  Header Token)      │         │  MANUFACTURER token)│
 └─────────────────────┘         └─────────────────────┘
```

---

## 5. Proposed Implementation Phases

### Phase 1: Core Backend Gateway & Database Migration
* Establish Unified FastAPI Application structure (`/backend/app`).
* Implement PostgreSQL database models (`User`, `Manufacturer`, `Product`, `LocationHistory`, `ScanHistory`, `AuditLog`) with Alembic migrations.
* Build JWT Authentication & RBAC middleware.

### Phase 2: Blockchain Bridge Realignment
* Update `blockchain_client.py` to match `ProductVerification.sol` ABI methods (`registerProduct`, `registerProductBatch`, `updateNextLocation`, `updateProductStatus`, `verifyProduct`, `getLocationHistory`).
* Integrate wallet key vault for transaction signing.

### Phase 3: AI Inference & Feature Imputer Pipeline
* Refactor `ai_client.py` with automatic feature imputation for mobile QR scan payloads.
* Integrate Random Forest + GNN ensemble scoring into backend verification workflow.

### Phase 4: Manufacturer Onboarding & Admin Governance Portal
* Implement Manufacturer registration with document upload & GSTIN validation.
* Implement Admin Approval, Rejection, Suspension workflow & Audit Logging.

### Phase 5: Public Consumer Scan & QR Payload Verification
* Implement public verification endpoint (`/api/v1/public/verify`) with real-time AI anomaly scoring and blockchain provenance display.
* Generate standard QR code payloads.

### Phase 6: System Verification & Testing
* Run local Hardhat blockchain network.
* Execute end-to-end integration tests (Auth $\rightarrow$ Approval $\rightarrow$ Registration $\rightarrow$ Route Update $\rightarrow$ QR Scan $\rightarrow$ AI Anomaly Alert $\rightarrow$ Blockchain Status Update).

---

> [!NOTE]
> All existing code files remain 100% untouched in strict compliance with phase instructions.

ANALYSIS COMPLETE – READY FOR PHASE 1
