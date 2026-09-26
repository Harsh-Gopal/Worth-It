@echo off
setlocal
cd /d "%~dp0"

echo ========================================================
echo         🎯 Worth-It Installer (Windows)
echo ========================================================
echo.

echo 1. Checking for Docker...
docker --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Docker is not installed or not in PATH.
    echo Please install Docker Desktop from:
    echo https://www.docker.com/products/docker-desktop/
    pause
    exit /b 1
)

echo 2. Checking if Docker is running...
docker info >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Docker is installed but not running.
    echo Please start Docker Desktop and try again.
    pause
    exit /b 1
)
echo [OK] Docker is running.

echo 3. Building Worth-It...
echo This might take a few minutes the first time.
docker compose build
if %errorlevel% neq 0 (
    echo [ERROR] Failed to build Worth-It images.
    pause
    exit /b 1
)
echo [OK] Successfully built Worth-It.

echo 4. Preparing data directories...
if not exist "backend\data" mkdir "backend\data"
echo [OK] Data directories ready.

echo.
echo ========================================================
echo   ✅ Installation Complete!
echo   You can now start the application by double-clicking:
echo   👉 Worth-It.bat
echo ========================================================
echo.
pause
