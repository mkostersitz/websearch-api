#!/bin/bash

# Stop All - Master script to stop both projects
# Stops WebSearch API and OTEL Receiver

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
echo -e "${YELLOW}Stopping All Enterprise Services${NC}"
echo -e "${BLUE}════════════════════════════════════════════════════════════${NC}"
echo ""

# Stop WebSearch API Services
echo -e "${BLUE}[1/2] Stopping WebSearch API Services...${NC}"
if [ -d "$API_DIR" ]; then
    cd "$API_DIR"
    if [ -x "run.sh" ]; then
        ./run.sh stop
    else
        docker-compose down
    fi
else
    echo -e "${YELLOW}WebSearch API directory not found${NC}"
fi

echo ""

# Stop OTEL Receiver
echo -e "${BLUE}[2/2] Stopping OTEL Receiver...${NC}"
if [ -d "$OTEL_DIR" ]; then
    cd "$OTEL_DIR"
    if [ -x "run.sh" ]; then
        ./run.sh stop
    else
        docker-compose down
    fi
else
    echo -e "${YELLOW}OTEL Receiver directory not found${NC}"
fi

echo ""
echo -e "${GREEN}════════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}✓ All services stopped!${NC}"
echo -e "${GREEN}════════════════════════════════════════════════════════════${NC}"
echo ""
