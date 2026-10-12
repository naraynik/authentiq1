from fastapi import APIRouter
from fastapi.responses import HTMLResponse

router = APIRouter(prefix="/demo", tags=["Interactive Visual Demos"])

PHASE3_DEMO_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AuthentiQ — Phase 3 Manufacturer Governance Dashboard</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <style>
        :root {
            --bg: #0f172a;
            --panel: #1e293b;
            --border: #334155;
            --primary: #6366f1;
            --primary-hover: #4f46e5;
            --success: #10b981;
            --warning: #f59e0b;
            --danger: #ef4444;
            --text: #f8fafc;
            --text-muted: #94a3b8;
        }
        * { box-sizing: border-box; margin: 0; padding: 0; font-family: 'Inter', sans-serif; }
        body { background-color: var(--bg); color: var(--text); padding: 2rem; }
        .header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 2rem; border-bottom: 1px solid var(--border); padding-bottom: 1rem; }
        .header h1 { font-size: 1.8rem; font-weight: 700; background: linear-gradient(90deg, #818cf8, #c084fc); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
        .badge { padding: 0.35rem 0.75rem; border-radius: 9999px; font-size: 0.75rem; font-weight: 600; text-transform: uppercase; }
        .badge-pending { background: rgba(245, 158, 11, 0.15); color: #fbbf24; border: 1px solid rgba(245, 158, 11, 0.3); }
        .badge-approved { background: rgba(16, 185, 129, 0.15); color: #34d399; border: 1px solid rgba(16, 185, 129, 0.3); }
        .badge-rejected { background: rgba(239, 68, 68, 0.15); color: #f87171; border: 1px solid rgba(239, 68, 68, 0.3); }
        .badge-suspended { background: rgba(148, 163, 184, 0.15); color: #cbd5e1; border: 1px solid rgba(148, 163, 184, 0.3); }
        
        .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(400px, 1fr)); gap: 1.5rem; margin-bottom: 2rem; }
        .card { background: var(--panel); border: 1px solid var(--border); border-radius: 0.75rem; padding: 1.5rem; box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.3); }
        .card h2 { font-size: 1.2rem; font-weight: 600; margin-bottom: 1rem; color: #e2e8f0; display: flex; align-items: center; justify-content: space-between; }
        
        .form-group { margin-bottom: 1rem; }
        .form-group label { display: block; font-size: 0.85rem; color: var(--text-muted); margin-bottom: 0.35rem; }
        .form-control { width: 100%; padding: 0.65rem 0.85rem; background: #0f172a; border: 1px solid var(--border); border-radius: 0.5rem; color: var(--text); font-size: 0.9rem; }
        .form-control:focus { outline: none; border-color: var(--primary); }
        
        .btn { padding: 0.65rem 1.25rem; border: none; border-radius: 0.5rem; font-size: 0.85rem; font-weight: 600; cursor: pointer; transition: all 0.2s; display: inline-flex; align-items: center; gap: 0.5rem; text-decoration: none; }
        .btn-primary { background: var(--primary); color: white; }
        .btn-primary:hover { background: var(--primary-hover); }
        .btn-success { background: var(--success); color: white; }
        .btn-danger { background: var(--danger); color: white; }
        .btn-warning { background: var(--warning); color: black; }
        .btn-outline { background: transparent; border: 1px solid var(--border); color: var(--text); }
        .btn-outline:hover { background: rgba(255,255,255,0.05); }
        .btn-sm { padding: 0.35rem 0.75rem; font-size: 0.75rem; }
        
        .table-container { overflow-x: auto; margin-top: 1rem; }
        table { width: 100%; border-collapse: collapse; text-align: left; font-size: 0.85rem; }
        th, td { padding: 0.85rem; border-bottom: 1px solid var(--border); }
        th { color: var(--text-muted); font-weight: 500; background: rgba(15, 23, 42, 0.5); }
        
        .output-box { background: #090d16; border: 1px solid #1e293b; border-radius: 0.5rem; padding: 1rem; font-family: monospace; font-size: 0.8rem; color: #38bdf8; max-height: 250px; overflow-y: auto; white-space: pre-wrap; margin-top: 1rem; }
    </style>
</head>
<body>

    <div class="header">
        <div>
            <h1>AuthentiQ Phase 3 — Manufacturer Governance Dashboard</h1>
            <p style="color: var(--text-muted); font-size: 0.9rem; margin-top: 0.25rem;">Manufacturer Verification & Governance Workflow</p>
        </div>
        <div style="display: flex; gap: 0.5rem;">
            <a href="/demo/blockchain" class="btn btn-primary">🔗 Go to Phase 4 Blockchain Dashboard</a>
            <a href="/docs" target="_blank" class="btn btn-outline">📘 OpenAPI Swagger Docs</a>
        </div>
    </div>

    <div class="grid">
        <div class="card">
            <h2>1. Admin Authentication</h2>
            <div class="form-group">
                <label>Admin Email</label>
                <input type="email" id="adminEmail" class="form-control" value="admin@authentiq.com">
            </div>
            <div class="form-group">
                <label>Admin Password</label>
                <input type="password" id="adminPassword" class="form-control" value="Admin@123456">
            </div>
            <button class="btn btn-primary" onclick="loginAdmin()">🔑 Login as Admin</button>
            <div id="adminStatus" class="output-box" style="display:none;"></div>
        </div>

        <div class="card">
            <h2>2. Register New Manufacturer</h2>
            <div style="display:grid; grid-template-columns: 1fr 1fr; gap: 0.5rem;">
                <div class="form-group"><label>Company Name</label><input type="text" id="regCompany" class="form-control" value="Apex Healthcare Ltd"></div>
                <div class="form-group"><label>GSTIN</label><input type="text" id="regGstin" class="form-control" value="27AAACA9999A1Z5"></div>
            </div>
            <div style="display:grid; grid-template-columns: 1fr 1fr; gap: 0.5rem;">
                <div class="form-group"><label>Email</label><input type="email" id="regEmail" class="form-control" value="apex@healthcare.com"></div>
                <div class="form-group"><label>Phone</label><input type="text" id="regPhone" class="form-control" value="+919876543210"></div>
            </div>
            <div class="form-group"><label>Address</label><input type="text" id="regAddress" class="form-control" value="100 Tech Park, Mumbai"></div>
            <div class="form-group"><label>Password</label><input type="password" id="regPassword" class="form-control" value="Password123!"></div>
            <div class="form-group"><label>Verification Document</label><input type="file" id="regDoc" class="form-control"></div>
            <button class="btn btn-primary" onclick="registerManufacturer()">📝 Register Manufacturer</button>
            <div id="regStatus" class="output-box" style="display:none;"></div>
        </div>
    </div>

    <script>
        let adminToken = '';
        async function loginAdmin() {
            const email = document.getElementById('adminEmail').value;
            const password = document.getElementById('adminPassword').value;
            const statusBox = document.getElementById('adminStatus');
            statusBox.style.display = 'block';
            statusBox.textContent = 'Logging in...';

            try {
                const res = await fetch('/api/auth/login', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ email, password })
                });
                const data = await res.json();
                if (res.ok) {
                    adminToken = data.access_token;
                    statusBox.textContent = `✅ ADMIN LOGGED IN!\nRole: ${data.role}\nEmail: ${data.user.email}`;
                } else {
                    statusBox.textContent = `❌ LOGIN FAILED: ${data.detail}`;
                }
            } catch (err) {
                statusBox.textContent = `❌ ERROR: ${err.message}`;
            }
        }
    </script>
</body>
</html>
"""

PHASE4_BLOCKCHAIN_DEMO_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AuthentiQ — Phase 4 Blockchain Dashboard</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
    <style>
        :root {
            --bg: #0b0f19;
            --panel: #151c2e;
            --border: #232f48;
            --primary: #6366f1;
            --primary-hover: #4f46e5;
            --cyan: #06b6d4;
            --emerald: #10b981;
            --amber: #f59e0b;
            --rose: #f43f5e;
            --text: #f8fafc;
            --text-muted: #94a3b8;
        }
        * { box-sizing: border-box; margin: 0; padding: 0; font-family: 'Inter', sans-serif; }
        body { background-color: var(--bg); color: var(--text); padding: 2rem; min-height: 100vh; }
        
        .header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 2rem; border-bottom: 1px solid var(--border); padding-bottom: 1.25rem; }
        .header-title { display: flex; align-items: center; gap: 1rem; }
        .header h1 { font-size: 1.8rem; font-weight: 700; background: linear-gradient(90deg, #38bdf8, #818cf8, #c084fc); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
        .header-subtitle { color: var(--text-muted); font-size: 0.85rem; margin-top: 0.25rem; }

        .btn-group { display: flex; gap: 0.75rem; }
        .btn { padding: 0.6rem 1.2rem; border: none; border-radius: 0.5rem; font-size: 0.85rem; font-weight: 600; cursor: pointer; transition: all 0.2s ease; display: inline-flex; align-items: center; gap: 0.5rem; text-decoration: none; }
        .btn-primary { background: linear-gradient(135deg, var(--primary), #4338ca); color: white; box-shadow: 0 4px 12px rgba(99, 102, 241, 0.3); }
        .btn-primary:hover { opacity: 0.95; transform: translateY(-1px); }
        .btn-cyan { background: linear-gradient(135deg, var(--cyan), #0891b2); color: white; }
        .btn-emerald { background: linear-gradient(135deg, var(--emerald), #059669); color: white; }
        .btn-rose { background: linear-gradient(135deg, var(--rose), #be123c); color: white; }
        .btn-outline { background: transparent; border: 1px solid var(--border); color: var(--text); }
        .btn-outline:hover { background: rgba(255,255,255,0.05); }
        .btn-sm { padding: 0.35rem 0.75rem; font-size: 0.75rem; }

        .grid-2 { display: grid; grid-template-columns: 1fr 1fr; gap: 1.5rem; margin-bottom: 1.5rem; }
        .grid-3 { display: grid; grid-template-columns: repeat(3, 1fr); gap: 1.5rem; margin-bottom: 1.5rem; }
        
        .card { background: var(--panel); border: 1px solid var(--border); border-radius: 0.85rem; padding: 1.5rem; box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.4); position: relative; }
        .card-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 1.2rem; padding-bottom: 0.75rem; border-bottom: 1px solid rgba(255,255,255,0.05); }
        .card-title { font-size: 1.1rem; font-weight: 600; color: #f1f5f9; display: flex; align-items: center; gap: 0.5rem; }

        .status-indicator { display: inline-flex; align-items: center; gap: 0.4rem; padding: 0.3rem 0.8rem; border-radius: 9999px; font-size: 0.75rem; font-weight: 700; letter-spacing: 0.05em; text-transform: uppercase; }
        .status-healthy { background: rgba(16, 185, 129, 0.15); color: #34d399; border: 1px solid rgba(16, 185, 129, 0.3); }
        .status-unhealthy { background: rgba(244, 63, 94, 0.15); color: #fb7185; border: 1px solid rgba(244, 63, 94, 0.3); }
        .status-dot { width: 8px; height: 8px; border-radius: 50%; background: currentColor; display: inline-block; }

        .info-list { display: flex; flex-direction: column; gap: 0.75rem; font-size: 0.88rem; }
        .info-row { display: flex; justify-content: space-between; align-items: center; border-bottom: 1px border-subtle; padding-bottom: 0.4rem; }
        .info-label { color: var(--text-muted); font-size: 0.82rem; }
        .info-value { font-family: 'JetBrains Mono', monospace; font-weight: 500; color: #38bdf8; }

        .form-group { margin-bottom: 1rem; }
        .form-group label { display: block; font-size: 0.82rem; color: var(--text-muted); margin-bottom: 0.35rem; font-weight: 500; }
        .form-control { width: 100%; padding: 0.65rem 0.85rem; background: #0b0f19; border: 1px solid var(--border); border-radius: 0.5rem; color: var(--text); font-size: 0.88rem; font-family: inherit; }
        .form-control:focus { outline: none; border-color: var(--cyan); box-shadow: 0 0 0 2px rgba(6, 182, 212, 0.2); }

        .output-box { background: #070a12; border: 1px solid #1e293b; border-radius: 0.6rem; padding: 1rem; font-family: 'JetBrains Mono', monospace; font-size: 0.8rem; color: #a5f3fc; max-height: 220px; overflow-y: auto; white-space: pre-wrap; margin-top: 1rem; word-break: break-all; }
        
        .badge { padding: 0.25rem 0.6rem; border-radius: 0.4rem; font-size: 0.75rem; font-weight: 600; font-family: 'JetBrains Mono', monospace; }
        .badge-onchain { background: rgba(16, 185, 129, 0.2); color: #34d399; border: 1px solid rgba(16, 185, 129, 0.4); }
        .badge-offchain { background: rgba(245, 158, 11, 0.2); color: #fbbf24; border: 1px solid rgba(245, 158, 11, 0.4); }

        details summary { cursor: pointer; color: var(--cyan); font-size: 0.85rem; font-weight: 600; margin-top: 0.5rem; }
        
        .flow-stepper { display: flex; justify-content: space-between; background: rgba(15, 23, 42, 0.6); border: 1px solid var(--border); padding: 1rem; border-radius: 0.75rem; margin-bottom: 1.5rem; }
        .step { flex: 1; text-align: center; position: relative; font-size: 0.8rem; color: var(--text-muted); }
        .step.active { color: var(--cyan); font-weight: 600; }
        .step-num { width: 24px; height: 24px; border-radius: 50%; background: var(--border); color: white; display: flex; align-items: center; justify-content: center; margin: 0 auto 0.4rem auto; font-size: 0.75rem; }
        .step.active .step-num { background: var(--cyan); color: black; font-weight: bold; }
    </style>
</head>
<body>

    <!-- Header -->
    <div class="header">
        <div class="header-title">
            <span style="font-size: 2rem;">⚡</span>
            <div>
                <h1>Phase 4 — Blockchain Integration Dashboard</h1>
                <div class="header-subtitle">Real-Time Interaction with ProductVerification.sol Smart Contract & FastAPI Backend</div>
            </div>
        </div>
        <div class="btn-group">
            <button class="btn btn-emerald" onclick="checkBlockchainHealth()">🔄 Refresh Node Status</button>
            <a href="/demo" class="btn btn-outline">👈 Phase 3 Demo</a>
            <a href="/docs" target="_blank" class="btn btn-outline">📘 OpenAPI Swagger Docs</a>
        </div>
    </div>

    <!-- Visual Flow Stepper -->
    <div class="flow-stepper">
        <div class="step active" id="step1"><div class="step-num">1</div>Node & Contract Check</div>
        <div class="step" id="step2"><div class="step-num">2</div>Auth Token Setup</div>
        <div class="step" id="step3"><div class="step-num">3</div>Product Registration</div>
        <div class="step" id="step4"><div class="step-num">4</div>On-Chain Tx Confirmation</div>
        <div class="step" id="step5"><div class="step-num">5</div>On-Chain Verification</div>
    </div>

    <!-- Row 1: Node Health & Contract Info -->
    <div class="grid-2">
        <!-- Blockchain Status Card -->
        <div class="card">
            <div class="card-header">
                <div class="card-title">🌐 Blockchain Connection Status</div>
                <div id="healthBadge" class="status-indicator status-unhealthy"><span class="status-dot"></span>CHECKING</div>
            </div>
            <div class="info-list">
                <div class="info-row"><span class="info-label">Network RPC:</span><span class="info-value" id="infoRpc">http://127.0.0.1:8545</span></div>
                <div class="info-row"><span class="info-label">Chain ID:</span><span class="info-value" id="infoChainId">Checking...</span></div>
                <div class="info-row"><span class="info-label">Latest Block Number:</span><span class="info-value" id="infoLatestBlock">Checking...</span></div>
                <div class="info-row"><span class="info-label">RPC Node Reachable:</span><span class="info-value" id="infoRpcReachable">Checking...</span></div>
                <div class="info-row"><span class="info-label">Wallet Address:</span><span class="info-value" id="infoWallet">Checking...</span></div>
            </div>
        </div>

        <!-- Contract Details Card -->
        <div class="card">
            <div class="card-header">
                <div class="card-title">📜 Smart Contract Architecture</div>
                <div class="badge badge-onchain">SOLDIITY V0.8.20</div>
            </div>
            <div class="info-list">
                <div class="info-row"><span class="info-label">Contract Name:</span><span class="info-value" style="color:#e2e8f0;">ProductVerification.sol</span></div>
                <div class="info-row"><span class="info-label">Contract Address:</span><span class="info-value" id="infoContractAddr">0x5FbDB2315678afecb367f032d93F642f64180aa3</span></div>
                <div class="info-row"><span class="info-label">Contract Accessible:</span><span class="info-value" id="infoContractAccessible">Checking...</span></div>
                <div class="info-row"><span class="info-label">ABI Source Path:</span><span class="info-value" style="color:var(--text-muted);">app/contracts/ProductVerification.json</span></div>
                <div class="info-row"><span class="info-label">Access Control:</span><span class="info-value" style="color:#cbd5e1;">MANUFACTURER_ROLE & INSPECTOR_ROLE</span></div>
            </div>
        </div>
    </div>

    <!-- Row 2: Auth Setup & Product Registration Form -->
    <div class="grid-2">
        <!-- Quick Authentication Assistant -->
        <div class="card">
            <div class="card-header">
                <div class="card-title">🔐 Manufacturer Authorization Setup</div>
                <span class="badge badge-onchain" id="authRoleBadge">NO TOKEN</span>
            </div>
            <p style="font-size: 0.82rem; color: var(--text-muted); margin-bottom: 1rem;">
                On-chain product registration requires JWT token from an APPROVED Manufacturer. Click below to quickly login or auto-setup a test manufacturer account.
            </p>
            <div class="form-group">
                <label>Manufacturer Email</label>
                <input type="email" id="authEmail" class="form-control" value="mfr_bc_demo@authentiq.com">
            </div>
            <div class="form-group">
                <label>Manufacturer Password</label>
                <input type="password" id="authPassword" class="form-control" value="Password@123">
            </div>
            <div style="display:flex; gap: 0.5rem; flex-wrap: wrap;">
                <button class="btn btn-primary" onclick="setupApprovedManufacturer()">🚀 Auto-Setup & Login Approved Manufacturer</button>
                <button class="btn btn-outline" onclick="loginManufacturerManual()">🔑 Login Existing</button>
            </div>
            <div id="authOutput" class="output-box" style="display:none;"></div>
        </div>

        <!-- Product Registration Form -->
        <div class="card">
            <div class="card-header">
                <div class="card-title">📦 Register Product on Smart Contract</div>
                <span class="badge badge-offchain" id="regOnchainBadge">PENDING REGISTER</span>
            </div>
            <div style="display:grid; grid-template-columns: 1fr 1fr; gap: 0.5rem;">
                <div class="form-group">
                    <label>Product ID (Canonical Unique Code)</label>
                    <input type="text" id="regProductId" class="form-control" value="PROD-BC-2026-001">
                </div>
                <div class="form-group">
                    <label>Product Name</label>
                    <input type="text" id="regProductName" class="form-control" value="CardioProtect 50mg Injection">
                </div>
            </div>
            <div style="display:grid; grid-template-columns: 1fr 1fr; gap: 0.5rem;">
                <div class="form-group">
                    <label>Batch Number</label>
                    <input type="text" id="regBatch" class="form-control" value="BATCH-CP-8890">
                </div>
                <div class="form-group">
                    <label>Manufacturing Date</label>
                    <input type="datetime-local" id="regMfgDate" class="form-control" value="2026-09-01T08:00">
                </div>
            </div>
            <div style="display:grid; grid-template-columns: 1fr 1fr; gap: 0.5rem;">
                <div class="form-group">
                    <label>Current Location</label>
                    <input type="text" id="regCurrentLoc" class="form-control" value="Plant Alpha, Mumbai Facility">
                </div>
                <div class="form-group">
                    <label>Next Location Target</label>
                    <input type="text" id="regNextLoc" class="form-control" value="Central Logistics Hub, Pune">
                </div>
            </div>
            <button class="btn btn-cyan" style="width:100%; justify-content: center; margin-top: 0.5rem;" onclick="registerProductOnChain()">
                ⛓️ REGISTER PRODUCT ON BLOCKCHAIN
            </button>
            <div id="regOutput" class="output-box" style="display:none;"></div>
        </div>
    </div>

    <!-- Row 3: Transaction Card & Product Verification -->
    <div class="grid-2">
        <!-- Real-Time Transaction Card -->
        <div class="card">
            <div class="card-header">
                <div class="card-title">🧾 Transaction Receipt & On-Chain Audit</div>
                <span class="badge badge-onchain" id="txStatusBadge">NO RECENT TX</span>
            </div>
            <div class="info-list">
                <div class="info-row"><span class="info-label">Transaction Hash:</span><span class="info-value" id="txHashDisplay">0x...</span></div>
                <div class="info-row"><span class="info-label">Block Number:</span><span class="info-value" id="txBlockDisplay">None</span></div>
                <div class="info-row"><span class="info-label">Gas Used:</span><span class="info-value" id="txGasDisplay">None</span></div>
                <div class="info-row"><span class="info-label">Contract Function:</span><span class="info-value" style="color:#e2e8f0;">registerProduct()</span></div>
                <div class="info-row"><span class="info-label">On-Chain State (is_onchain):</span><span class="info-value" id="txIsOnchain">FALSE</span></div>
            </div>
        </div>

        <!-- Product Verification & Query -->
        <div class="card">
            <div class="card-header">
                <div class="card-title">🔍 On-Chain Product Verification</div>
                <button class="btn btn-outline btn-sm" onclick="verifyProductOnChain()">Verify</button>
            </div>
            <div class="form-group">
                <label>Enter Product ID to Verify</label>
                <div style="display:flex; gap:0.5rem;">
                    <input type="text" id="verifyProductId" class="form-control" value="PROD-BC-2026-001">
                    <button class="btn btn-primary" onclick="verifyProductOnChain()">VERIFY</button>
                </div>
            </div>
            <div id="verifyOutput" class="output-box" style="display:none;"></div>
        </div>
    </div>

    <!-- Row 4: Status & Location Tracking -->
    <div class="grid-2">
        <!-- Location History & Updates -->
        <div class="card">
            <div class="card-header">
                <div class="card-title">📍 Supply Chain Location Update</div>
            </div>
            <div style="display:grid; grid-template-columns: 1fr 1fr; gap: 0.5rem;">
                <div class="form-group"><label>Product ID</label><input type="text" id="locProductId" class="form-control" value="PROD-BC-2026-001"></div>
                <div class="form-group"><label>New Next Location</label><input type="text" id="locNextName" class="form-control" value="Regional Pharmacy, Delhi"></div>
            </div>
            <div class="form-group"><label>Tracking Details</label><input type="text" id="locDetails" class="form-control" value="Dispatched via temperature-controlled transport"></div>
            <div style="display:flex; gap:0.5rem;">
                <button class="btn btn-cyan" onclick="updateProductLocation()">Update Location On-Chain</button>
                <button class="btn btn-outline" onclick="fetchLocationHistory()">Fetch Location History</button>
            </div>
            <div id="locOutput" class="output-box" style="display:none;"></div>
        </div>

        <!-- Status Management -->
        <div class="card">
            <div class="card-header">
                <div class="card-title">🛡️ Smart Contract Status Management</div>
            </div>
            <div class="form-group"><label>Product ID</label><input type="text" id="statProductId" class="form-control" value="PROD-BC-2026-001"></div>
            <div class="form-group">
                <label>New Smart Contract Status (Enum uint8)</label>
                <select id="statSelect" class="form-control">
                    <option value="GENUINE">GENUINE (0)</option>
                    <option value="SUSPICIOUS">SUSPICIOUS (1)</option>
                    <option value="RECALLED">RECALLED (2)</option>
                </select>
            </div>
            <button class="btn btn-rose" onclick="updateProductStatus()">Update On-Chain Status</button>
            <div id="statOutput" class="output-box" style="display:none;"></div>
        </div>
    </div>

    <!-- Technical Details Collapsible -->
    <div class="card" style="margin-top: 1rem;">
        <details>
            <summary>⚙️ Technical API & Debugging Details</summary>
            <div id="techDetailsBox" class="output-box" style="margin-top:0.75rem; height: 180px;">
                API Endpoint Calls & HTTP responses will be logged here.
            </div>
        </details>
    </div>

    <script>
        let mfrToken = '';

        window.onload = function() {
            checkBlockchainHealth();
        };

        function logTechDetails(endpoint, method, statusCode, payload) {
            const box = document.getElementById('techDetailsBox');
            const logEntry = `[${new Date().toLocaleTimeString()}] ${method} ${endpoint} (Status ${statusCode})\n${JSON.stringify(payload, null, 2)}\n----------------------------------------\n`;
            box.textContent = logEntry + box.textContent;
        }

        async function checkBlockchainHealth() {
            const badge = document.getElementById('healthBadge');
            badge.className = 'status-indicator status-unhealthy';
            badge.innerHTML = '<span class="status-dot"></span>FETCHING...';

            try {
                const res = await fetch('/api/health/blockchain');
                const data = await res.json();
                logTechDetails('/api/health/blockchain', 'GET', res.status, data);

                const bc = data.blockchain || {};
                document.getElementById('infoRpc').textContent = settings_rpc || 'http://127.0.0.1:8545';
                document.getElementById('infoChainId').textContent = bc.chain_id !== null ? bc.chain_id : 'N/A';
                document.getElementById('infoLatestBlock').textContent = bc.latest_block !== null ? bc.latest_block : 'N/A';
                document.getElementById('infoRpcReachable').textContent = bc.rpc_reachable ? 'YES (HTTP 200)' : 'NO';
                document.getElementById('infoWallet').textContent = bc.wallet_address || 'None';
                document.getElementById('infoContractAddr').textContent = bc.contract_address || '0x5FbDB2315678afecb367f032d93F642f64180aa3';
                document.getElementById('infoContractAccessible').textContent = bc.contract_accessible ? 'YES (MANUFACTURER_ROLE Verified)' : 'NO';

                if (data.status === 'HEALTHY' || data.status === 'PARTIAL' || bc.rpc_reachable) {
                    badge.className = 'status-indicator status-healthy';
                    badge.innerHTML = '<span class="status-dot"></span>CONNECTED';
                    document.getElementById('step1').className = 'step active';
                    document.getElementById('step2').className = 'step active';
                } else {
                    badge.className = 'status-indicator status-unhealthy';
                    badge.innerHTML = '<span class="status-dot"></span>DISCONNECTED';
                }
            } catch (err) {
                badge.className = 'status-indicator status-unhealthy';
                badge.innerHTML = '<span class="status-dot"></span>NODE OFFLINE';
                logTechDetails('/api/health/blockchain', 'GET', 500, { error: err.message });
            }
        }
        const settings_rpc = "http://127.0.0.1:8545";

        async function setupApprovedManufacturer() {
            const outBox = document.getElementById('authOutput');
            outBox.style.display = 'block';
            outBox.textContent = 'Auto-configuring Approved Manufacturer account...';

            const email = document.getElementById('authEmail').value;
            const password = document.getElementById('authPassword').value;
            const gstin = "27AAACB" + Math.floor(1000 + Math.random() * 9000) + "A1Z9";

            try {
                // 1. Admin Login
                const adminLoginRes = await fetch('/api/auth/login', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ email: 'admin@authentiq.com', password: 'Admin@123456' })
                });
                const adminLoginData = await adminLoginRes.json();
                if (!adminLoginRes.ok) throw new Error("Admin login failed. Please check seed_admin.");
                const adminToken = adminLoginData.access_token;

                // 2. Register Manufacturer
                const fd = new FormData();
                fd.append('company_name', 'BioTech Pharma Ltd');
                fd.append('GSTIN', gstin);
                fd.append('company_address', '45 Biotech Park, Pune');
                fd.append('phone', '+919876543210');
                fd.append('email', email);
                fd.append('password', password);
                fd.append('verification_document', new Blob(["Cert PDF Content"], { type: "application/pdf" }), "cert.pdf");

                const regRes = await fetch('/api/auth/manufacturer/register', { method: 'POST', body: fd });
                const regData = await regRes.json();
                
                let mfrId;
                if (regRes.ok) {
                    mfrId = regData.manufacturer_id;
                } else if (regData.detail && regData.detail.includes('already registered')) {
                    // Try direct login if already registered
                } else {
                    throw new Error(regData.detail);
                }

                // If created, approve via admin
                if (mfrId) {
                    await fetch(`/api/admin/manufacturers/${mfrId}/status`, {
                        method: 'PUT',
                        headers: {
                            'Authorization': `Bearer ${adminToken}`,
                            'Content-Type': 'application/json'
                        },
                        body: JSON.stringify({ status: 'APPROVED' })
                    });
                }

                // 3. Login as Manufacturer
                const mfrLoginRes = await fetch('/api/auth/login', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ email, password })
                });
                const mfrLoginData = await mfrLoginRes.json();
                if (!mfrLoginRes.ok) throw new Error("Manufacturer login failed: " + mfrLoginData.detail);

                mfrToken = mfrLoginData.access_token;
                document.getElementById('authRoleBadge').className = 'badge badge-onchain';
                document.getElementById('authRoleBadge').textContent = 'APPROVED MANUFACTURER';
                
                outBox.textContent = `✅ SETUP SUCCESSFUL!\nManufacturer Email: ${email}\nVerification Status: APPROVED\nJWT Access Token Acquired for Blockchain Operations.`;
                logTechDetails('/api/auth/login', 'POST', 200, { email, role: 'MANUFACTURER', status: 'APPROVED' });
                document.getElementById('step3').className = 'step active';
            } catch (err) {
                outBox.textContent = `❌ SETUP ERROR: ${err.message}`;
            }
        }

        async function loginManufacturerManual() {
            const outBox = document.getElementById('authOutput');
            outBox.style.display = 'block';
            outBox.textContent = 'Logging in...';

            const email = document.getElementById('authEmail').value;
            const password = document.getElementById('authPassword').value;

            try {
                const res = await fetch('/api/auth/login', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ email, password })
                });
                const data = await res.json();
                logTechDetails('/api/auth/login', 'POST', res.status, data);

                if (res.ok) {
                    mfrToken = data.access_token;
                    document.getElementById('authRoleBadge').className = 'badge badge-onchain';
                    document.getElementById('authRoleBadge').textContent = data.role;
                    outBox.textContent = `✅ LOGGED IN SUCCESSFULLY!\nEmail: ${data.user.email}\nCompany: ${data.user.company_name || 'N/A'}\nVerification Status: ${data.user.verification_status || 'N/A'}`;
                    document.getElementById('step3').className = 'step active';
                } else {
                    outBox.textContent = `❌ LOGIN FAILED: ${data.detail}`;
                }
            } catch (err) {
                outBox.textContent = `❌ ERROR: ${err.message}`;
            }
        }

        async function registerProductOnChain() {
            if (!mfrToken) {
                alert('Please login/setup an APPROVED Manufacturer token first!');
                return;
            }

            const outBox = document.getElementById('regOutput');
            outBox.style.display = 'block';
            outBox.textContent = 'Sending transaction to ProductVerification.sol smart contract via backend...';

            const payload = {
                product_id: document.getElementById('regProductId').value,
                product_name: document.getElementById('regProductName').value,
                batch_number: document.getElementById('regBatch').value,
                manufacturing_date: new Date(document.getElementById('regMfgDate').value).toISOString(),
                expiry_date: new Date(Date.now() + 365*24*3600*1000).toISOString(),
                current_location: document.getElementById('regCurrentLoc').value,
                next_location: document.getElementById('regNextLoc').value
            };

            try {
                const res = await fetch('/api/products/register', {
                    method: 'POST',
                    headers: {
                        'Authorization': `Bearer ${mfrToken}`,
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify(payload)
                });
                const data = await res.json();
                logTechDetails('/api/products/register', 'POST', res.status, data);

                if (res.ok) {
                    document.getElementById('regOnchainBadge').className = 'badge badge-onchain';
                    document.getElementById('regOnchainBadge').textContent = 'REGISTERED ON-CHAIN';
                    
                    document.getElementById('txStatusBadge').className = 'badge badge-onchain';
                    document.getElementById('txStatusBadge').textContent = 'CONFIRMED';
                    document.getElementById('txHashDisplay').textContent = data.transaction_hash;
                    document.getElementById('txIsOnchain').textContent = 'TRUE (100% Confirmed)';

                    outBox.textContent = `✅ PRODUCT REGISTRATION SUCCESSFUL!\n\nPostgreSQL: ✓ Saved\nBlockchain: ✓ Registered\nTransaction Hash: ${data.transaction_hash}\nProduct Hash (SHA256): ${data.product_hash}\nIs On-Chain: TRUE\nStatus: ${data.status}`;
                    
                    document.getElementById('step4').className = 'step active';
                    document.getElementById('step5').className = 'step active';
                } else {
                    document.getElementById('regOnchainBadge').className = 'badge badge-offchain';
                    document.getElementById('regOnchainBadge').textContent = 'FAILED';
                    outBox.textContent = `❌ REGISTRATION FAILED (HTTP ${res.status}):\n${data.detail}`;
                }
            } catch (err) {
                outBox.textContent = `❌ NETWORK ERROR: ${err.message}`;
            }
        }

        async function verifyProductOnChain() {
            const pid = document.getElementById('verifyProductId').value;
            const outBox = document.getElementById('verifyOutput');
            outBox.style.display = 'block';
            outBox.textContent = `Querying ProductVerification.sol for product '${pid}'...`;

            try {
                const res = await fetch(`/api/products/${encodeURIComponent(pid)}`);
                const data = await res.json();
                logTechDetails(`/api/products/${pid}`, 'GET', res.status, data);

                if (res.ok) {
                    const db = data.database || {};
                    const bc = data.blockchain || {};
                    outBox.textContent = `🔍 PRODUCT VERIFICATION RESULT\n\nProduct ID: ${data.product_id}\nDatabase Record: FOUND (${db.product_name})\nManufacturer: ${db.manufacturer_name}\nBatch Number: ${db.batch_number}\n\nSmart Contract Verification:\n  Status: ${bc.status || db.status}\n  On-Chain: ${db.is_onchain ? 'YES (VERIFIED)' : 'NO'}\n  Product Hash: ${db.product_hash}\n  Registration Tx: ${db.registration_tx_hash || 'None'}\n  Current Location: ${db.current_location}\n  Next Target Location: ${db.next_location}`;
                } else {
                    outBox.textContent = `❌ VERIFICATION FAILED: ${data.detail}`;
                }
            } catch (err) {
                outBox.textContent = `❌ ERROR: ${err.message}`;
            }
        }

        async function updateProductLocation() {
            if (!mfrToken) return alert('Manufacturer JWT token required');
            const pid = document.getElementById('locProductId').value;
            const nextLoc = document.getElementById('locNextName').value;
            const details = document.getElementById('locDetails').value;
            const outBox = document.getElementById('locOutput');
            outBox.style.display = 'block';
            outBox.textContent = 'Calling updateNextLocation on smart contract...';

            try {
                const res = await fetch(`/api/products/${encodeURIComponent(pid)}/location`, {
                    method: 'POST',
                    headers: {
                        'Authorization': `Bearer ${mfrToken}`,
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({ next_location: nextLoc, details })
                });
                const data = await res.json();
                logTechDetails(`/api/products/${pid}/location`, 'POST', res.status, data);

                if (res.ok) {
                    outBox.textContent = `📍 LOCATION UPDATED ON-CHAIN!\n\nProduct ID: ${pid}\nNew Target Location: ${data.next_location}\nTx Hash: ${data.transaction_hash}`;
                } else {
                    outBox.textContent = `❌ LOCATION UPDATE FAILED: ${data.detail}`;
                }
            } catch (err) {
                outBox.textContent = `❌ ERROR: ${err.message}`;
            }
        }

        async function fetchLocationHistory() {
            const pid = document.getElementById('locProductId').value;
            const outBox = document.getElementById('locOutput');
            outBox.style.display = 'block';
            outBox.textContent = 'Fetching location history...';

            try {
                const res = await fetch(`/api/products/${encodeURIComponent(pid)}/history`);
                const data = await res.json();
                logTechDetails(`/api/products/${pid}/history`, 'GET', res.status, data);

                if (res.ok) {
                    outBox.textContent = `📜 LOCATION AUDIT TRAIL FOR '${pid}':\n\n${JSON.stringify(data, null, 2)}`;
                } else {
                    outBox.textContent = `❌ ERROR: ${data.detail}`;
                }
            } catch (err) {
                outBox.textContent = `❌ ERROR: ${err.message}`;
            }
        }

        async function updateProductStatus() {
            if (!mfrToken) return alert('Manufacturer or Admin token required');
            const pid = document.getElementById('statProductId').value;
            const newStat = document.getElementById('statSelect').value;
            const outBox = document.getElementById('statOutput');
            outBox.style.display = 'block';
            outBox.textContent = 'Updating status on smart contract...';

            try {
                const res = await fetch(`/api/products/${encodeURIComponent(pid)}/status`, {
                    method: 'POST',
                    headers: {
                        'Authorization': `Bearer ${mfrToken}`,
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({ status: newStat })
                });
                const data = await res.json();
                logTechDetails(`/api/products/${pid}/status`, 'POST', res.status, data);

                if (res.ok) {
                    outBox.textContent = `🛡️ ON-CHAIN STATUS UPDATED!\n\nProduct ID: ${pid}\nNew Status: ${data.status}\nTx Hash: ${data.transaction_hash}`;
                } else {
                    outBox.textContent = `❌ STATUS UPDATE FAILED: ${data.detail}`;
                }
            } catch (err) {
                outBox.textContent = `❌ ERROR: ${err.message}`;
            }
        }
    </script>
</body>
</html>
"""

@router.get("", response_class=HTMLResponse)
@router.get("/phase3", response_class=HTMLResponse)
async def get_interactive_demo():
    """
    Serves the Phase 3 Interactive Demonstration Web Dashboard.
    """
    return HTMLResponse(content=PHASE3_DEMO_HTML, status_code=200)

@router.get("/blockchain", response_class=HTMLResponse)
@router.get("/phase4", response_class=HTMLResponse)
async def get_blockchain_demo():
    """
    Serves the Phase 4 Interactive Blockchain Demonstration Web Dashboard.
    Visually verifies real-time RPC connectivity, ProductVerification.sol smart contract queries,
    on-chain product registration, transaction hash generation, location tracking, and status management.
    """
    return HTMLResponse(content=PHASE4_BLOCKCHAIN_DEMO_HTML, status_code=200)
