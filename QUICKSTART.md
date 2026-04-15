# 🚀 Quick Start Guide

Get your WebSearch API running in 5 minutes!

## Prerequisites Check

```bash
# Check Python version (need 3.11+)
python3 --version

# Check Docker
docker --version
docker-compose --version

# Install Poetry if needed
curl -sSL https://install.python-poetry.org | python3 -
```

## Step-by-Step Setup

### 1. Install Dependencies

```bash
cd /Users/mikek/repos/websearch-api

# Install Python dependencies
poetry install

# This installs:
# - FastAPI, uvicorn
# - MongoDB driver (motor)
# - Redis client
# - OpenTelemetry SDK
# - Authentication libs (jose, passlib)
# - And more...
```

### 2. Get API Keys

You'll need at least one search provider API key:

**Option A: Google Custom Search (Recommended)**
1. Go to https://console.cloud.google.com/
2. Enable Custom Search API
3. Create API key
4. Create Custom Search Engine at https://programmablesearchengine.google.com/
5. Note the Search Engine ID

**Option B: Bing Search API**
1. Go to https://portal.azure.com/
2. Create Bing Search v7 resource
3. Copy the API key

### 3. Configure Environment

```bash
# Copy the example
cp .env.example .env

# Edit .env and add your keys
nano .env  # or use your favorite editor

# Required settings:
GOOGLE_API_KEY=your_google_api_key_here
GOOGLE_SEARCH_ENGINE_ID=your_engine_id_here
# OR
BING_API_KEY=your_bing_api_key_here
```

### 4. Start Services

```bash
# Start all infrastructure services
docker-compose up -d

# Wait a moment for services to be ready (about 10 seconds)
sleep 10

# Check services are running
docker-compose ps

# You should see:
# - websearch-mongodb
# - websearch-redis
# - websearch-jaeger
# - websearch-otel-collector
# - websearch-prometheus
# - websearch-grafana
```

### 5. Initialize Database

```bash
# Create admin user and get API key
poetry run python scripts/create_admin.py

# ⚠️ IMPORTANT: Copy the API key that's displayed!
# You'll need it for all API requests.
```

### 6. Start the API

**Option A: Development mode (with auto-reload)**
```bash
poetry run uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

**Option B: Using Docker**
```bash
# Build and run
docker-compose up api
```

### 7. Verify It's Working

```bash
# Health check (no auth required)
curl http://localhost:8000/api/v1/health

# Should return:
# {"status":"healthy","version":"0.1.0","timestamp":"...","environment":"development"}

# Run smoke tests
poetry run python tests/smoke_test.py
```

### 8. Make Your First Search!

```bash
# Replace YOUR_API_KEY with the key from step 5
export API_KEY="YOUR_API_KEY_HERE"

# Search for AI-related content
curl -X POST http://localhost:8000/api/v1/search \
  -H "X-API-Key: $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "artificial intelligence latest developments",
    "max_results": 5,
    "safe_search": true
  }'

# You should get JSON with search results!
```

## 🎉 Success! What's Next?

### Explore the API Documentation
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### Check Out the Observability Stack
- **Jaeger (Traces)**: http://localhost:16686
- **Prometheus (Metrics)**: http://localhost:9090
- **Grafana (Dashboards)**: http://localhost:3001
  - Username: `admin`
  - Password: `admin`

### Try More Features

**Create a new client:**
```bash
curl -X POST http://localhost:8000/api/v1/clients \
  -H "X-API-Key: $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "client_name": "My AI Agent",
    "client_type": "api_key",
    "quota_per_day": 1000,
    "quota_per_month": 30000
  }'
```

**Check provider status:**
```bash
curl -H "X-API-Key: $API_KEY" \
  http://localhost:8000/api/v1/search/providers
```

**List your clients:**
```bash
curl -H "X-API-Key: $API_KEY" \
  http://localhost:8000/api/v1/clients
```

## 🐛 Troubleshooting

### MongoDB Connection Failed
```bash
# Check MongoDB is running
docker-compose ps mongodb

# Check logs
docker-compose logs mongodb

# Restart if needed
docker-compose restart mongodb
```

### Redis Connection Failed
```bash
# Check Redis is running
docker-compose ps redis

# Test connection
docker-compose exec redis redis-cli ping
# Should return: PONG
```

### API Key Not Working
```bash
# Create a new admin client
poetry run python scripts/create_admin.py

# The script will show if admin already exists
# API keys are only shown once during creation
```

### Search Returns No Results
```bash
# Check your API keys are set correctly in .env
cat .env | grep API_KEY

# Test provider health
curl -X POST http://localhost:8000/api/v1/search/providers/health-check \
  -H "X-API-Key: $API_KEY"

# Check application logs
docker-compose logs api
```

### Port Already in Use
```bash
# Change ports in docker-compose.yml or .env
# Common conflicts: 8000 (API), 27017 (MongoDB), 6379 (Redis)

# Example: Change API port to 8080
# Edit docker-compose.yml:
# ports:
#   - "8080:8000"
```

## 📚 Next Steps

1. **Read the full README**: `README.md`
2. **Check implementation summary**: `IMPLEMENTATION_SUMMARY.md`
3. **Review the code**: Start with `src/main.py`
4. **Set up OAuth**: Configure Okta or Entra ID (optional)
5. **Create policies**: Use MongoDB to add search policies
6. **Monitor traces**: Open Jaeger to see request traces
7. **Build your AI agent**: Integrate the search API!

## 🎯 Common Use Cases

### For AI Agent Development
```python
import httpx

async def search_web(query: str, api_key: str):
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:8000/api/v1/search",
            headers={"X-API-Key": api_key},
            json={
                "query": query,
                "max_results": 10,
                "safe_search": True
            }
        )
        return response.json()

# Use it
results = await search_web("machine learning", "your-api-key")
print(f"Found {results['total_results']} results")
for result in results['results']:
    print(f"- {result['title']}: {result['url']}")
```

### For Production Deployment
```bash
# 1. Set environment to production in .env
ENVIRONMENT=production
DEBUG=false

# 2. Use proper secrets management
# Don't put real API keys in .env!

# 3. Set strong JWT secret
JWT_SECRET_KEY=$(openssl rand -hex 32)

# 4. Configure proper CORS origins
CORS_ORIGINS=["https://yourdomain.com"]

# 5. Use managed services
MONGODB_URL=mongodb+srv://user:pass@your-cluster.mongodb.net
REDIS_URL=redis://your-redis-instance:6379

# 6. Deploy with Kubernetes (coming soon)
```

## 💡 Tips

- **Rate Limits**: Default is 60 requests/minute. Adjust in .env
- **Quotas**: Default is 1000/day, 30000/month per client
- **Caching**: Results are cached for 1 hour by default
- **Policies**: Create in MongoDB to filter content
- **Tracing**: All requests are traced in Jaeger
- **Logs**: Check `logs/` directory for application logs

## 🆘 Need Help?

1. Check logs: `docker-compose logs -f api`
2. Run smoke tests: `poetry run python tests/smoke_test.py`
3. Review documentation: http://localhost:8000/docs
4. Check this guide again!

---

**You're all set! Happy searching! 🔍**
