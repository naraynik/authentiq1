@echo off
rem Stops AuthentiQ. Database, blockchain and uploads are kept.
cd /d "%~dp0"
docker compose --profile tools down
echo AuthentiQ stopped. Your data is kept.
pause
