#!/bin/bash
# WebSearch API Run Script - Supports Local Docker and Kubernetes

set -e
cd "$(dirname "$0")"

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

ADMIN_API_KEY="GA_Incg4zEhpK-65G6PwL499t2kXvH2Cs-hWf6udtZU"

# Detect deployment mode (local or k8s)
DEPLOY_MODE="${DEPLOY_MODE:-local}"

show_help() {
    cat << EOF
===============================================================
        WebSearch API Management Script
===============================================================

Usage: ./run.sh [command] [options]

Deployment Modes:
  DEPLOY_MODE=local  ./run.sh [command]    # Local Docker (default)
  DEPLOY_MODE=k8s    ./run.sh [command]    # Kubernetes

Commands:
  start         Start the WebSearch API
  stop          Stop all services
  restart       Restart all services
  rebuild       Rebuild app images and rolling-restart pods (k8s mode only)
  api           Start only the API server (local mode only)
  services      Start only MongoDB and Redis (local mode only)
  status        Show service status
  logs          Show API logs
  test          Run a test search
                  --pretty, -f    Format output (pretty display)
                  --json          JSON output (default)
                  --trace         Detailed trace output
  health        Check API health
  admin         Create a new admin user (local mode only)
  shell         Open API shell (local mode only)
  install       Install dependencies (local mode only)
  clean         Stop and remove all data
  help          Show this help

Examples:
  # Local Docker (default)
  ./run.sh start              # Start everything with docker-compose
  ./run.sh test --pretty      # Test search (formatted output)
  
  # Kubernetes
  DEPLOY_MODE=k8s ./run.sh start      # Deploy to Kubernetes
  DEPLOY_MODE=k8s ./run.sh status     # Check K8s deployment status
  DEPLOY_MODE=k8s ./run.sh test       # Test search via ingress
  DEPLOY_MODE=k8s ./run.sh clean      # Clean up K8s deployment

Access URLs:
  Local:         http://localhost:8000 (API), http://localhost:3000 (Dashboard)
  Kubernetes:    http://localhost/ (Dashboard & API via ingress)

Current Mode: ${DEPLOY_MODE}

===============================================================
EOF
}

check_poetry() {
    if ! command -v poetry &> /dev/null; then
        echo -e "${RED}[ERROR] Poetry is not installed${NC}"
        echo "Install: curl -sSL https://install.python-poetry.org | python3 -"
        exit 1
    fi
}

check_docker() {
    if ! command -v docker &> /dev/null; then
        echo -e "${RED}[ERROR] Docker is not installed${NC}"
        exit 1
    fi
    
    if ! docker info &> /dev/null; then
        echo -e "${RED}[ERROR] Docker daemon is not running${NC}"
        exit 1
    fi
}

check_kubectl() {
    if ! command -v kubectl &> /dev/null; then
        echo -e "${RED}[ERROR] kubectl is not installed${NC}"
        echo "Install kubectl for Kubernetes management"
        exit 1
    fi
}


# ============================================================================
# Kubernetes Commands
# ============================================================================

cmd_k8s_start() {
    echo -e "${BLUE}Deploying WebSearch API to Kubernetes...${NC}"
    check_kubectl
    check_docker
    
    cd k8s
    ./deploy.sh
    cd ..
    
    echo ""
    echo -e "${GREEN}[OK] Kubernetes deployment complete${NC}"
    echo ""
    echo -e "${CYAN}Access URLs:${NC}"
    echo -e "  Dashboard: ${BLUE}http://localhost/${NC}"
    echo -e "  API:       ${BLUE}http://localhost/api/v1/${NC}"
    echo ""
    echo -e "${YELLOW}Login: admin / admin${NC}"
}

cmd_k8s_stop() {
    echo -e "${BLUE}Stopping Kubernetes deployment...${NC}"
    check_kubectl
    
    cd k8s
    ./cleanup.sh
    cd ..
    
    echo -e "${GREEN}[OK] Kubernetes deployment stopped${NC}"
}

cmd_k8s_status() {
    echo -e "${BLUE}Checking Kubernetes deployment status...${NC}"
    check_kubectl
    
    echo ""
    echo "==============================================================="
    echo "Kubernetes Deployment Status:"
    echo "==============================================================="
    echo ""
    
    echo -e "${YELLOW}Pods:${NC}"
    kubectl get pods -n websearch-api 2>/dev/null || echo "No deployment found"
    
    echo ""
    echo -e "${YELLOW}Services:${NC}"
    kubectl get svc -n websearch-api 2>/dev/null || echo "No services found"
    
    echo ""
    echo -e "${YELLOW}Ingress:${NC}"
    kubectl get ingress -n websearch-api 2>/dev/null || echo "No ingress found"
    
    echo ""
}

cmd_k8s_logs() {
    echo -e "${BLUE}Showing Kubernetes API logs (Ctrl+C to stop)...${NC}"
    check_kubectl

    kubectl logs -f deployment/websearch-api -n websearch-api
}

cmd_k8s_rebuild() {
    echo -e "${BLUE}Rebuilding and rolling out application images...${NC}"
    check_kubectl
    check_docker

    VERSION=$(grep '^version = ' pyproject.toml | sed 's/version = "\(.*\)"/\1/')
    echo -e "${CYAN}Version: ${VERSION}${NC}"

    echo "Building API image..."
    docker build -t websearch-api:${VERSION} -t websearch-api:latest -f Dockerfile .

    echo "Building Dashboard image..."
    docker build -t websearch-dashboard:${VERSION} -t websearch-dashboard:latest -f Dockerfile.dashboard .

    echo "Rolling out new images..."
    kubectl set image deployment/websearch-api api=websearch-api:${VERSION} -n websearch-api
    kubectl set image deployment/dashboard dashboard=websearch-dashboard:${VERSION} -n websearch-api

    echo "Waiting for rollout..."
    kubectl rollout status deployment/websearch-api -n websearch-api
    kubectl rollout status deployment/dashboard -n websearch-api

    echo -e "${GREEN}[OK] Rollout complete (v${VERSION})${NC}"
}

# ============================================================================
# Local Docker Commands
# ============================================================================

cmd_install() {
    echo -e "${BLUE}Installing dependencies...${NC}"
    check_poetry
    poetry install --no-interaction
    echo -e "${GREEN}[OK] Dependencies installed${NC}"
}

cmd_services() {
    echo -e "${BLUE}Starting MongoDB and Redis...${NC}"
    check_docker
    
    docker-compose up -d mongodb redis
    
    echo ""
    echo -e "${GREEN}[OK] Services started${NC}"
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
    if [ "$DEPLOY_MODE" = "k8s" ]; then
        cmd_k8s_start
    else
        echo -e "${BLUE}Starting WebSearch API stack (Local Docker)...${NC}"
        
        # Start services
        cmd_services
        echo ""
        
        # Start API in foreground
        echo -e "${BLUE}Starting API server...${NC}"
        sleep 2
        cmd_api
    fi
}

cmd_stop() {
    if [ "$DEPLOY_MODE" = "k8s" ]; then
        cmd_k8s_stop
    else
        echo -e "${BLUE}Stopping WebSearch API (Local Docker)...${NC}"
        
        # Find and stop API process
        API_PID=$(pgrep -f "uvicorn src.main:app" 2>/dev/null || echo "")
        if [ -n "$API_PID" ]; then
            echo "Stopping API (PID: $API_PID)..."
            kill "$API_PID" 2>/dev/null || true
            echo -e "${GREEN}[OK] API stopped${NC}"
        fi
        
        # Stop Docker services
        docker-compose down
        echo -e "${GREEN}[OK] Services stopped${NC}"
    fi
}

cmd_restart() {
    echo -e "${BLUE}Restarting WebSearch API...${NC}"
    cmd_stop
    sleep 2
    cmd_start
}

cmd_status() {
    if [ "$DEPLOY_MODE" = "k8s" ]; then
        cmd_k8s_status
    else
        echo "==============================================================="
        echo "Service Status (Local Docker):"
        echo "==============================================================="
        
        # Check Docker services
        docker-compose ps 2>/dev/null || echo "No Docker services running"
        
        echo ""
        
        # Check API
        if pgrep -f "uvicorn src.main:app" > /dev/null; then
            echo -e "${GREEN}[OK] API Server: Running${NC}"
        else
            echo -e "${YELLOW}[ ] API Server: Stopped${NC}"
        fi
        
        echo ""
    fi
}

cmd_logs() {
    if [ "$DEPLOY_MODE" = "k8s" ]; then
        cmd_k8s_logs
    else
        echo -e "${BLUE}Following API logs (Ctrl+C to stop)...${NC}"
        
        if [ -d "logs" ]; then
            tail -f logs/*.log
        else
            echo -e "${YELLOW}No logs directory found. Run the API first.${NC}"
        fi
    fi
}

cmd_test() {
    local format="json"
    local query="OpenTelemetry"
    local api_key="${ADMIN_API_KEY}"
    local max_results=5
    local user_email=""
    
    # Set API URL based on deployment mode
    local api_url="http://localhost:8000"
    if [ "$DEPLOY_MODE" = "k8s" ]; then
        api_url="http://localhost"
    fi
    
    # Parse flags
    while [[ $# -gt 0 ]]; do
        case $1 in
            --pretty|--format|-f)
                format="pretty"
                shift
                ;;
            --json)
                format="json"
                shift
                ;;
            --trace)
                format="trace"
                shift
                ;;
            -q|--query)
                query="$2"
                shift 2
                ;;
            -k|--key)
                api_key="$2"
                shift 2
                ;;
            --user)
                user_email="$2"
                shift 2
                ;;
            -m|--max)
                max_results="$2"
                shift 2
                ;;
            *)
                shift
                ;;
        esac
    done
    
    echo -e "${BLUE}Running test search (${DEPLOY_MODE} mode)...${NC}"
    
    # Check if API is running
    local health_url="${api_url}/api/v1/health"
    if ! curl -s "$health_url" > /dev/null 2>&1; then
        echo -e "${RED}[ERROR] API is not running${NC}"
        if [ "$DEPLOY_MODE" = "k8s" ]; then
            echo -e "${YELLOW}Deploy to Kubernetes first: DEPLOY_MODE=k8s ./run.sh start${NC}"
        else
            echo -e "${YELLOW}Start the API first with: ./run.sh start${NC}"
        fi
        return 1
    fi
    
    echo -e "${GREEN}[OK] API is running${NC}"
    echo ""
    
    # If user email provided, request API key
    if [ -n "$user_email" ]; then
        echo -e "${YELLOW}Requesting API key for ${user_email}...${NC}"
        key_response=$(curl -X POST ${api_url}/api/v1/auth/request-key \
            -H "Content-Type: application/json" \
            -d "{\"email\": \"$user_email\"}" \
            -s)
        
        api_key=$(echo "$key_response" | python3 -c "import sys, json; print(json.load(sys.stdin).get('api_key', ''))" 2>/dev/null)
        
        if [ -z "$api_key" ]; then
            echo -e "${RED}[ERROR] Failed to get API key for $user_email${NC}"
            echo "$key_response"
            return 1
        fi
        
        # Extract user info
        user_name=$(echo "$key_response" | python3 -c "import sys, json; print(json.load(sys.stdin).get('name', ''))" 2>/dev/null)
        user_groups=$(echo "$key_response" | python3 -c "import sys, json; print(', '.join(json.load(sys.stdin).get('groups', [])))" 2>/dev/null)
        daily_limit=$(echo "$key_response" | python3 -c "import sys, json; print(json.load(sys.stdin).get('quotas', {}).get('daily_limit', 0))" 2>/dev/null)
        monthly_limit=$(echo "$key_response" | python3 -c "import sys, json; print(json.load(sys.stdin).get('quotas', {}).get('monthly_limit', 0))" 2>/dev/null)
        
        echo -e "${GREEN}[OK] API key generated successfully${NC}"
        echo ""
        echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
        echo -e "${CYAN}User:${NC} ${user_name}"
        echo -e "${CYAN}Groups:${NC} ${user_groups}"
        echo -e "${CYAN}Daily Quota:${NC} ${daily_limit} searches"
        echo -e "${CYAN}Monthly Quota:${NC} ${monthly_limit} searches"
        echo ""
        echo -e "${YELLOW}API Key (store securely):${NC}"
        echo -e "${GREEN}${api_key}${NC}"
        echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
        echo ""
    fi
    
    # Run test search
    response=$(curl -X POST ${api_url}/api/v1/search \
        -H "X-API-Key: ${api_key}" \
        -H "Content-Type: application/json" \
        -d "{\"query\": \"$query\", \"max_results\": $max_results}" \
        -s -w "\n%{http_code}")
    
    http_code=$(echo "$response" | tail -n1)
    body=$(echo "$response" | sed '$d')
    
    if [ "$http_code" = "200" ]; then
        echo -e "${GREEN}[OK] Search successful (HTTP $http_code)${NC}"
        echo ""
        
        if [ "$format" = "trace" ]; then
            # Trace format with detailed information
            echo -e "${BLUE}════════════════════════════════════════════════════════════${NC}"
            echo -e "${GREEN}SEARCH TRACE${NC}"
            echo -e "${BLUE}════════════════════════════════════════════════════════════${NC}"
            echo ""
            
            echo -e "${YELLOW}Request:${NC}"
            echo -e "  Query: \"$query\""
            echo -e "  Max Results: $max_results"
            if [ -n "$user_email" ]; then
                echo -e "  User: $user_email"
            fi
            echo -e "  API Key: ${api_key:0:10}...***"
            echo ""
            
            # Extract metadata
            provider=$(echo "$body" | python3 -c "import sys, json; print(json.load(sys.stdin).get('provider', 'N/A'))" 2>/dev/null)
            total=$(echo "$body" | python3 -c "import sys, json; print(json.load(sys.stdin).get('total_results', 0))" 2>/dev/null)
            response_time=$(echo "$body" | python3 -c "import sys, json; print(f\"{json.load(sys.stdin).get('response_time_ms', 0):.2f}\")" 2>/dev/null)
            
            echo -e "${YELLOW}Provider Selection:${NC}"
            echo -e "  Selected: $provider"
            echo ""
            
            echo -e "${YELLOW}Performance:${NC}"
            echo -e "  Total Time: ${response_time}ms"
            echo ""
            
            echo -e "${YELLOW}Results:${NC}"
            echo -e "  Total Found: $total"
            echo -e "  Returned: $(echo "$body" | python3 -c "import sys, json; print(len(json.load(sys.stdin).get('results', [])))" 2>/dev/null)"
            echo ""
            
            # Quota info
            echo "$body" | python3 << 'PYTHON_SCRIPT'
import sys
import json

try:
    data = json.load(sys.stdin)
    
    # Quota info
    quota = data.get("quota_info", {})
    if quota:
        daily = quota.get("daily", {})
        monthly = quota.get("monthly", {})
        print("\033[1;33mQuota Status:\033[0m")
        if daily:
            used = daily.get("used", 0)
            limit = daily.get("limit", 0)
            print(f"  Today: {used} / {limit} searches")
        if monthly:
            used = monthly.get("used", 0)
            limit = monthly.get("limit", 0)
            print(f"  This Month: {used:,} / {limit:,} searches")
        print()
    
    # Show a few results
    results = data.get("results", [])
    if results:
        print("\033[1;33mSample Results:\033[0m")
        for i, result in enumerate(results[:3], 1):
            title = result.get("title", "No Title")
            url = result.get("url", "")
            print(f"  {i}. {title}")
            print(f"     {url}")
        print()
        
except Exception as e:
    print(f"Error: {e}", file=sys.stderr)
PYTHON_SCRIPT
            echo -e "${BLUE}════════════════════════════════════════════════════════════${NC}"
            
        elif [ "$format" = "pretty" ]; then
            # Pretty formatted output
            echo -e "${BLUE}════════════════════════════════════════════════════════════${NC}"
            echo -e "${GREEN}Search Results for: $query${NC}"
            echo -e "${BLUE}════════════════════════════════════════════════════════════${NC}"
            echo ""
            
            # Extract metadata
            provider=$(echo "$body" | python3 -c "import sys, json; print(json.load(sys.stdin).get('provider', 'N/A'))" 2>/dev/null)
            total=$(echo "$body" | python3 -c "import sys, json; print(json.load(sys.stdin).get('total_results', 0))" 2>/dev/null)
            response_time=$(echo "$body" | python3 -c "import sys, json; print(f\"{json.load(sys.stdin).get('response_time_ms', 0):.2f}\")" 2>/dev/null)
            
            echo -e "${YELLOW}Provider:${NC} $provider"
            echo -e "${YELLOW}Total Results:${NC} $total"
            echo -e "${YELLOW}Response Time:${NC} ${response_time}ms"
            echo ""
            echo -e "${BLUE}────────────────────────────────────────────────────────────${NC}"
            echo ""
            
            # Parse and display results
            echo "$body" | python3 -c '
import sys
import json

try:
    data = json.load(sys.stdin)
    results = data.get("results", [])
    
    for i, result in enumerate(results, 1):
        title = result.get("title", "No Title")
        url = result.get("url", "N/A")
        snippet = result.get("snippet", "No description")
        
        print(f"\033[1;36m[{i}] {title}\033[0m")
        print(f"    \033[0;33mURL:\033[0m {url}")
        
        if len(snippet) > 120:
            snippet = snippet[:117] + "..."
        print(f"    \033[0;37m{snippet}\033[0m")
        print()
    
    # Rate limit info
    rate_limit = data.get("rate_limit_info", {})
    if rate_limit:
        print("\033[0;34m────────────────────────────────────────────────────────────\033[0m")
        remaining = rate_limit.get("remaining", 0)
        limit = rate_limit.get("limit", 0)
        print(f"\033[1;33mRate Limit:\033[0m {remaining}/{limit} remaining")
        
    # Quota info
    quota = data.get("quota_info", {})
    if quota:
        monthly = quota.get("monthly", {})
        remaining = monthly.get("remaining", 0)
        limit = monthly.get("limit", 0)
        print(f"\033[1;33mMonthly Quota:\033[0m {remaining:,}/{limit:,} remaining")

except Exception as e:
    print(f"Error parsing results: {e}", file=sys.stderr)
    sys.exit(1)
'
            
            echo ""
            echo -e "${BLUE}════════════════════════════════════════════════════════════${NC}"
        else
            # JSON output
            echo "$body" | python3 -m json.tool
        fi
    else
        echo -e "${RED}[ERROR] Search failed (HTTP $http_code)${NC}"
        echo "$body"
        return 1
    fi
    
    echo ""
    echo -e "${GREEN}[OK] Test complete${NC}"
}

cmd_health() {
    echo -e "${BLUE}Checking API health...${NC}"
    
    local health_url="http://localhost:8000/health"
    if [ "$DEPLOY_MODE" = "k8s" ]; then
        health_url="http://localhost/api/v1/health"
    fi
    
    response=$(curl -s "$health_url")
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}[OK] API is healthy (${DEPLOY_MODE} mode)${NC}"
        echo "$response" | python3 -m json.tool 2>/dev/null || echo "$response"
    else
        echo -e "${RED}[ERROR] API is not responding${NC}"
        if [ "$DEPLOY_MODE" = "k8s" ]; then
            echo "Make sure Kubernetes deployment is running: DEPLOY_MODE=k8s ./run.sh start"
        else
            echo "Make sure the API is running: ./run.sh start"
        fi
        exit 1
    fi
}

cmd_admin() {
    if [ "$DEPLOY_MODE" = "k8s" ]; then
        echo -e "${YELLOW}Admin user creation is not supported in Kubernetes mode${NC}"
        echo "The admin user is created automatically during deployment"
        echo "Login: admin / admin"
        return 0
    fi
    
    echo -e "${BLUE}Creating admin user...${NC}"
    check_poetry
    
    poetry run python scripts/create_admin.py
    
    echo -e "${GREEN}[OK] Admin user created${NC}"
}

cmd_shell() {
    echo -e "${BLUE}Opening Poetry shell...${NC}"
    check_poetry
    poetry shell
}

cmd_clean() {
    if [ "$DEPLOY_MODE" = "k8s" ]; then
        echo -e "${RED}WARNING: This will delete the entire Kubernetes deployment!${NC}"
        read -p "Are you sure? (yes/no): " confirm
        
        if [ "$confirm" = "yes" ]; then
            echo -e "${BLUE}Cleaning Kubernetes deployment...${NC}"
            cmd_k8s_stop
            echo -e "${GREEN}[OK] Kubernetes deployment cleaned${NC}"
        else
            echo "Cancelled"
        fi
    else
        echo -e "${RED}WARNING: This will delete all data (MongoDB, Redis)!${NC}"
        read -p "Are you sure? (yes/no): " confirm
        
        if [ "$confirm" = "yes" ]; then
            echo -e "${BLUE}Stopping and cleaning...${NC}"
            cmd_stop
            docker-compose down -v
            rm -rf logs/*
            echo -e "${GREEN}[OK] All data cleaned${NC}"
        else
            echo "Cancelled"
        fi
    fi
}

# Validate local-only commands
validate_local_mode() {
    if [ "$DEPLOY_MODE" = "k8s" ]; then
        echo -e "${RED}[ERROR] This command is only available in local mode${NC}"
        echo "Remove DEPLOY_MODE=k8s or use DEPLOY_MODE=local"
        exit 1
    fi
}

case "${1:-help}" in
    start) cmd_start ;;
    stop) cmd_stop ;;
    restart) cmd_restart ;;
    rebuild)
        if [ "$DEPLOY_MODE" != "k8s" ]; then
            echo -e "${RED}[ERROR] rebuild is only available in k8s mode${NC}"
            exit 1
        fi
        cmd_k8s_rebuild
        ;;
    api) 
        validate_local_mode
        cmd_api 
        ;;
    services) 
        validate_local_mode
        cmd_services 
        ;;
    status) cmd_status ;;
    logs) cmd_logs ;;
    test) 
        shift
        cmd_test "$@"
        ;;
    health) cmd_health ;;
    admin) cmd_admin ;;
    shell) 
        validate_local_mode
        cmd_shell 
        ;;
    install) 
        validate_local_mode
        cmd_install 
        ;;
    clean) cmd_clean ;;
    *) show_help ;;
esac
