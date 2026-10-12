@echo off
REM AuthentiQ Quick Start Script (Windows)
REM This script sets up the entire development environment

setlocal enabledelayedexpansion
cd /d "%~dp0"

echo.
echo 🚀 AuthentiQ Quick Start Setup (Windows)
echo ========================================
echo.

REM Check prerequisites
echo [1/6] Checking prerequisites...
where git >nul 2>nul
if errorlevel 1 (
    echo ❌ Git not found. Please install Git.
    exit /b 1
)

where docker >nul 2>nul
if errorlevel 1 (
    echo ❌ Docker not found. Please install Docker Desktop.
    exit /b 1
)

where npm >nul 2>nul
if errorlevel 1 (
    echo ❌ Node.js/npm not found. Please install Node.js.
    exit /b 1
)

where python >nul 2>nul
if errorlevel 1 (
    echo ❌ Python not found. Please install Python 3.10+.
    exit /b 1
)

echo ✓ All prerequisites found
echo.

REM Install Python Dependencies
echo [2/6] Installing Python dependencies...
cd ai-engine
python -m venv venv
call venv\Scripts\activate.bat
pip install -q -r requirements.txt
cd ..
echo ✓ AI engine dependencies installed

cd backend
pip install -q -r requirements.txt
cd ..
echo ✓ Backend dependencies installed
echo.

REM Install Node Dependencies  
echo [3/6] Installing Node.js dependencies...
if exist "..\AuthentiQ-Blockchain-main" (
    cd ..\AuthentiQ-Blockchain-main
    call npm install -q
    cd ..\AUTHENIQ-AI-main
    echo ✓ Blockchain dependencies installed
) else (
    echo ⚠️ Canonical blockchain folder AuthentiQ-Blockchain-main not found.
)

cd frontend
call npm install -q
cd ..
echo ✓ Frontend dependencies installed
echo.

REM Start PostgreSQL
echo [4/6] Starting PostgreSQL database...
docker ps -a --format "{{.Names}}" | findstr "authentiq-postgres-dev" >nul
if not errorlevel 1 (
    docker rm -f authentiq-postgres-dev >nul 2>&1
)
docker-compose -f docker-compose.dev.yml up -d
echo ✓ PostgreSQL started
echo.

REM Train AI Models
echo [5/6] Training AI models...
cd ai-engine
call venv\Scripts\activate.bat
python train.py
cd ..
echo ✓ Models trained and saved
echo.

REM Summary
echo ========================================
echo ✓ Setup complete!
echo ========================================
echo.
echo 📋 Next Steps (in separate Command Prompts):
echo ========================================
echo.
echo 1. Start Blockchain (Console 1):
echo    cd ..\AuthentiQ-Blockchain-main ^& npm run node
echo.
echo 2. Deploy Contracts (Console 2):
echo    cd ..\AuthentiQ-Blockchain-main ^& npm run deploy:local
echo.
echo 3. Start Backend (Console 3):
echo    cd backend ^& uvicorn app.main:app --reload
echo.
echo 4. Start Frontend (Console 4):
echo    cd frontend ^& npm run dev
echo.
echo ========================================
echo 🌐 Access:
echo ========================================
echo Frontend:  http://localhost:3000
echo API Docs:  http://localhost:8000/docs
echo Database:  localhost:5432
echo.
pause
