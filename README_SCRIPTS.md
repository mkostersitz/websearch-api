# Master Infrastructure Scripts

This directory contains master scripts for managing the entire infrastructure stack.

## Scripts

### start-all.sh

Starts all infrastructure services in the correct order:

1. **OTEL Observability Stack** (in ../otel/otel-receiver)
   - Jaeger (distributed tracing)
   - Prometheus (metrics)
   - Grafana (dashboards)
   - Loki (logs)
   - OTEL Collector (telemetry aggregation)

2. **WebSearch API Dependencies**
   - MongoDB (database)
   - Redis (cache)

**Usage:**
```bash
cd /Users/mikek/repos/websearch-api
./start-all.sh
```

**What it does:**
- Validates directories exist
- Starts OTEL stack using run.sh
- Starts MongoDB and Redis
- Shows status and access information
- Displays next steps

### stop-all.sh

Stops all infrastructure services.

**Usage:**
```bash
cd /Users/mikek/repos/websearch-api
./stop-all.sh
```

**What it does:**
- Stops WebSearch API (if running)
- Stops MongoDB and Redis
- Stops OTEL stack
- Confirms all services stopped

## Workflow

### 1. Start Infrastructure

```bash
cd /Users/mikek/repos/websearch-api
./start-all.sh
```

This starts everything except the API itself.

### 2. Start the API

```bash
# Option A: Using run.sh
./run.sh api

# Option B: Using Poetry directly
poetry run uvicorn src.main:app --host 0.0.0.0 --port 8000

# Option C: Development mode with auto-reload
poetry run uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload
```

### 3. Access Services

- **WebSearch API:** http://localhost:8000
- **API Docs:** http://localhost:8000/docs
- **Jaeger UI:** http://localhost:17686
- **Grafana:** http://localhost:3002
- **Prometheus:** http://localhost:9091

### 4. Stop Everything

```bash
# Stop just the API
./run.sh stop

# Stop all infrastructure
./stop-all.sh
```

## Directory Structure

```
repos/
├── otel/
│   └── otel-receiver/          # OTEL observability stack
│       └── run.sh
└── websearch-api/              # WebSearch API (you are here)
    ├── start-all.sh            # Master start script
    ├── stop-all.sh             # Master stop script
    ├── run.sh                  # API management script
    └── README_SCRIPTS.md       # This file
```

## Troubleshooting

### Scripts fail with "directory not found"

Ensure the directory structure is correct:
```bash
ls -la /Users/mikek/repos/otel/otel-receiver/
ls -la /Users/mikek/repos/websearch-api/
```

### Port conflicts

Check if ports are already in use:
```bash
lsof -i :17686  # Jaeger
lsof -i :3002   # Grafana  
lsof -i :9091   # Prometheus
lsof -i :8000   # WebSearch API
lsof -i :27017  # MongoDB
lsof -i :6379   # Redis
```

### Services won't start

Try a clean restart:
```bash
./stop-all.sh
docker system prune -f
./start-all.sh
```

### View logs

```bash
# OTEL services
cd /Users/mikek/repos/otel/otel-receiver
./run.sh logs [service]

# WebSearch API services
./run.sh logs [mongodb|redis]
```

## Notes

- The scripts use absolute paths, so they work from any directory
- OTEL stack must be started before the WebSearch API
- MongoDB and Redis are started automatically
- The API itself must be started separately with `./run.sh api`
- All scripts have colorized output for better readability
