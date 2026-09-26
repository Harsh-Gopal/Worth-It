#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

COMPOSE_FILE="$SCRIPT_DIR/docker-compose.yml"
TARGET_PORT="3000"
TARGET_URL="http://localhost:$TARGET_PORT"

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'
CYAN='\033[0;36m'; BOLD='\033[1m'; RESET='\033[0m'

banner() { echo -e "\n${CYAN}${BOLD}$1${RESET}"; }
ok()     { echo -e "  ${GREEN}✓${RESET} $1"; }
warn()   { echo -e "  ${YELLOW}⚠${RESET}  $1"; }
fail()   { echo -e "\n${RED}✗ ERROR:${RESET} $1\n"; }

clear
echo -e "${BOLD}"
echo "  ╔══════════════════════════════════════╗"
echo "  ║            🚀 Worth-It               ║"
echo "  ╚══════════════════════════════════════╝"
echo -e "${RESET}"

if ! docker info &>/dev/null; then
    fail "Docker is not running or you lack permissions."
    exit 1
fi

banner "1. Starting Worth-It..."
echo "  Starting containers in the background..."
docker compose -f "$COMPOSE_FILE" up -d

banner "2. Waiting for Services to be Ready..."
echo "  Checking backend health endpoint..."

MAX_WAIT=60
waited=0
backend_ready=false

while [ $waited -lt $MAX_WAIT ]; do
    if curl -s -f http://localhost:8000/api/health >/dev/null 2>&1; then
        backend_ready=true
        break
    fi
    printf "."
    sleep 2
    waited=$((waited + 2))
done
echo ""

if [ "$backend_ready" = true ]; then
    ok "Backend is healthy."
else
    fail "Backend failed to become healthy within ${MAX_WAIT}s."
    echo "  Check logs: docker compose logs backend"
    exit 1
fi

echo "  Checking frontend readiness..."
if ! curl -s -I "$TARGET_URL" >/dev/null 2>&1; then
    sleep 2
fi
ok "Frontend is ready."

echo ""
echo -e "${BOLD}${GREEN}  ✅ Worth-It is now running!${RESET}"
echo "  Application is available at: $TARGET_URL"
echo ""

if command -v xdg-open >/dev/null; then
    xdg-open "$TARGET_URL" 2>/dev/null &
fi

echo "  To stop Worth-It, run: docker compose down"
echo ""
