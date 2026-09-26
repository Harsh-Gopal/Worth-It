#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

COMPOSE_FILE="$SCRIPT_DIR/docker-compose.yml"

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'
CYAN='\033[0;36m'; BOLD='\033[1m'; RESET='\033[0m'

banner() { echo -e "\n${CYAN}${BOLD}$1${RESET}"; }
ok()     { echo -e "  ${GREEN}✓${RESET} $1"; }
warn()   { echo -e "  ${YELLOW}⚠${RESET}  $1"; }
fail()   { echo -e "\n${RED}✗ ERROR:${RESET} $1\n"; }

clear
echo -e "${BOLD}"
echo "  ╔══════════════════════════════════════╗"
echo "  ║        🎯 Worth-It Installer         ║"
echo "  ╚══════════════════════════════════════╝"
echo -e "${RESET}"

banner "1. Checking for Docker Engine..."
if ! command -v docker &>/dev/null; then
    fail "Docker is not installed."
    echo "  Docker is required to run Worth-It."
    echo ""
    echo "  ➡ Please install Docker engine for your distribution:"
    echo "     https://docs.docker.com/engine/install/"
    exit 1
fi

banner "2. Checking if Docker is running..."
if ! sudo -n docker info &>/dev/null && ! docker info &>/dev/null 2>&1; then
    fail "Docker is installed but not running, or you lack permissions."
    echo "  Ensure the docker daemon is running and you are in the 'docker' group."
    exit 1
else
    ok "Docker is running and accessible."
fi

banner "3. Verifying Docker Compose..."
if ! docker compose version &>/dev/null && ! docker-compose version &>/dev/null; then
    fail "Docker Compose is not available. Please install it."
    exit 1
fi
ok "Docker Compose is ready."

banner "4. Building Worth-It..."
echo "  Building local images for backend and frontend."
echo "  This might take a few minutes the first time."
echo ""

if ! docker compose -f "$COMPOSE_FILE" build; then
    fail "Failed to build Worth-It images."
    exit 1
fi
ok "Successfully built Worth-It."

banner "5. Preparing data directories..."
mkdir -p "$SCRIPT_DIR/backend/data"
chmod 777 "$SCRIPT_DIR/backend/data" 2>/dev/null || true
ok "Data directories ready."

echo ""
echo -e "${BOLD}${GREEN}  ✅ Installation Complete!${RESET}"
echo "  You can now start the application by running:"
echo "  👉 ./Worth-It.sh"
echo ""
