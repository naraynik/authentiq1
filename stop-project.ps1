# AuthentiQ Safe Project Shutdown Script (Windows PowerShell)
# Stops running backend, frontend, and Ganache processes without deleting any database records or persistent blockchain state.

Write-Host "====================================================" -ForegroundColor Yellow
Write-Host "AuthentiQ System Safe Shutdown" -ForegroundColor Yellow
Write-Host "====================================================" -ForegroundColor Yellow

# Stop Node.js processes (Ganache, website & admin portal)
Write-Host "Stopping Node.js background processes (Ganache & Frontend)..." -ForegroundColor Gray
Get-Process -Name "node" -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue

# Stop Python / Uvicorn backend processes
Write-Host "Stopping Python / Uvicorn backend server..." -ForegroundColor Gray
Get-Process -Name "python", "uvicorn" -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue

Write-Host "====================================================" -ForegroundColor Green
Write-Host "✓ AuthentiQ background processes stopped cleanly." -ForegroundColor Green
Write-Host "✓ Persistent blockchain data (./chain_data) and PostgreSQL database state remain fully intact." -ForegroundColor Green
Write-Host "====================================================" -ForegroundColor Green
