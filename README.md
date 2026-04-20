# WebSearch API for AI Agents

Enterprise-grade web search API designed for AI agents with comprehensive security, observability, and policy enforcement.

## 🎯 Features

- 🔐 **Multi-Auth Support**: OAuth (Okta, Entra ID), API Keys, Client Certificates
- 📊 **Full Observability**: OpenTelemetry with distributed tracing (Jaeger, Prometheus)
- 🛡️ **Enterprise Guardrails**: Content filtering, parental controls, domain policies
- 🚦 **Rate Limiting**: Distributed throttling with Redis (60 req/min default)
- 🔄 **Provider Fallback**: Multi-provider search (Google, Bing) with automatic failover
- 📈 **Admin Dashboard**: React-based UI with Settings, Analytics, Client Management
- ⚙️ **Pinnable Sidebar**: Customizable navigation with persistent state
- 🔍 **Audit Logging**: Complete audit trail for compliance
- ⚡ **High Performance**: Async operations, caching, connection pooling
- ☸️ **Kubernetes Ready**: Production deployment with ingress, HA, and auto-scaling

## 🚀 Quick Start

**Choose your deployment mode:**

### Local Docker (Development)
```bash
# Install and start
./run.sh install
./run.sh start

# Access API
curl http://localhost:8000/api/v1/health
```

### Kubernetes (Production)
```bash
# Deploy to Kubernetes
DEPLOY_MODE=k8s ./run.sh start

# Access via ingress
open http://localhost/
```

**📖 See [DEPLOYMENT_MODES.md](DEPLOYMENT_MODES.md) for complete guide**

## 📋 Prerequisites

**For Local Docker:**
- Python 3.11+
- Docker & Docker Compose
- Poetry (install: `curl -sSL https://install.python-poetry.org | python3 -`)

**For Kubernetes:**
- Kubernetes cluster (Docker Desktop, minikube, or cloud)
- kubectl configured
- Docker for building images

## 🔧 Configuration

### 1. Clone and Setup

```bash
# Copy environment file
cp .env.example .env

# Edit .env and add your API keys:
# - GOOGLE_API_KEY and GOOGLE_SEARCH_ENGINE_ID
# - BING_API_KEY
# - Optionally: OKTA_DOMAIN, ENTRA_TENANT_ID, etc.
```

### 2. Choose Deployment Mode

#### Option A: Local Docker (Development)

```bash
# Install dependencies
./run.sh install

# Start all services (MongoDB, Redis, Jaeger, OTEL, Prometheus, Grafana)
./run.sh start

# Check services are running
./run.sh status
```

#### Option B: Kubernetes (Production)

```bash
# Deploy entire stack to K8s
DEPLOY_MODE=k8s ./run.sh start

# Check deployment status
DEPLOY_MODE=k8s ./run.sh status
```

### 3. Initialize Database

#### Local Docker Mode:
```bash
# Create admin user
./run.sh admin

# Login: admin / admin (change on first login)
```

#### Kubernetes Mode:
Admin user is created automatically during deployment.
- Username: `admin`
- Password: `admin` (change immediately)

### 4. Access the Application

#### Local Docker:
- **API**: http://localhost:8000/api/v1/
- **API Docs**: http://localhost:8000/docs
- **Dashboard**: Deploy separately (see admin-dashboard/README.md)

#### Kubernetes:
- **Dashboard**: http://localhost/
- **API**: http://localhost/api/v1/
- **Monitoring**: Use `k8s/port-forward.sh` for Grafana/Jaeger/Prometheus

### 5. Test the API

```bash
# Local mode
./run.sh test -q "OpenTelemetry" --pretty

# Kubernetes mode
DEPLOY_MODE=k8s ./run.sh test -q "OpenTelemetry" --pretty

# Manual curl test (Local)
curl -X POST http://localhost:8000/api/v1/search \
  -H "X-API-Key: YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"query": "artificial intelligence", "max_results": 5}'

# Manual curl test (Kubernetes)
curl -X POST http://localhost/api/v1/search \
  -H "X-API-Key: YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"query": "artificial intelligence", "max_results": 5}'
```

## 📚 Management Script (run.sh)

The `run.sh` script supports both local Docker and Kubernetes deployments:

```bash
# Local Docker (default)
./run.sh start          # Start all services
./run.sh stop           # Stop all services
./run.sh status         # Show status
./run.sh logs           # View logs
./run.sh test           # Test API
./run.sh health         # Health check

# Kubernetes
DEPLOY_MODE=k8s ./run.sh start     # Deploy to K8s
DEPLOY_MODE=k8s ./run.sh stop      # Stop K8s deployment
DEPLOY_MODE=k8s ./run.sh status    # K8s status
DEPLOY_MODE=k8s ./run.sh logs      # K8s logs
DEPLOY_MODE=k8s ./run.sh test      # Test K8s API
DEPLOY_MODE=k8s ./run.sh health    # K8s health check
```

**Local-only commands:**
```bash
./run.sh api            # Start API only (development)
./run.sh services       # Start MongoDB/Redis only
./run.sh admin          # Create admin user
./run.sh shell          # Open Poetry shell
./run.sh install        # Install dependencies
```

See `./run.sh help` or [DEPLOYMENT_MODES.md](DEPLOYMENT_MODES.md) for complete guide.

## 🏗️ Architecture

### Local Docker Mode
```
Browser
   ↓
localhost:8000 (API via Poetry/uvicorn)
   ↓
   ├─→ MongoDB (Docker, port 27017)
   ├─→ Redis (Docker, port 6379)
   ├─→ OTEL Collector → Jaeger/Prometheus
   └─→ Grafana (monitoring)
```

### Kubernetes Mode
```
Browser (localhost:80)
   ↓
nginx-ingress-controller
   ↓
   ├─→ /api/v1/* → websearch-api (2 replicas)
   └─→ /* → dashboard (2 replicas)
   
Internal Services:
   ├─→ MongoDB (StatefulSet)
   ├─→ Redis (Deployment)
   ├─→ OTEL Collector
   ├─→ Jaeger (distributed tracing)
   ├─→ Prometheus (metrics)
   └─→ Grafana (dashboards)
```

## 📖 API Documentation

### Local Docker Mode
Once running, visit:
- **API Docs (Swagger)**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **Jaeger UI**: http://localhost:16686 (distributed tracing)
- **Prometheus**: http://localhost:9090 (metrics)
- **Grafana**: http://localhost:3001 (dashboards, admin/admin)

### Kubernetes Mode
- **Dashboard**: http://localhost/
- **API Docs (Swagger)**: http://localhost/api/v1/docs
- **Monitoring**: Forward ports with `k8s/port-forward.sh`, then:
  - **Jaeger UI**: http://localhost:16686
  - **Prometheus**: http://localhost:9090
  - **Grafana**: http://localhost:3001

## 🔑 API Endpoints

### Health & Status
- `GET /api/v1/health` - Basic health check
- `GET /api/v1/ready` - Readiness check with dependency validation
- `GET /api/v1/search/providers` - Search provider status
- `POST /api/v1/search/providers/health-check` - Trigger provider health check

### Search
- `POST /api/v1/search` - Perform web search

**Request:**
```json
{
  "query": "your search query",
  "max_results": 10,
  "safe_search": true,
  "preferred_provider": "google"
}
```

**Response:**
```json
{
  "query": "your search query",
  "results": [...],
  "total_results": 10,
  "filtered_results": 2,
  "provider": "google",
  "response_time_ms": 234.5,
  "policies_applied": ["policy-001"],
  "rate_limit_info": {...},
  "quota_info": {...}
}
```

### Client Management
- `POST /api/v1/clients` - Create new API client
- `GET /api/v1/clients` - List all clients
- `GET /api/v1/clients/{id}` - Get client details
- `PATCH /api/v1/clients/{id}` - Update client
- `DELETE /api/v1/clients/{id}` - Delete client
- `POST /api/v1/clients/{id}/regenerate-key` - Regenerate API key

## 🏗️ Architecture

```
┌─────────────────┐
│   AI Agents     │
└────────┬────────┘
         │
         ▼
┌─────────────────────────────────────────┐
│  API Gateway + Auth Middleware          │
│  (OAuth/API Key/Client Cert)           │
└────────┬────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────┐
│  FastAPI Application                    │
│  ├─ Search Endpoint                     │
│  ├─ Policy Engine                       │
│  ├─ Rate Limiter                        │
│  └─ OTEL Instrumentation               │
└────┬────────────────────────┬───────────┘
     │                        │
     ▼                        ▼
┌──────────────┐      ┌─────────────────┐
│   MongoDB    │      │  Search Manager │
│  ├─ Policies │      │  ├─ Google API  │
│  ├─ Users    │      │  ├─ Bing API    │
│  ├─ Clients  │      │  └─ Fallback    │
│  └─ Logs     │      └─────────────────┘
└──────────────┘
```

## ⚙️ Configuration

Key environment variables in `.env`:

### Required
```bash
GOOGLE_API_KEY=your_key
GOOGLE_SEARCH_ENGINE_ID=your_engine_id
BING_API_KEY=your_key
```

### Optional
```bash
# OAuth
OKTA_DOMAIN=your-domain.okta.com
ENTRA_TENANT_ID=your_tenant_id

# Rate Limiting
RATE_LIMIT_PER_MINUTE=60
RATE_LIMIT_BURST=10

# Search
SEARCH_CACHE_TTL_SECONDS=3600
SEARCH_MAX_RESULTS=100
SEARCH_TIMEOUT_SECONDS=10
```

## 🛡️ Security Features

### Authentication Methods
1. **API Keys**: Hash-based, secure storage
2. **OAuth 2.0**: Okta and Microsoft Entra ID support
3. **Client Certificates**: mTLS support (future)

### Authorization
- Role-Based Access Control (RBAC)
- Three roles: Admin, User, Agent
- Granular permissions system

### Policy Enforcement
- Content filtering by keywords
- Domain allowlist/blocklist
- Parental controls
- Safe search enforcement
- Per-user policy inheritance

### Rate Limiting & Quotas
- 60 requests/minute (default)
- Configurable daily/monthly quotas
- Distributed rate limiting with Redis
- Proper HTTP 429 responses

## 📊 Observability

### OpenTelemetry Integration
- Distributed tracing across all operations
- Custom spans for critical paths
- Request/response metadata capture
- Exception tracking

### Metrics
- Request count, latency, errors
- Provider health and response times
- Cache hit rates
- Quota usage

### Logging
- Structured logging with loguru
- Request/response logging
- Error tracking with stack traces
- Audit trail for compliance

## 🧪 Development

```bash
# Run tests
poetry run pytest

# Format code
poetry run black src/ tests/

# Lint
poetry run ruff check src/ tests/

# Type check
poetry run mypy src/

# Coverage
poetry run pytest --cov=src --cov-report=html
```

## 📦 Project Structure

```
websearch-api/
├── src/
│   ├── api/
│   │   └── routes/          # API endpoints
│   ├── core/                # Core configuration
│   ├── middleware/          # Auth, logging, tracing
│   ├── models/              # Data models
│   ├── services/            # Business logic
│   └── utils/               # Utilities
├── tests/                   # Test suite
├── scripts/                 # Utility scripts
├── docker-compose.yml       # Service orchestration
└── pyproject.toml          # Dependencies

```

## 🎯 Implementation Status

- ✅ **Phase 1**: Core Infrastructure (100%)
- ✅ **Phase 2**: Authentication (71% - mTLS and tests pending)
- ✅ **Phase 3**: OpenTelemetry (100%)
- ✅ **Phase 4**: Search Providers (100%)
- ✅ **Phase 5**: Policy Engine (100%)
- ✅ **Phase 6**: Rate Limiting (100%)
- ✅ **Phase 7**: Core Search API (100%)
- ⏳ **Phase 8**: Dashboard Backend (0%)
- ⏳ **Phase 9**: Frontend (0%)
- ⏳ **Phase 10-12**: Security, Testing, Deployment (0%)

**Overall Progress: 58.4%** (45/77 tasks complete)

## 🚧 Coming Soon

- Admin dashboard (React)
- Advanced analytics
- Result caching
- mTLS authentication
- Kubernetes deployment
- CI/CD pipeline

## 📝 License

MIT License - See LICENSE file for details

## 🤝 Contributing

Contributions welcome! Please read contributing guidelines first.

## 📧 Support

For issues and questions, please open a GitHub issue.

