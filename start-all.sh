#!/bin/bash

# Start All - Master script to start both projects
# Starts OTEL Receiver and WebSearch API together

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

OTEL_DIR="/Users/mikek/repos/otel/otel-receiver"
API_DIR="/Users/mikek/repos/websearch-api"

echo -e "${BLUE}════════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}Starting Complete Enterprise Observability Stack${NC}"
echo -e "${BLUE}════════════════════════════════════════════════════════════${NC}"
echo ""

# Check if directories exist
if [ ! -d "$OTEL_DIR" ]; then
    echo -e "${RED}✗ OTEL receiver directory not found: $OTEL_DIR${NC}"
    exit 1
fi

if [ ! -d "$API_DIR" ]; then
    echo -e "${RED}✗ WebSearch API directory not found: $API_DIR${NC}"
    exit 1
fi

# Start OTEL Receiver
echo -e "${BLUE}[1/2] Starting OTEL Receiver...${NC}"
cd "$OTEL_DIR"
if [ -x "run.sh" ]; then
    ./run.sh start
else
    echo -e "${YELLOW}No run.sh found, using docker-compose...${NC}"
    docker-compose up -d
fi

echo ""
sleep 3

# Start WebSearch API Services
echo -e "${BLUE}[2/2] Starting WebSearch API Services...${NC}"
cd "$API_DIR"
if [ -x "run.sh" ]; then
    ./run.sh services
else
    echo -e "${YELLOW}No run.sh found, using docker-compose...${NC}"
    docker-compose up -d mongodb redis
fi

echo ""
echo -e "${GREEN}════════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}✓ All services started!${NC}"
echo -e "${GREEN}════════════════════════════════════════════════════════════${NC}"
echo ""

# Show status
echo -e "${YELLOW}OTEL Receiver Status:${NC}"
cd "$OTEL_DIR"
docker-compose ps
echo ""

echo -e "${YELLOW}WebSearch API Status:${NC}"
cd "$API_DIR"
docker-compose ps
echo ""

# Show access info
echo -e "${BLUE}════════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}Access Information:${NC}"
echo -e "${BLUE}════════════════════════════════════════════════════════════${NC}"
echo ""
echo -e "${YELLOW}OTEL Receiver:${NC}"
echo "  • Jaeger UI:    http://localhost:17686"
echo "  • Grafana:      http://localhost:3002 (admin/admin)"
echo "  • Prometheus:   http://localhost:9091"
echo "  • Health:       http://localhost:14133/health"
echo ""
echo -e "${YELLOW}WebSearch API:${NC}"
echo "  • Services:     MongoDB, Redis (running)"
echo "  • API:          Ready to start"
echo ""
echo -e "${BLUE}════════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}Next Steps:${NC}"
echo -e "${BLUE}════════════════════════════════════════════════════════════${NC}"
echo ""
echo "Start the WebSearch API:"
echo "  cd $API_DIR"
echo "  ./run.sh api"
echo ""
echo "Or run everything in one terminal:"
echo "  cd $API_DIR"
echo "  poetry run uvicorn src.main:app --host 0.0.0.0 --port 8000"
echo ""
echo -e "${BLUE}════════════════════════════════════════════════════════════${NC}${NC}"
