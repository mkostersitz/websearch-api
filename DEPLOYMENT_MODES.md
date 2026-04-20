# Deployment Modes Guide

The WebSearch API supports two deployment modes:
- **Local Docker** - Development and testing using docker-compose
- **Kubernetes** - Production deployment on Kubernetes clusters

## Quick Reference

```bash
# Local Docker mode (default)
./run.sh start
./run.sh status
./run.sh health

# Kubernetes mode
DEPLOY_MODE=k8s ./run.sh start
DEPLOY_MODE=k8s ./run.sh status
DEPLOY_MODE=k8s ./run.sh health
```

## Local Docker Mode

**Use for:** Development, testing, quick starts

**Requirements:**
- Docker Desktop or Docker Engine
- Docker Compose
- Poetry (Python package manager)

**Commands:**
```bash
# Install dependencies
./run.sh install

# Start services (MongoDB, Redis)
./run.sh services

# Start API server (with auto-reload)
./run.sh api

# Start everything (services + API)
./run.sh start

# Check status
./run.sh status

# View logs
./run.sh logs

# Test the API
./run.sh test -q "OpenTelemetry" --pretty

# Check health
./run.sh health

# Create admin user
./run.sh admin

# Open Python shell
./run.sh shell

# Stop everything
./run.sh stop

# Clean all data (WARNING: destructive)
./run.sh clean
```

**Access URLs:**
- API: http://localhost:8000/api/v1/
- API Docs: http://localhost:8000/docs
- Dashboard: Separate deployment required

**Architecture:**
```
Browser
   ↓
localhost:8000 (API via Poetry/uvicorn)
   ↓
   ├─→ MongoDB (Docker, port 27017)
   └─→ Redis (Docker, port 6379)
```

**Pros:**
- Fast startup
- Hot reload for development
- Direct access to code
- Easy debugging
- Low resource usage

**Cons:**
- Not production-ready
- Single instance (no HA)
- Manual service management
- No ingress/routing

## Kubernetes Mode

**Use for:** Production, staging, integration testing

**Requirements:**
- Kubernetes cluster (Docker Desktop, minikube, cloud cluster)
- kubectl installed and configured
- Docker for building images

**Commands:**
```bash
# Deploy entire stack to K8s
DEPLOY_MODE=k8s ./run.sh start

# Check deployment status
DEPLOY_MODE=k8s ./run.sh status

# View API logs
DEPLOY_MODE=k8s ./run.sh logs

# Test the API
DEPLOY_MODE=k8s ./run.sh test -q "OpenTelemetry" --pretty

# Check health
DEPLOY_MODE=k8s ./run.sh health

# Stop deployment
DEPLOY_MODE=k8s ./run.sh stop

# Clean deployment (WARNING: destructive)
DEPLOY_MODE=k8s ./run.sh clean
```

**Access URLs:**
- Dashboard: http://localhost/
- API: http://localhost/api/v1/
- Grafana: Use port-forwarding (k8s/port-forward.sh)
- Jaeger: Use port-forwarding (k8s/port-forward.sh)
- Prometheus: Use port-forwarding (k8s/port-forward.sh)

**Architecture:**
```
Browser (localhost:80)
   ↓
nginx-ingress-controller (LoadBalancer)
   ↓
   ├─→ /api/v1/* → websearch-api (ClusterIP, 2 replicas)
   └─→ /* → dashboard (ClusterIP, 2 replicas)
   
Internal Services:
   ├─→ MongoDB (StatefulSet)
   ├─→ Redis (Deployment)
   ├─→ OTEL Collector (Deployment)
   ├─→ Jaeger (Deployment)
   ├─→ Prometheus (Deployment)
   └─→ Grafana (Deployment)
```

**Pros:**
- Production-ready
- High availability (multiple replicas)
- Automatic scaling
- Service discovery
- Ingress routing
- Complete observability stack

**Cons:**
- Slower startup
- Higher resource usage
- More complex debugging
- Requires K8s knowledge

## Command Availability by Mode

| Command    | Local | Kubernetes | Notes                              |
|------------|-------|------------|------------------------------------|
| `start`    | ✅    | ✅         | Different implementations          |
| `stop`     | ✅    | ✅         | Different implementations          |
| `restart`  | ✅    | ✅         | Calls stop + start                 |
| `status`   | ✅    | ✅         | Different output formats           |
| `logs`     | ✅    | ✅         | tail vs kubectl logs               |
| `test`     | ✅    | ✅         | Different API URLs                 |
| `health`   | ✅    | ✅         | Different API URLs                 |
| `api`      | ✅    | ❌         | Local only - Poetry/uvicorn        |
| `services` | ✅    | ❌         | Local only - docker-compose        |
| `admin`    | ✅    | ⚠️         | K8s: auto-created, login shown     |
| `shell`    | ✅    | ❌         | Local only - Poetry shell          |
| `install`  | ✅    | ❌         | Local only - Poetry install        |
| `clean`    | ✅    | ✅         | Different cleanup procedures       |

## Switching Between Modes

**From Local to Kubernetes:**
```bash
# Stop local services
./run.sh stop

# Deploy to Kubernetes
DEPLOY_MODE=k8s ./run.sh start

# Access via ingress
curl http://localhost/api/v1/health
```

**From Kubernetes to Local:**
```bash
# Stop Kubernetes deployment
DEPLOY_MODE=k8s ./run.sh stop

# Start local services
./run.sh start

# Access via localhost:8000
curl http://localhost:8000/api/v1/health
```

## Environment Variables

### DEPLOY_MODE
Controls which deployment mode to use.

**Values:**
- `local` - Local Docker mode (default)
- `k8s` - Kubernetes mode

**Examples:**
```bash
# Explicit local mode
DEPLOY_MODE=local ./run.sh start

# Kubernetes mode
DEPLOY_MODE=k8s ./run.sh start

# Default (local)
./run.sh start
```

### ADMIN_API_KEY
Admin API key for testing.

**Used by:** `./run.sh test`

**Example:**
```bash
ADMIN_API_KEY=your-key ./run.sh test -q "search query"
```

## Troubleshooting

### "This command is only available in local mode"
**Problem:** You're trying to use a local-only command in K8s mode.

**Solution:**
```bash
# Remove DEPLOY_MODE=k8s or switch to local
./run.sh install

# Instead of:
DEPLOY_MODE=k8s ./run.sh install  # ERROR
```

### "kubectl: command not found"
**Problem:** kubectl is not installed.

**Solution:**
```bash
# macOS
brew install kubectl

# Linux
curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
sudo install -o root -g root -m 0755 kubectl /usr/local/bin/kubectl
```

### "No deployment found"
**Problem:** Kubernetes deployment hasn't been created yet.

**Solution:**
```bash
DEPLOY_MODE=k8s ./run.sh start
```

### Health check fails in K8s mode
**Problem:** Ingress not ready or API not responding.

**Solution:**
```bash
# Check deployment status
DEPLOY_MODE=k8s ./run.sh status

# Check API logs
DEPLOY_MODE=k8s ./run.sh logs

# Verify ingress
kubectl get ingress -n websearch-api
```

## Best Practices

### Development Workflow
1. Use **local mode** for active development
2. Hot reload keeps code changes instant
3. Use Poetry shell for debugging
4. Test locally before deploying to K8s

### Testing Workflow
1. Test in **local mode** first
2. Deploy to **K8s mode** for integration tests
3. Use `./run.sh test` in both modes
4. Verify health checks pass

### Production Workflow
1. Use **K8s mode** exclusively
2. Never use local mode in production
3. Monitor with Grafana/Prometheus
4. Use ingress for external access

## Examples

### Complete Local Development Cycle
```bash
# Install dependencies
./run.sh install

# Start services
./run.sh start

# Make code changes (auto-reload active)

# Test changes
./run.sh test -q "test query" --pretty

# Check health
./run.sh health

# View logs
./run.sh logs

# Stop when done
./run.sh stop
```

### Complete Kubernetes Deployment
```bash
# Deploy to Kubernetes
DEPLOY_MODE=k8s ./run.sh start

# Wait for deployment
# (Output shows when ready)

# Check status
DEPLOY_MODE=k8s ./run.sh status

# Test API
DEPLOY_MODE=k8s ./run.sh test -q "test query" --pretty

# Check health
DEPLOY_MODE=k8s ./run.sh health

# Access dashboard
open http://localhost/

# View logs if needed
DEPLOY_MODE=k8s ./run.sh logs

# Stop when done
DEPLOY_MODE=k8s ./run.sh stop
```

### Testing in Both Modes
```bash
# Test locally
./run.sh start
./run.sh test -q "OpenTelemetry" --pretty
./run.sh stop

# Test in K8s
DEPLOY_MODE=k8s ./run.sh start
DEPLOY_MODE=k8s ./run.sh test -q "OpenTelemetry" --pretty
DEPLOY_MODE=k8s ./run.sh stop
```

## See Also

- [README.md](README.md) - Project overview
- [k8s/README.md](k8s/README.md) - Kubernetes deployment details
- [k8s/QUICKSTART.md](k8s/QUICKSTART.md) - 5-minute K8s setup guide
- [k8s/INGRESS_ACCESS.md](k8s/INGRESS_ACCESS.md) - Ingress configuration guide
