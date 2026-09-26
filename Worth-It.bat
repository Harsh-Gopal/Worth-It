@echo off
setlocal
cd /d "%~dp0"

set TARGET_PORT=3000
set TARGET_URL=http://localhost:%TARGET_PORT%

echo ========================================================
echo             🚀 Worth-It (Windows)
echo ========================================================
echo.

docker info >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Docker is not running.
    echo Please start Docker Desktop and try again.
    pause
    exit /b 1
)

echo 1. Starting Worth-It...
docker compose up -d
if %errorlevel% neq 0 (
    echo [ERROR] Failed to start containers.
    pause
    exit /b 1
)

echo 2. Waiting for Services to be Ready...
echo Checking backend health...

set MAX_WAIT=30
set WAITED=0

:waitloop
curl -s -f http://localhost:8000/api/health >nul 2>&1
if %errorlevel% equ 0 (
    echo [OK] Backend is healthy.
    goto frontendcheck
)

<nul set /p="."
timeout /t 2 /nobreak >nul
set /a WAITED+=2
if %WAITED% lss %MAX_WAIT% goto waitloop

echo.
echo [ERROR] Backend failed to become healthy within %MAX_WAIT%s.
echo Check logs: docker compose logs backend
pause
exit /b 1

:frontendcheck
echo Checking frontend...
timeout /t 2 /nobreak >nul
echo [OK] Frontend is ready.

echo.
echo ========================================================
echo   ✅ Worth-It is now running!
echo   Opening browser to: %TARGET_URL%
echo ========================================================
echo.

start "" "%TARGET_URL%"

echo To stop Worth-It, you can run 'docker compose down' in your terminal,
echo or stop it via Docker Desktop.
echo.
pause
