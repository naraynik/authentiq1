# 🏛️ AuthentiQ System Architecture & Integration Analysis

**Project**: Smart Product Authentication / Anti-Counterfeit System  
**Date**: September 8, 2026  
**Document Status**: Comprehensive Analysis & Integration Blueprint  

---

## Executive Summary

The **AuthentiQ** Anti-Counterfeit System is designed as a hybrid security architecture combining **EVM Blockchain Provenance** with **Dual-Model AI Anomaly Detection** (Random Forest + Graph Neural Networks). 

This document delivers an exhaustive architectural analysis of the two existing codebases:
1. **Blockchain Module** (`/AuthentiQ-Blockchain-main`)
2. **AI Anomaly Detection Module** (`/AUTHENIQ-AI-main`)

It details their current technical configurations, interface surfaces, dependencies, incompatibilities, and presents a production-grade recommended backend architecture, database schema, authentication blueprint, and step-by-step integration roadmap.

---

## 1. Current Architecture of Blockchain Module

The Blockchain module resides in `AuthentiQ-Blockchain-main` and provides an immutable, decentralized ledger for product birth certificates, manufacturer supply chain route declarations, and provenance tracking.

```
┌─────────────────────────────────────────────────────────────────────────┐
│                       BLOCKCHAIN MODULE ARCHITECTURE                    │
└─────────────────────────────────────────────────────────────────────────┘
                                     │
          ┌──────────────────────────┴──────────────────────────┐
          │                                                     │
┌─────────▼──────────┐                               ┌──────────▼──────────┐
│   Smart Contract   │                               │    REST API Server  │
│ ProductVerification│                               │     (server.js)     │
└─────────┬──────────┘                               └──────────┬──────────┘
          │ Solidity 0.8.20                                     │ Express.js
          │ OpenZeppelin AccessControl                          │ Ethers.js v6
          │                                                     │
 ┌────────┴──────────────────────────┐               ┌──────────┴──────────┐
 │ Contract Roles:                   │               │ Endpoints:          │
 │ - DEFAULT_ADMIN_ROLE              │               │ - GET  /health      │
 │ - MANUFACTURER_ROLE               │               │ - POST /api/...     │
 │ - INSPECTOR_ROLE                  │               │ - GET  /api/...     │
 └───────────────────────────────────┘               └─────────────────────┘
```

### Technical Specifications
* **Programming Language & Framework**: 
  * Smart Contract: Solidity (`^0.8.20`), compiled with optimization (`runs: 200`, `viaIR: true`).
  * Development Environment: Hardhat (`^2.22.3`) with `@nomicfoundation/hardhat-toolbox` (`^5.0.0`).
  * Backend Middleware Server: Node.js with Express.js (`^4.19.2`) and Ethers.js (`v6`).
* **Blockchain Technology**:
  * EVM (Ethereum Virtual Machine) compatible.
  * Supported Networks: Local Hardhat Node (Chain ID `1337`), Local Ganache Node (`http://127.0.0.1:7545`, Chain ID `5777`), Ethereum Sepolia Testnet (Chain ID `11155111`).
* **Smart Contracts**:
  * Core Contract: `contracts/ProductVerification.sol` (`contract ProductVerification is AccessControl`).
  * OpenZeppelin Base: `@openzeppelin/contracts/access/AccessControl.sol` for granular role-based permissions.

### Smart Contract Functions (`ProductVerification.sol`)
1. **`constructor(address defaultAdmin)`**: Grants `DEFAULT_ADMIN_ROLE`, `MANUFACTURER_ROLE`, and `INSPECTOR_ROLE` to `defaultAdmin` (or `msg.sender` if `address(0)`).
2. **`registerProduct(...)`**: `external onlyRole(MANUFACTURER_ROLE)`
   * *Parameters*: `string productId`, `string manufacturerName`, `string batchNumber`, `uint256 manufacturingDate`, `uint256 expiryDate`, `bytes32 productHash`, `string currentLocation`, `string nextLocation`.
   * *Logic*: Verifies non-existence, registers `Product` struct, appends origin `LocationRecord`, emits `ProductRegistered`.
3. **`registerProductBatch(...)`**: `external onlyRole(MANUFACTURER_ROLE)`
   * *Parameters*: `string[] productIds`, `string manufacturerName`, `string batchNumber`, `uint256 manufacturingDate`, `uint256 expiryDate`, `bytes32[] productHashes`, `string currentLocation`, `string nextLocation`.
   * *Logic*: Gas-optimized batch registration for bulk factory production.
4. **`updateNextLocation(...)`**: `external onlyRole(MANUFACTURER_ROLE)`
   * *Parameters*: `string productId`, `string newNextLocation`, `string details`.
   * *Logic*: Shifts `nextLocation` to `currentLocation`, sets new `nextLocation`, appends `LocationRecord` to `locationHistories[productId]`, emits `LocationUpdated`.
5. **`updateProductStatus(...)`**: `external onlyRole(INSPECTOR_ROLE)`
   * *Parameters*: `string productId`, `ProductStatus newStatus` (`GENUINE=0`, `SUSPICIOUS=1`, `RECALLED=2`).
   * *Logic*: Updates status flag, emits `ProductStatusUpdated`.
6. **`verifyProduct(string productId)`**: `external view returns (Product memory)`
   * *Logic*: Free read query returning full digital birth certificate.
7. **`getLocationHistory(string productId)`**: `external view returns (LocationRecord[] memory)`
   * *Logic*: Free read query returning complete location and route history array.
8. **`productExists(string productId)`**: `external view returns (bool)`
   * *Logic*: Returns `true` if `productId` is registered.

### Deployment & Export Configuration
* Configuration File: `hardhat.config.js`.
* Deployment Script: `scripts/deploy.js` deploys `ProductVerification` and outputs contract address.
* Artifact Export Script: `scripts/exportArtifacts.js` copies compiled ABI and deployed address to `exports/contractData.json`.

### Wallet & Web3 Integration
* `server.js` connects via `ethers.JsonRpcProvider(RPC_URL)`.
* Signed transactions are executed using `ethers.Wallet(MANUFACTURER_PRIVATE_KEY, provider)`.
* Client test interface: `test_ui.html` provides standard browser interaction with the API server.

### Product Registration & Verification Flow
* **Registration**: Executed via HTTP `POST /api/products/register`. Server instantiates `ethers.Wallet` using `MANUFACTURER_PRIVATE_KEY` and calls contract function `registerProduct()`.
* **Verification**: Executed via HTTP `GET /api/products/verify/:productId`. Server queries `contract.verifyProduct()` and `contract.getLocationHistory()` in parallel using `Promise.all` without spending gas.

### Dependencies & Environment Variables
* **Dependencies**: `@openzeppelin/contracts` (`^5.0.2`), `dotenv` (`^16.4.5`), `express` (`^4.19.2`), `hardhat` (`^2.22.3`), `@nomicfoundation/hardhat-toolbox` (`^5.0.0`).
* **Environment Variables**:
  * `PORT` (default: 3000)
  * `RPC_URL` (default: `http://127.0.0.1:8545`)
  * `CONTRACT_ADDRESS`
  * `MANUFACTURER_PRIVATE_KEY`
  * `GANACHE_PRIVATE_KEY`
  * `SEPOLIA_RPC_URL`
  * `SEPOLIA_PRIVATE_KEY`
  * `ETHERSCAN_API_KEY`

---

## 2. Current Architecture of AI Module

The AI module resides in `AUTHENIQ-AI-main` and provides multi-tiered machine learning and deep learning anomaly detection to flag counterfeit products, cloned QR codes, and supply chain fraud rings.

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           AI MODULE ARCHITECTURE                        │
└─────────────────────────────────────────────────────────────────────────┘
                                     │
          ┌──────────────────────────┴──────────────────────────┐
          │                                                     │
┌─────────▼──────────┐                               ┌──────────▼──────────┐
│  AI Engine Models  │                               │    Backend Gateway  │
│  (ai-engine/)      │                               │    (backend/app)    │
└─────────┬──────────┘                               └──────────┬──────────┘
          │ Scikit-Learn 1.5.0                                  │ Flask 3.0.3
          │ PyTorch 2.3/2.4 + PyG                               │ SQLAlchemy 2.0
          │                                                     │ Pydantic 2.7
┌─────────┴──────────────────────────┐               ┌──────────┴──────────┐
│ Dual-Model Core:                   │               │ Endpoints:          │
│ 1. Random Forest Classifier        │               │ - POST /api/register│
│    (Optical/IoT & Scan Anomaly)    │               │ - POST /api/verify  │
│ 2. Graph Neural Network (GNN)      │               │ - GET  /api/product │
│    (Supply Chain Network Fraud)    │               └─────────────────────┘
└────────────────────────────────────┘
```

### Technical Specifications
* **Programming Language & Framework**:
  * Language: Python 3.10+.
  * Machine Learning: `scikit-learn` (`1.5.0`), `joblib` (`1.4.2`), `pandas` (`2.2.2`), `numpy` (`1.26.4`).
  * Deep Learning & Graph Analytics: `torch` (`2.3.1`/`2.4.0`), `torch-geometric` (`2.5.0`), `networkx` (`3.2`).
  * Backend API Server: Flask (`3.0.3`) in `backend/app/main.py` with `flask-cors`, `SQLAlchemy` (`2.0.31`), `pydantic` (`2.7.4`), `pydantic-settings` (`2.3.4`).

### ML / DL Model Architecture
1. **Random Forest Classifier**:
   * *Basic Model (`train.py`)*: Trained on scan velocity, temporal creation gap, and geographic anomaly indicators (`scan_velocity`, `hours_since_creation`, `is_location_anomaly`). Configured with 200 trees, `max_depth=12`, `class_weight='balanced'`.
   * *Advanced Model (`train_advanced.py`)*: Trained on 16 features including optical/spectral metrics (`micro_textures`, `color_printing_patterns`, `geometric_alignment`, `surface_features`, `printing_artifacts`, `frequency_features`, `color_space_metrics`, `spectral_metrics`, `deep_learning_latent_features`, `qr_code_integrity`, `barcode_integrity`, `temperature`, `humidity`, `hours_since_creation`, `scan_velocity`, `is_location_anomaly`).
2. **Graph Neural Network (GNN)**:
   * *Architecture*: `GNNAuthenticityDetector` / `AdvancedGNN` built with PyTorch Geometric using two `GCNConv` graph convolution layers, ReLU activation, Dropout (`p=0.5`), and Linear classification head outputting LogSoftmax.
   * *Purpose*: Models supply chain items as graph nodes and shared origin/transit routes as edges to detect coordinated counterfeiting rings.

### Trained Model Files
* `ai-engine/rf_model.joblib` (23.5 MB) - Full basic Random Forest model.
* `backend/app/models/rf_advanced_model.joblib` (540 KB) - Advanced optical Random Forest model dictionary containing model + feature names list.
* `backend/app/models/gnn_model.pt` (7.7 KB) - PyTorch GNN state dictionary.
* `backend/app/models/gnn_advanced_model.pt` (5.6 KB) - Advanced GNN model weights.

### Preprocessing & Feature Engineering
* `LeakageFreePipeline`: Implements strict `GroupShuffleSplit` on `device_id` to eliminate data leakage. Computes `hours_since_creation` from timestamps, `scan_velocity` from device activity counts, and `is_location_anomaly` from device-to-IP cardinality mapping.
* One-hot encoding (`pd.get_dummies`) for categorical variables (`manufacturing_location`, `origin`, `weather_conditions`). Backend automatically aligns missing columns to 0.

### Input & Output Formats
* **Input Format (`VerifyRequest` Pydantic schema)**:
  ```json
  {
    "product_id": "PROD-001",
    "manufacturing_location": "Nashik Plant",
    "origin": "India",
    "weather_conditions": "Clear",
    "temperature": 22.5,
    "humidity": 45.0,
    "micro_textures": 0.95,
    "color_printing_patterns": 0.92,
    "geometric_alignment": 0.98,
    "surface_features": 0.90,
    "printing_artifacts": 0.96,
    "frequency_features": 0.85,
    "color_space_metrics": 0.94,
    "spectral_metrics": 0.91,
    "deep_learning_latent_features": 0.88,
    "qr_code_integrity": 0.99,
    "barcode_integrity": 0.99,
    "product_network": null
  }
  ```
* **Output Format (`VerifyResponse` Pydantic schema)**:
  ```json
  {
    "status": "authentic",
    "message": "AUTHENTIC: Product is verified on-chain and scan patterns are standard.",
    "ai_metrics": {
      "authenticity_probability": 0.94,
      "anomaly_score": 0.06,
      "flags": [],
      "model_scores": {
        "random_forest": {
          "authenticity_prob": 0.94,
          "counterfeit_prob": 0.06
        },
        "gnn_network": null
      }
    },
    "blockchain_receipt": { ... }
  }
  ```

### Inference & Anomaly Scoring Process
* Executed by `AIClient` singleton in `backend/app/ai_client.py`.
* **Ensemble Weighting**: When both models are available, calculates `combined_authenticity = 0.6 * RF_authenticity + 0.4 * GNN_authenticity`.
* **Anomaly Score Calculation**: $\text{Anomaly Score} = 1.0 - \text{Authenticity Probability}$.
* **Verdict Rules**:
  * Anomaly Score $> 0.6$ or $\ge 2$ physical flags $\rightarrow$ `counterfeit` / `suspicious`.
  * Anomaly Score $< 0.4$ and $0$ flags $\rightarrow$ `authentic`.

### Backend Service Exposure & Environment Variables
* Exposed via Flask REST server (`main.py`) running default on port `8000`.
* **Environment Variables**:
  * `APP_NAME` (default: "AuthentiQ API Gateway")
  * `DATABASE_URL` (default: `sqlite:///./authentiq.db`)
  * `RPC_URL` (default: `http://localhost:8545`)
  * `CONTRACT_ADDRESS`
  * `CONTRACT_ABI_PATH`
  * `RF_MODEL_PATH`
  * `GNN_MODEL_PATH`

---

## 3. Dependencies Matrix

| Module | Category | Library / Dependency | Version / Range | Purpose |
| :--- | :--- | :--- | :--- | :--- |
| **Blockchain** | Smart Contract | `@openzeppelin/contracts` | `^5.0.2` | AccessControl role management |
| **Blockchain** | Dev Framework | `hardhat` | `^2.22.3` | EVM contract compilation & testing |
| **Blockchain** | Dev Framework | `@nomicfoundation/hardhat-toolbox` | `^5.0.0` | Ethers, Chai, & Hardhat plugins |
| **Blockchain** | Server / Web3 | `express` | `^4.19.2` | REST API HTTP Web Server |
| **Blockchain** | Server / Web3 | `dotenv` | `^16.4.5` | Environment variable loader |
| **Blockchain** | Server / Web3 | `ethers` | `^6.0.0` | EVM RPC Provider & Wallet Signer |
| **AI** | Machine Learning | `scikit-learn` | `1.5.0` | Random Forest Classifier |
| **AI** | Data Science | `pandas` | `2.2.2` | Dataframe manipulation & dummies |
| **AI** | Data Science | `numpy` | `1.26.4` | Matrix computations & arrays |
| **AI** | Model Persistence | `joblib` | `1.4.2` | Serialization of RF model binaries |
| **AI** | Deep Learning | `torch` | `2.3.1` / `2.4.0` | PyTorch GNN tensor computation |
| **AI** | Graph Neural Nets | `torch-geometric` | `2.5.0` | PyG Graph Convolution Layers |
| **AI** | Graph Analytics | `networkx` | `3.2` | Graph construction utilities |
| **AI** | Web Framework | `Flask` | `3.0.3` | REST Backend Application Gateway |
| **AI** | CORS Middleware | `Flask-Cors` | `4.0.1` | Cross-Origin Resource Sharing |
| **AI** | Database ORM | `sqlalchemy` | `2.0.31` | SQL Database ORM mapping |
| **AI** | Database Driver | `psycopg2-binary` | `2.9.9` | PostgreSQL database adapter |
| **AI** | Data Validation | `pydantic` | `2.7.4` | Request/Response schema validation |
| **AI** | Config Management | `pydantic-settings` | `2.3.4` | Environment settings parser |
| **AI** | Web3 Integration | `web3` | `>=7.0.0` | Python Web3 Ethereum client |

---

## 4. APIs & Functions Currently Available

### A. Blockchain Module APIs (`AuthentiQ-Blockchain-main/server.js`)
* **`GET /health`**: Checks server status and Web3 provider network details (`name`, `chainId`).
* **`POST /api/products/register`**: Registers product with manufacturer route on-chain. Accepts `productId`, `manufacturerName`, `batchNumber`, `manufacturingDate`, `expiryDate`, `productHash`, `currentLocation`, `nextLocation`.
* **`POST /api/products/update-location`**: Updates product next target location. Accepts `productId`, `nextLocation`, `details`.
* **`GET /api/products/verify/:productId`**: Queries on-chain birth certificate and location history log.
* **`GET /api/products/qr-payload/:productId`**: Generates standardized QR code verification payload.

### B. AI Module APIs (`AUTHENIQ-AI-main/backend/app/main.py`)
* **`GET /`**: Welcome & health check endpoint.
* **`POST /api/register`**: Registers product in SQLite DB and calls mock/on-chain contract. Accepts `product_id`, `name`, `batch_number`, `production_location`.
* **`POST /api/verify`**: Executes full verification pipeline (Blockchain read + AI optical/anomaly evaluation + On-chain scan logging + SQL scan history logging). Accepts 17 optical/environmental fields + optional `product_network`.
* **`GET /api/product/<product_id>`**: Retrieves product details, total scan count, complete SQL scan history, and blockchain status.

---

## 5. Integration Points

```
                               ┌───────────────────────────┐
                               │  User / Client (Frontend) │
                               └─────────────┬─────────────┘
                                             │ HTTP Request
                               ┌─────────────▼─────────────┐
                               │  Unified Backend Gateway  │
                               └──────┬─────────────┬──────┘
                                      │             │
                    ┌─────────────────┘             └─────────────────┐
                    │ Internal Call                                   │ RPC / Web3
       ┌────────────▼────────────┐                       ┌────────────▼────────────┐
       │   AI Engine Service     │                       │    Blockchain Service   │
       │ (RF + GNN Models)       │                       │ (ProductVerification)   │
       └─────────────────────────┘                       └─────────────────────────┘
```

1. **Product Registration Phase**:
   * Frontend submits product metadata to Backend.
   * Backend generates cryptographic `productHash` ($H = \text{keccak256}(\text{productId} \parallel \text{manufacturer} \parallel \text{batch})$).
   * Backend writes product baseline record to relational database.
   * Backend invokes Blockchain module (`ProductVerification.sol:registerProduct`) to mint the immutable birth certificate with declared supply chain origin and target destination.
2. **Product Scan & Verification Phase**:
   * Consumer/Inspector scans QR code on physical product item.
   * Client sends scan payload (`productId`, location, physical/optical metrics, device metadata) to Backend.
   * Backend reads golden record from Blockchain (`ProductVerification.sol:verifyProduct`) to confirm registration and verify expected supply chain location.
   * Backend feeds scan metrics into `AIClient` (Random Forest + GNN) to calculate `authenticity_probability` and `anomaly_score`.
   * If AI flags an anomaly or location violation, Backend invokes Blockchain module (`ProductVerification.sol:updateProductStatus`) to mark item as `SUSPICIOUS` or `RECALLED`.
   * Backend saves scan audit event to relational database and returns unified verification receipt to client.

---

## 6. Identified Problems & Incompatibilities

> [!WARNING]
> Critical architectural discrepancies exist between the two codebases that must be resolved prior to unified deployment.

1. **Smart Contract Interface Incompatibility**:
   * `AUTHENIQ-AI-main/backend/app/blockchain_client.py` was built to interface with `AuthentiQRegistry.sol` (which uses methods `getProduct()`, `recordScan()`, `getTokenId()`, and ERC-721 token minting).
   * `AuthentiQ-Blockchain-main/contracts/ProductVerification.sol` implements a completely different interface (`registerProduct()`, `registerProductBatch()`, `updateNextLocation()`, `updateProductStatus()`, `verifyProduct()`, `getLocationHistory()`, `productExists()`).
   * **Impact**: `blockchain_client.py` will fail with missing method reverts if connected directly to `ProductVerification.sol`.

2. **Dual Backend & Framework Fragmentation**:
   * The Blockchain repository relies on a Node.js/Express server (`server.js`) on port `3000`.
   * The AI repository relies on a Python/Flask server (`main.py`) on port `8000`.
   * **Impact**: Redundant endpoints (`/api/register`), split business logic, higher deployment complexity, and unnecessary inter-service network hops.

3. **Database Schema Deficit**:
   * The current SQLAlchemy ORM models (`AUTHENIQ-AI-main/backend/app/models.py`) only store basic fields (`product_id`, `name`, `batch_number`, `production_location`).
   * Crucial blockchain parameters (`expiry_date`, `product_hash`, `current_location`, `next_location`, `status`, `transaction_hash`, `block_number`) are omitted from the relational database schema.

4. **Lack of Authentication & Wallet Security**:
   * Neither codebase provides user authentication (JWT/OAuth2) or Role-Based Access Control (RBAC) at the HTTP layer.
   * `server.js` and `blockchain_client.py` rely on hardcoded server-side private keys (`MANUFACTURER_PRIVATE_KEY`), allowing any unauthenticated user to register products or alter supply chain routes.

5. **AI Input Feature Imputation Gap**:
   * The advanced Random Forest model requires 16 complex physical/optical features (`micro_textures`, `spectral_metrics`, `deep_learning_latent_features`, etc.).
   * Real-world mobile QR scans only transmit `product_id`, GPS coordinates, and timestamp.
   * **Impact**: Direct API calls without optical analysis payload fail validation or produce inaccurate inference scores without a feature imputer layer.

---

## 7. Recommended Backend Architecture

To achieve production-grade performance, maintainability, and scalability, we recommend consolidating both codebases into a single **Unified Python FastAPI Application Gateway**.

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    RECOMMENDED UNIFIED BACKEND ARCHITECTURE             │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌───────────────────────────────────────────────────────────────────┐  │
│  │                    API Gateway Layer (FastAPI)                    │  │
│  │  - CORS Middleware  - Rate Limiter  - JWT / OAuth2 RBAC Auth      │  │
│  └─────────────────────────────────┬─────────────────────────────────┘  │
│                                    │                                    │
│       ┌────────────────────────────┼────────────────────────────┐       │
│       │                            │                            │       │
│  ┌────▼────────────────────┐  ┌────▼────────────────────┐  ┌────▼────▼──────────────┐  │
│  │ Product & Supply Chain  │  │ AI Anomaly Engine       │  │ Web3 Blockchain Bridge │  │
│  │ Service                 │  │ Service                 │  │ Service                │  │
│  │ - Product Lifecycle     │  │ - RF Optical Model      │  │ - Web3.py / Ethers     │  │
│  │ - Route History         │  │ - GNN Network Model     │  │ - ProductVerification  │  │
│  │ - QR Payload Generator  │  │ - Imputer Preprocessor  │  │ - Nonce & Gas Manager  │  │
│  └────────────┬────────────┘  └────────────┬────────────┘  └────────────┬───────────┘  │
│               │                            │                            │             │
│               └────────────────────────────┼────────────────────────────┘             │
│                                            │                                          │
│                              ┌─────────────▼─────────────┐                            │
│                              │  Persistence Layer        │                            │
│                              │  PostgreSQL + Redis Cache │                            │
│                              └───────────────────────────┘                            │
└─────────────────────────────────────────────────────────────────────────┘
```

### Core Architecture Components
1. **Framework**: FastAPI (Asynchronous Python 3.10+) for high-throughput async processing and automatic OpenAPI/Swagger specification generation.
2. **Blockchain Bridge Module (`app/services/blockchain_service.py`)**: Python `web3.py` wrapper updated specifically to match `ProductVerification.sol` ABI methods.
3. **AI Anomaly Engine (`app/services/ai_service.py`)**: Refactored `AIClient` with an automatic **Feature Imputer & Default Metrics Generator** for standard QR mobile scans.
4. **Asynchronous Task Queue (Celery + Redis)**: Handles background transaction mining and batch registrations without blocking client responses.

---

## 8. Recommended Authentication Architecture

Security requires aligning **HTTP Application RBAC** with **On-Chain AccessControl Roles**.

```
┌─────────────────────────────────────────────────────────────────────────┐
│                     AUTHENTICATION & ACCESS CONTROL MAP                 │
└─────────────────────────────────────────────────────────────────────────┘

  HTTP User Role                JWT Claims                   Blockchain Contract Role
 ┌──────────────┐             ┌────────────┐               ┌──────────────────────────┐
 │ Admin        │ ──────────> │ role: admin│ ────────────> │ DEFAULT_ADMIN_ROLE       │
 └──────────────┘             └────────────┘               └──────────────────────────┘
 ┌──────────────┐             ┌────────────┐               ┌──────────────────────────┐
 │ Manufacturer │ ──────────> │ role: mfr  │ ────────────> │ MANUFACTURER_ROLE        │
 └──────────────┘             └────────────┘               └──────────────────────────┘
 ┌──────────────┐             ┌────────────┐               ┌──────────────────────────┐
 │ Inspector    │ ──────────> │ role: insp │ ────────────> │ INSPECTOR_ROLE           │
 └──────────────┘             └────────────┘               └──────────────────────────┘
 ┌──────────────┐             ┌────────────┐               ┌──────────────────────────┐
 │ Consumer     │ ──────────> │ role: public│ ───────────> │ Free View Calls Only     │
 └──────────────┘             └────────────┘               └──────────────────────────┘
```

### Key Security Protocols
1. **JWT Authentication**: Users log in with credentials and receive an RS256-signed JWT containing `user_id`, `email`, `role`, and assigned `wallet_address`.
2. **Wallet Key Vault**:
   * System transactions use encrypted private keys stored in environment secrets or HashiCorp Vault.
   * Endpoints requiring `MANUFACTURER_ROLE` or `INSPECTOR_ROLE` verify JWT signatures before executing contract transactions.
3. **Password Security**: Passwords hashed using `bcrypt` (12 rounds).

---

## 9. Recommended Database Structure

To support full provenance, AI scoring history, and supply chain target routes, the database schema must be expanded as follows:

```
┌──────────────────┐       1:N       ┌──────────────────────┐
│      users       │ ───────────────<│       products       │
└──────────────────┘                 └──────────┬───────────┘
                                                │
                                       1:N      │      1:N
                        ┌───────────────────────┴───────────────────────┐
                        │                                               │
               ┌────────▼─────────────┐                       ┌─────────▼────────────┐
               │   location_history   │                       │     scan_history     │
               └──────────────────────┘                       └──────────────────────┘
```

### SQL DDL Schema Specification

```sql
-- 1. Users Table
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(50) NOT NULL CHECK (role IN ('ADMIN', 'MANUFACTURER', 'INSPECTOR', 'CONSUMER')),
    wallet_address VARCHAR(42),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 2. Products Table (Golden Provenance Record)
CREATE TABLE products (
    id SERIAL PRIMARY KEY,
    product_id VARCHAR(100) UNIQUE NOT NULL,
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
    registered_by_id INT REFERENCES users(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 3. Location History Table (Supply Chain Route Audit Log)
CREATE TABLE location_history (
    id SERIAL PRIMARY KEY,
    product_id VARCHAR(100) REFERENCES products(product_id) ON DELETE CASCADE,
    location_name VARCHAR(255) NOT NULL,
    details TEXT,
    updated_by_address VARCHAR(42) NOT NULL,
    tx_hash VARCHAR(66),
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 4. Scan History Table (AI Inspection & Verification Audit Log)
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
    flags TEXT, -- Comma-separated or JSON list of flags
    raw_optical_metrics JSONB, -- Complete JSON scan payload
    scan_tx_hash VARCHAR(66),
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
```

---

## 10. Required Environment Variables

```env
# ==============================================================================
# AUTHENIQ INTEGRATED SYSTEM ENVIRONMENT CONFIGURATION
# ==============================================================================

# General Application Configuration
APP_ENV=development
APP_PORT=8000
SECRET_KEY=super-secret-jwt-signing-key-change-in-production

# Persistence Layer Configuration
DATABASE_URL=postgresql://authentiq_user:secure_password@localhost:5432/authentiq_db

# EVM Blockchain Network Settings
RPC_URL=http://127.0.0.1:8545
CHAIN_ID=1337
CONTRACT_ADDRESS=0x5FbDB2315678afecb367f032d93F642f64180aa3
CONTRACT_ABI_PATH=app/contracts/ProductVerification.json

# Authorized Signer Keys (Key Vault Managed in Production)
ADMIN_PRIVATE_KEY=0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80
MANUFACTURER_PRIVATE_KEY=0x59c6995e998f97a5a0044966f0945389dc9e86dae88c7a8412f4603b6b78690d
INSPECTOR_PRIVATE_KEY=0x5de4111407a93169b73250246214a57350280f4991a500500753b27730178387

# AI Model Files Configuration
RF_MODEL_PATH=app/models/rf_advanced_model.joblib
GNN_MODEL_PATH=app/models/gnn_advanced_model.pt

# Frontend & CORS Settings
FRONTEND_URL=http://localhost:3000
ALLOWED_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
```

---

## 11. Step-by-Step Integration Plan

```
┌─────────────────────────────────────────────────────────────────────────┐
│                       INTEGRATION EXECUTION ROADMAP                     │
└─────────────────────────────────────────────────────────────────────────┘

  [Phase 1] Smart Contract & Web3 Client Realignment
     │
  [Phase 2] Database ORM Migration & Schema Upgrade
     │
  [Phase 3] Unified FastAPI Gateway Development
     │
  [Phase 4] AI Inference & Imputation Pipeline Integration
     │
  [Phase 5] Security, JWT Auth & Key Vault Integration
     │
  [Phase 6] System Verification & End-to-End Testing
```

### Phase 1: Smart Contract & Web3 Client Realignment
1. Standardize on `ProductVerification.sol` from `AuthentiQ-Blockchain-main` as the primary contract.
2. Compile contract artifacts using Hardhat and export `ProductVerification.json` to the backend service contracts folder (`backend/app/contracts/ProductVerification.json`).
3. Rewrite `backend/app/blockchain_client.py` to match `ProductVerification.sol` function signatures (`registerProduct`, `updateNextLocation`, `updateProductStatus`, `verifyProduct`, `getLocationHistory`).

### Phase 2: Database ORM Migration & Schema Upgrade
1. Update SQLAlchemy models in `backend/app/models.py` to implement `User`, `Product`, `LocationHistory`, and `ScanHistory` tables matching Section 9 schema.
2. Setup Alembic migration scripts for zero-downtime database upgrades.

### Phase 3: Unified FastAPI Gateway Development
1. Consolidate backend routes into a structured FastAPI router hierarchy:
   * `/api/v1/auth` (Login, Registration, Token Refresh)
   * `/api/v1/products` (Register, Batch Register, Update Route, Verify, History)
   * `/api/v1/ai` (Standalone Scan Diagnostics, Model Health)
2. Implement custom CORS and Pydantic exception handlers.

### Phase 4: AI Inference & Imputation Pipeline Integration
1. Update `AIClient` in `ai_client.py` to safely handle missing optical features by generating standard imputation defaults for mobile QR scans.
2. Ensure PyTorch CPU compatibility gracefully handles environments without GPU or PyG installed.

### Phase 5: Security, JWT Auth & Key Vault Integration
1. Implement JWT bearer token authentication middleware.
2. Restrict product registration endpoints to authenticated users with `MANUFACTURER` role.
3. Restrict status flagging endpoints to users with `INSPECTOR` role.

### Phase 6: System Verification & End-to-End Testing
1. Run local Hardhat blockchain node.
2. Execute automated test suite covering:
   * Unit tests for `ProductVerification.sol`.
   * Unit tests for `AIClient` (Random Forest + GNN inference).
   * Integration tests for FastAPI registration and verification endpoints.
3. Validate client frontend integration with unified backend API gateway.

---

> [!NOTE]
> All source code files remain untouched in accordance with instructions. Implementation will begin upon explicit user approval of this integration blueprint.
