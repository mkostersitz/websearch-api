# WebSearch API for AI Agents

Enterprise-grade web search API designed for AI agents with comprehensive security, observability, and policy enforcement.

## Features

- 🔐 **Multi-Auth Support**: OAuth (Okta, Entra ID), API Keys, Client Certificates
- 📊 **Full Observability**: OpenTelemetry integration with distributed tracing
- 🛡️ **Enterprise Guardrails**: Content filtering, parental controls, domain policies
- 🚦 **Rate Limiting**: Distributed throttling with Redis
- 🔄 **Provider Fallback**: Multi-provider search (Google, Bing) with automatic failover
- 📈 **Admin Dashboard**: React-based UI for policy and user management
- 🔍 **Audit Logging**: Complete audit trail for compliance

## Quick Start

### Prerequisites

- Python 3.11+
- Docker & Docker Compose
- Poetry (for dependency management)

### Installation

```bash
# Install dependencies
poetry install

# Start services with Docker Compose
docker-compose up -d

# Run the API
poetry run uvicorn src.main:app --reload
```

### Configuration

Copy `.env.example` to `.env` and configure:

```bash
cp .env.example .env
```

Required environment variables:
- `MONGODB_URL`: MongoDB connection string
- `REDIS_URL`: Redis connection string
- `GOOGLE_API_KEY`: Google Custom Search API key
- `BING_API_KEY`: Bing Search API key
- `OKTA_DOMAIN`: Okta domain for OAuth
- `ENTRA_TENANT_ID`: Microsoft Entra ID tenant

## Architecture

```
API Gateway → FastAPI App → Search Providers
                ↓
        MongoDB + Redis + OTEL
```

## Development

```bash
# Run tests
poetry run pytest

# Format code
poetry run black src/ tests/

# Lint
poetry run ruff check src/ tests/

# Type check
poetry run mypy src/
```

## API Documentation

Once running, visit:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## License

MIT License - See LICENSE file for details
