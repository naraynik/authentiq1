# AuthentiQ one-click start for Windows (Docker Desktop).
# Creates .env with fresh passwords the first time, builds and starts everything,
# waits until it is ready, then opens the website and the admin portal.
# Continue: Windows PowerShell 5.1 turns harmless docker messages on stderr into errors under "Stop"
$ErrorActionPreference = "Continue"
Set-Location (Split-Path -Parent $PSScriptRoot)

function Say($text, $color = "White") { Write-Host $text -ForegroundColor $color }
function RandomHex($bytes) {
    $b = New-Object byte[] $bytes
    [System.Security.Cryptography.RandomNumberGenerator]::Create().GetBytes($b)
    -join ($b | ForEach-Object { $_.ToString("x2") })
}

Say "==============================================" Cyan
Say " AuthentiQ: starting the whole system" Cyan
Say "==============================================" Cyan

# 1. Docker Desktop installed and running?
if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
    Say "Docker Desktop is not installed." Red
    Say "Install it from https://www.docker.com/products/docker-desktop/ , open it once, then run this again." Yellow
    Start-Process "https://www.docker.com/products/docker-desktop/"
    Read-Host "Press Enter to close"; exit 1
}
docker info *> $null
if ($LASTEXITCODE -ne 0) {
    Say "Docker Desktop is installed but not running. Starting it..." Yellow
    $dd = Join-Path $env:ProgramFiles "Docker\Docker\Docker Desktop.exe"
    if (Test-Path $dd) { Start-Process $dd }
    for ($i = 0; $i -lt 60; $i++) {
        Start-Sleep -Seconds 3
        docker info *> $null
        if ($LASTEXITCODE -eq 0) { break }
    }
    docker info *> $null
    if ($LASTEXITCODE -ne 0) {
        Say "Docker did not start. Open Docker Desktop, wait until it says 'Engine running', then run this again." Red
        Read-Host "Press Enter to close"; exit 1
    }
}
Say "[OK] Docker is running" Green

# 2. First run: create .env with fresh secrets
$port = 8080
if (-not (Test-Path ".env")) {
    $adminPassword = "AdminPassword123!"   # the team's chosen login; change it in .env any time
    $lines = @(
        "# Created by scripts/start-docker.ps1 on $(Get-Date -Format 'yyyy-MM-dd HH:mm'). Keep this file private.",
        "POSTGRES_PASSWORD=$(RandomHex 16)",
        "SECRET_KEY=$(RandomHex 32)",
        "ADMIN_EMAIL=admin@authentiq.com",
        "ADMIN_PASSWORD=$adminPassword",
        "BLOCKCHAIN_PRIVATE_KEY=0x$(RandomHex 32)",
        "WEB_PORT=$port",
        "ADMINER_PORT=8081"
    )
    # UTF-8 without BOM, which Docker Compose reads correctly
    [System.IO.File]::WriteAllText((Join-Path (Get-Location) ".env"), ($lines -join "`n") + "`n", (New-Object System.Text.UTF8Encoding $false))
    $login = "AuthentiQ team console`r`n  Open http://localhost:$port/#/manufacturer -> Log in`r`n  Email:    admin@authentiq.com`r`n  Password: $adminPassword`r`n"
    [System.IO.File]::WriteAllText((Join-Path (Get-Location) "ADMIN-LOGIN.txt"), $login)
    Say "[OK] Created .env with new passwords (admin login saved in ADMIN-LOGIN.txt)" Green
} else {
    $m = Select-String -Path ".env" -Pattern '^WEB_PORT=(\d+)' | Select-Object -First 1
    if ($m) { $port = [int]$m.Matches[0].Groups[1].Value } else { $port = 80 }
    Say "[OK] Using the existing .env" Green
}

# 3. Build and start (first time: 5-15 minutes, it downloads the AI libraries)
Say "Building and starting... the first time takes 5-15 minutes." Yellow
docker compose --profile tools up -d --build
if ($LASTEXITCODE -ne 0) {
    Say "Something failed while building or starting. The messages above say what." Red
    Read-Host "Press Enter to close"; exit 1
}

# 4. Wait for the backend
$base = if ($port -eq 80) { "http://localhost" } else { "http://localhost:$port" }
Say "Waiting for AuthentiQ to be ready at $base ..." Yellow
$ready = $false
for ($i = 0; $i -lt 90; $i++) {
    try {
        $r = Invoke-WebRequest -Uri "$base/api/health" -UseBasicParsing -TimeoutSec 5
        if ($r.StatusCode -eq 200) { $ready = $true; break }
    } catch {}
    Start-Sleep -Seconds 4
}
if (-not $ready) {
    Say "Not ready after 6 minutes. See what the backend says with:  docker compose logs backend" Red
    Read-Host "Press Enter to close"; exit 1
}

Say "==============================================" Green
Say " AuthentiQ is running" Green
Say "   Website:       $base/" White
Say "   Team console:  $base/#/manufacturer -> Log in (login in ADMIN-LOGIN.txt)" White
Say "   API docs:      $base/api/docs" White
Say "   Database:      http://localhost:8081  (System PostgreSQL, Server db, User authentiq," White
Say "                  Password = POSTGRES_PASSWORD in .env, Database authentiq)" White
Say " Stop it with STOP-AUTHENTIQ.bat (your data is kept)." White
Say "==============================================" Green
Start-Process "$base/"
Start-Process "$base/#/manufacturer"
if (Test-Path "ADMIN-LOGIN.txt") { Start-Process notepad.exe "ADMIN-LOGIN.txt" }
Read-Host "Press Enter to close this window (AuthentiQ keeps running)"
