#!/bin/bash

# WebSearch API Run Script
# Convenient commands for managing the WebSearch API

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

ADMIN_API_KEY="GA_Incg4zEhpK-65G6PwL499t2kXvH2Cs-hWf6udtZU"

show_help() {
    cat << EOF
${BLUE}═══════════════════════════════════════════════════════════${NC}
${GREEN}WebSearch API Management Script${NC}
${BLUE}═══════════════════════════════════════════════════════════${NC}

Usage: ./run.sh [command]

${YELLOW}Commands:${NC}
  start         Start MongoDB, Redis, and API server
  stop          Stop all services
  restart       Restart all services
  api           Start only the API server (services must be running)
  services      Start only MongoDB and Redis
  status        Show service status
  logs          Show API logs
  test          Run a test search
  health        Check API health
  admin         Create a new admin user
  shell         Open API shell (poetry shell)
  install       Install dependencies
  clean         Stop and remove all data
  help          Show this help message

${YELLOW}Examples:${NC}
  ./run.sh start              # Start everything
  ./run.sh api                # Start just the API
  ./run.sh test               # Test search endpoint
  ./run.sh logs               # Follow API logs

${YELLOW}Access URLs:${NC}
  API:           http://localhost:8000
  API Docs:      http://localhost:8000/docs
  Health:        http://localhost:8000/health

${YELLOW}Admin API Key:${NC}
  ${ADMIN_API_KEY}

${BLUE}═══════════════════════════════════════════════════════════${NC}
EOF
}

check_poetry() {
    if ! command -v poetry &> /dev/null; then
        echo -e "${RED}✗ Poetry is not installed${NC}"
        echo "Install: curl -sSL https://install.python-poetry.org | python3 -"
        exit 1
    fi
}

check_docker() {
    if ! command -v docker &> /dev/null; then
        echo -e "${RED}✗ Docker is not installed${NC}"
        exit 1
    fi
    
    if ! docker info &> /dev/null; then
        echo -e "${RED}✗ Docker daemon is not running${NC}"
        exit 1
    fi
}

cmd_install() {
    echo -e "${BLUE}Installing dependencies...${NC}"
    check_poetry
    poetry install --no-interaction
    echo -e "${GREEN}✓ Dependencies installed${NC}"
}

cmd_services() {
    echo -e "${BLUE}Starting MongoDB and Redis...${NC}"
    check_docker
    
    docker-compose up -d mongodb redis
    
    echo ""
    echo -e "${GREEN}✓ Services started${NC}"
    sleep 3
    cmd_status
}

cmd_api() {
    echo -e "${BLUE}Starting API server...${NC}"
    check_poetry
    
    # Check if services are running
    if ! docker ps | grep -q "mongo\|redis"; then
        echo -e "${YELLOW}MongoDB/Redis not running. Starting services first...${NC}"
        cmd_services
        echo ""
    fi
    
    echo -e "${GREEN}Starting WebSearch API...${NC}"
    echo -e "${YELLOW}Access at: ${BLUE}http://localhost:8000${NC}"
    echo -e "${YELLOW}API Docs:  ${BLUE}http://localhost:8000/docs${NC}"
    echo ""
    
    poetry run uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload
}

cmd_start() {
    echo -e "${BLUE}Starting WebSearch API stack...${NC}"
    
    # Start services
    cmd_services
    echo ""
    
    # Start API in foreground
    echo -e "${BLUE}Starting API server...${NC}"
    sleep 2
    cmd_api
}

cmd_stop() {
    echo -e "${BLUE}Stopping WebSearch API...${NC}"
    
    # Find and stop API process
    API_PID=$(pgrep -f "uvicorn src.main:app" 2>/dev/null || echo "")
    if [ -n "$API_PID" ]; then
        echo "Stopping API (PID: $API_PID)..."
        kill "$API_PID" 2>/dev/null || true
        echo -e "${GREEN}✓ API stopped${NC}"
    fi
    
    # Stop Docker services
    docker-compose down
    echo -e "${GREEN}✓ Services stopped${NC}"
}

cmd_restart() {
    echo -e "${BLUE}Restarting WebSearch API...${NC}"
    cmd_stop
    sleep 2
    cmd_start
}

cmd_status() {
    echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
    echo -e "${GREEN}Service Status:${NC}"
    echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
    
    # Check Docker services
    docker-compose ps 2>/dev/null || echo "No Docker services running"
    
    echo ""
    
    # Check API
    if pgrep -f "uvicorn src.main:app" > /dev/null; then
        echo -e "${GREEN}✓ API Server: Running${NC}"
    else
        echo -e "${YELLOW}○ API Server: Stopped${NC}"
    fi
    
    echo ""
}

cmd_logs() {
    echo -e "${BLUE}Following API logs (Ctrl+C to stop)...${NC}"
    
    if [ -d "logs" ]; then
        tail -f logs/*.log
    else
        echo -e "${YELLOW}No logs directory found. Run the API first.${NC}"
    fi
}

cmd_test() {
    echo -e "${BLUE}Running test search...${NC}"
    
    curl -X POST http://localhost:8000/api/v1/search \
        -H "X-API-Key: ${ADMIN_API_KEY}" \
        -H "Content-Type: application/json" \
        -d '{"query": "OpenTelemetry", "max_results": 5}' \
        -s | python3 -m json.tool
    
    echo ""
    echo -e "${GREEN}✓ Test complete${NC}"
}

cmd_health() {
    echo -e "${BLUE}Checking API health...${NC}"
    
    response=$(curl -s http://localhost:8000/health)
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓ API is healthy${NC}"
        echo "$response" | python3 -m json.tool 2>/dev/null || echo "$response"
    else
        echo -e "${RED}✗ API is not responding${NC}"
        echo "Make sure the API is running: ./run.sh start"
        exit 1
    fi
}

cmd_admin() {
    echo -e "${BLUE}Creating admin user...${NC}"
    check_poetry
    
    poetry run python scripts/create_admin.py
    
    echo -e "${GREEN}✓ Admin user created${NC}"
}

cmd_shell() {
    echo -e "${BLUE}Opening Poetry shell...${NC}"
    check_poetry
    poetry shell
}

cmd_clean() {
    echo -e "${RED}WARNING: This will delete all data (MongoDB, Redis)!${NC}"
    read -p "Are you sure? (yes/no): " confirm
    
    if [ "$confirm" = "yes" ]; then
        echo -e "${BLUE}Stopping and cleaning...${NC}"
        cmd_stop
        docker-compose down -v
        rm -rf logs/*
        echo -e "${GREEN}✓ All data cleaned${NC}"
    else
        echo "Cancelled"
    fi
}

# Main script
case "${1:-help}" in
    start)
        cmd_start
        ;;
    stop)
        cmd_stop
        ;;
    restart)
        cmd_restart
        ;;
    api)
        cmd_api
        ;;
    services)
        cmd_services
        ;;
    status)
        cmd_status
        ;;
    logs)
        cmd_logs
        ;;
    test)
        cmd_test
        ;;
    health)
        cmd_health
        ;;
    admin)
        cmd_admin
        ;;
    shell)
        cmd_shell
        ;;
    install)
        cmd_install
        ;;
    clean)
        cmd_clean
        ;;
    help|--help|-h)
        show_help
        ;;
    *)
        echo -e "${RED}Unknown command: $1${NC}"
        echo "Run './run.sh help' for usage"
        exit 1
        ;;
esac
