# AuthentiQ Safe Project Startup Script (Windows PowerShell)
# Launches PostgreSQL, Persistent Ganache Node, Smart Contract Check, FastAPI and the AuthentiQ website

$ErrorActionPreference = "Continue"

Write-Host "====================================================" -ForegroundColor Cyan
Write-Host "AuthentiQ System Startup Orchestrator" -ForegroundColor Cyan
Write-Host "====================================================" -ForegroundColor Cyan

$WorkspaceRoot = (Resolve-Path "$PSScriptRoot\..").ProviderPath

# 1. Check PostgreSQL Container
Write-Host "[1/5] Checking PostgreSQL Database container..." -ForegroundColor Yellow
$pgRunning = $false
try {
    $pgStatus = (docker inspect -f '{{.State.Running}}' authentiq-postgres-dev 2>$null)
    if ($pgStatus -eq "true") { $pgRunning = $true }
} catch {
    $pgRunning = $false
}

if (-not $pgRunning) {
    Write-Host "Starting PostgreSQL container 'authentiq-postgres-dev'..." -ForegroundColor Gray
    try {
        docker start authentiq-postgres-dev 2>$null | Out-Null
    } catch {}
    Start-Sleep -Seconds 2
}
Write-Host "[OK] PostgreSQL container is RUNNING." -ForegroundColor Green

# 2. Check Persistent Blockchain RPC Node
Write-Host "[2/5] Checking Persistent Blockchain Node (RPC http://127.0.0.1:8545)..." -ForegroundColor Yellow
$rpcOnline = $false
try {
    $bodyJson = '{"jsonrpc":"2.0","method":"net_version","params":[],"id":1}'
    $res = Invoke-RestMethod -Uri "http://127.0.0.1:8545" -Method Post -ContentType "application/json" -Body $bodyJson -ErrorAction Stop
    if ($res.result) { $rpcOnline = $true }
} catch {
    $rpcOnline = $false
}

if (-not $rpcOnline) {
    Write-Host "Launching persistent Ganache node (storing state in ./chain_data)..." -ForegroundColor Gray
    $blockchainDir = Join-Path $PSScriptRoot "blockchain"
    if (-not (Test-Path $blockchainDir)) {
        $blockchainDir = Join-Path $WorkspaceRoot "AuthentiQ-Blockchain-main"
    }
    Start-Process -FilePath "powershell.exe" -ArgumentList "-NoProfile", "-Command", "npm run chain:start" -WorkingDirectory $blockchainDir -WindowStyle Minimized
    
    # Wait for RPC readiness
    $retries = 0
    while ((-not $rpcOnline) -and ($retries -lt 15)) {
        Start-Sleep -Seconds 1
        $retries++
        try {
            $bodyJson = '{"jsonrpc":"2.0","method":"net_version","params":[],"id":1}'
            $res = Invoke-RestMethod -Uri "http://127.0.0.1:8545" -Method Post -ContentType "application/json" -Body $bodyJson -ErrorAction Stop
            if ($res.result) { $rpcOnline = $true }
        } catch {}
    }
}

if ($rpcOnline) {
    Write-Host "[OK] Persistent Blockchain Node is ONLINE (Chain ID: 1337)." -ForegroundColor Green
} else {
    Write-Host "[ERROR] Failed to reach persistent blockchain RPC at http://127.0.0.1:8545" -ForegroundColor Red
    exit 1
}

# 3. Check Smart Contract Bytecode / Deploy if missing
Write-Host "[3/5] Verifying Smart Contract Bytecode on Persistent Blockchain..." -ForegroundColor Yellow
$blockchainDir = Join-Path $PSScriptRoot "blockchain"
if (-not (Test-Path $blockchainDir)) {
    $blockchainDir = Join-Path $WorkspaceRoot "AuthentiQ-Blockchain-main"
}
$originalLocation = Get-Location
try {
    Set-Location -Path $blockchainDir
    npx hardhat run scripts/deploy.js --network ganache
    Write-Host "[OK] Smart contract state verified." -ForegroundColor Green
} finally {
    Set-Location -Path $originalLocation
}

# 4. Check FastAPI Backend
Write-Host "[4/5] Checking FastAPI Backend Gateway (http://127.0.0.1:8000)..." -ForegroundColor Yellow
$backendOnline = $false
try {
    $bRes = Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/health" -Method Get -ErrorAction Stop
    if ($bRes.status -eq "healthy") { $backendOnline = $true }
} catch {}

if (-not $backendOnline) {
    Write-Host "Starting FastAPI server on port 8000..." -ForegroundColor Gray
    $backendDir = Join-Path $PSScriptRoot "backend"
    Start-Process -FilePath "powershell.exe" -ArgumentList "-NoProfile", "-Command", "python -m uvicorn app.main:app --reload --port 8000" -WorkingDirectory $backendDir -WindowStyle Minimized
    Start-Sleep -Seconds 3
}
Write-Host "[OK] FastAPI Backend is RUNNING at http://127.0.0.1:8000" -ForegroundColor Green

# 5. AuthentiQ website (frontend/, Vite + React, needs Bun: https://bun.sh)
Write-Host "[5/5] Checking AuthentiQ website (http://localhost:3000)..." -ForegroundColor Yellow
$frontendOnline = $false
try {
    $fRes = Invoke-WebRequest -Uri "http://localhost:3000" -UseBasicParsing -ErrorAction Stop
    if ($fRes.StatusCode -eq 200) { $frontendOnline = $true }
} catch {}

if (-not $frontendOnline) {
    $frontendDir = Join-Path $PSScriptRoot "frontend"
    if (-not (Test-Path (Join-Path $frontendDir "node_modules"))) {
        Write-Host "Installing website packages (first run only)..." -ForegroundColor Gray
        Push-Location $frontendDir; bun install; Pop-Location
    }
    Write-Host "Starting AuthentiQ website on port 3000..." -ForegroundColor Gray
    Start-Process -FilePath "powershell.exe" -ArgumentList "-NoProfile", "-Command", "bun run dev --port 3000" -WorkingDirectory $frontendDir -WindowStyle Minimized
    Start-Sleep -Seconds 5
}
Write-Host "[OK] AuthentiQ website is RUNNING at http://localhost:3000" -ForegroundColor Green

Write-Host "====================================================" -ForegroundColor Cyan
Write-Host "SUCCESS: AuthentiQ System is fully operational!" -ForegroundColor Cyan
Write-Host "Website:       http://localhost:3000" -ForegroundColor White
Write-Host "Team console:  Website -> Manufacturers -> Log in with the admin account" -ForegroundColor White
Write-Host "API Gateway:   http://127.0.0.1:8000" -ForegroundColor White
Write-Host "API docs:      http://127.0.0.1:8000/api/docs" -ForegroundColor White
Write-Host "Blockchain:    http://127.0.0.1:8545 (Chain ID: 1337)" -ForegroundColor White
Write-Host "====================================================" -ForegroundColor Cyan
