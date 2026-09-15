#!/usr/bin/env bash

# ==============================================================================
# Worth-It — Development Environment Launcher
# ==============================================================================

# Fail on error for setup steps
set -e

# Configuration
BACKEND_DIR="backend"
FRONTEND_DIR="frontend"
BACKEND_PORT=8000
FRONTEND_PORT=5173

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Print banner
echo -e "${BLUE}================================================${NC}"
echo -e "${BLUE} Worth-It — Development Environment ${NC}"
echo -e "${BLUE}================================================${NC}"
echo ""

# Dependency Checks
if ! command -v uv &> /dev/null; then
    echo -e "${RED}[ERROR] uv is required to run the backend. Please install uv first.${NC}"
    exit 1
fi

if ! command -v npm &> /dev/null; then
    echo -e "${RED}[ERROR] npm is required to run the frontend. Please install npm first.${NC}"
    exit 1
fi

# Frontend dependencies check
if [ ! -d "$FRONTEND_DIR/node_modules" ]; then
    echo -e "${YELLOW}[FRONTEND] node_modules not found. Installing dependencies...${NC}"
    (cd "$FRONTEND_DIR" && npm install)
fi

# Port checking
check_port() {
    local port=$1
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null; then
        return 0 # Port in use
    else
        return 1 # Port free
    fi
}

if check_port $BACKEND_PORT; then
    echo -e "${YELLOW}Port $BACKEND_PORT is already in use.${NC}"
    echo -e "Worth-It backend appears to already be running."
    echo -e "Backend: http://127.0.0.1:$BACKEND_PORT"
    echo -e "Please stop the existing process or use it directly."
    exit 1
fi

if check_port $FRONTEND_PORT; then
    echo -e "${YELLOW}Port $FRONTEND_PORT is already in use.${NC}"
    echo -e "Worth-It frontend appears to already be running."
    echo -e "Frontend: http://localhost:$FRONTEND_PORT"
    echo -e "Please stop the existing process or use it directly."
    exit 1
fi

# We will handle errors manually from here on
set +e

# Process IDs
BACKEND_PID=""
FRONTEND_PID=""

# Cleanup function
cleanup() {
    echo ""
    echo -e "${YELLOW}Stopping services...${NC}"
    if [ -n "$FRONTEND_PID" ]; then
        kill $FRONTEND_PID 2>/dev/null || true
    fi
    if [ -n "$BACKEND_PID" ]; then
        kill $BACKEND_PID 2>/dev/null || true
    fi
    wait
    echo -e "${GREEN}All services stopped cleanly.${NC}"
    exit 0
}

# Register cleanup on Ctrl+C and exit
trap cleanup INT TERM EXIT

# Start Backend
echo -e "${GREEN}[BACKEND]${NC} Starting FastAPI..."
cd "$BACKEND_DIR"
uv run uvicorn main:app --host 127.0.0.1 --port $BACKEND_PORT --reload 2>&1 | awk '{print "\033[0;32m[BACKEND]\033[0m " $0}' &
BACKEND_PID=$!
cd ..

# Wait for backend health check
echo -e "${GREEN}[BACKEND]${NC} Waiting for API to be ready..."
MAX_RETRIES=30
RETRY_COUNT=0
while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
    if curl -s -f http://127.0.0.1:$BACKEND_PORT/api/health >/dev/null 2>&1; then
        echo -e "${GREEN}[BACKEND] ✓ API ready${NC}"
        break
    fi
    sleep 1
    RETRY_COUNT=$((RETRY_COUNT+1))
done

if [ $RETRY_COUNT -eq $MAX_RETRIES ]; then
    echo -e "${RED}[BACKEND] ✕ Failed to start or health check timeout.${NC}"
    echo "Check backend logs above."
    cleanup
fi

# Start Frontend
echo -e "${BLUE}[FRONTEND]${NC} Starting Vite..."
cd "$FRONTEND_DIR"
npm run dev -- --port $FRONTEND_PORT 2>&1 | awk '{print "\033[0;34m[FRONTEND]\033[0m " $0}' &
FRONTEND_PID=$!
cd ..

# Wait for frontend readiness
echo -e "${BLUE}[FRONTEND]${NC} Waiting for Vite to be ready..."
RETRY_COUNT=0
while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
    if curl -s -I http://localhost:$FRONTEND_PORT >/dev/null 2>&1; then
        echo -e "${BLUE}[FRONTEND] ✓ Vite ready${NC}"
        break
    fi
    sleep 1
    RETRY_COUNT=$((RETRY_COUNT+1))
done

if [ $RETRY_COUNT -eq $MAX_RETRIES ]; then
    echo -e "${RED}[FRONTEND] ✕ Failed to start Vite.${NC}"
    cleanup
fi

echo ""
echo -e "${GREEN}================================================${NC}"
echo -e "${GREEN} Worth-It is running${NC}"
echo -e "${GREEN}================================================${NC}"
echo ""
echo -e "Frontend:"
echo -e "  ${BLUE}http://localhost:$FRONTEND_PORT${NC}"
echo ""
echo -e "Backend:"
echo -e "  ${GREEN}http://127.0.0.1:$BACKEND_PORT${NC}"
echo ""
echo -e "API:"
echo -e "  ${GREEN}http://127.0.0.1:$BACKEND_PORT/api${NC}"
echo ""
echo "Press Ctrl+C to stop."

# Wait indefinitely until interrupted
wait
