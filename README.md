# WebSearch API for AI Agents

Enterprise-grade web search API designed for AI agents with comprehensive security, observability, and policy enforcement.

## 🎯 Features

- 🔐 **Multi-Auth Support**: OAuth (Okta, Entra ID), API Keys, Client Certificates
- 📊 **Full Observability**: OpenTelemetry with distributed tracing (Jaeger, Prometheus)
- 🛡️ **Enterprise Guardrails**: Content filtering, parental controls, domain policies
- 🚦 **Rate Limiting**: Distributed throttling with Redis (60 req/min default)
- 🔄 **Provider Fallback**: Multi-provider search (Google, Bing) with automatic failover
- 📈 **Admin Dashboard**: React-based UI for policy and user management (Coming Soon)
- 🔍 **Audit Logging**: Complete audit trail for compliance
- ⚡ **High Performance**: Async operations, caching, connection pooling

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- Docker & Docker Compose
- Poetry (install: `curl -sSL https://install.python-poetry.org | python3 -`)

### 1. Clone and Setup

```bash
# Install dependencies
poetry install

# Copy environment file
cp .env.example .env

# Edit .env and add your API keys:
# - GOOGLE_API_KEY and GOOGLE_SEARCH_ENGINE_ID
# - BING_API_KEY
# - Optionally: OKTA_DOMAIN, ENTRA_TENANT_ID, etc.
```

### 2. Start Services

```bash
# Start all services (MongoDB, Redis, Jaeger, OTEL, Prometheus, Grafana)
docker-compose up -d

# Check services are running
docker-compose ps
```

### 3. Initialize Database

```bash
# Create admin user and API key
poetry run python scripts/create_admin.py

# Save the API key that's printed!
```

### 4. Run the API

```bash
# Development mode with auto-reload
poetry run uvicorn src.main:app --reload --host 0.0.0.0 --port 8000

# Or using Docker
docker-compose up api
```

### 5. Test the API

```bash
# Health check
curl http://localhost:8000/api/v1/health

# Search (replace YOUR_API_KEY)
curl -X POST http://localhost:8000/api/v1/search \
  -H "X-API-Key: YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"query": "artificial intelligence", "max_results": 5}'
```

## 📚 API Documentation

Once running, visit:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **Jaeger UI**: http://localhost:16686 (distributed tracing)
- **Prometheus**: http://localhost:9090 (metrics)
- **Grafana**: http://localhost:3001 (dashboards, admin/admin)

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

