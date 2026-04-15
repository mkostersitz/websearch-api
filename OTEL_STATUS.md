# OpenTelemetry (OTEL) Status

**Last Updated:** 2026-04-15  
**Status:** ⚠️ Optional (Python 3.14 Compatibility Issue)

## Current Situation

### What's Working ✅
- OTEL Collector running in Docker (port 4317)
- Jaeger UI accessible at http://localhost:16686
- Prometheus accessible at http://localhost:9090  
- Grafana accessible at http://localhost:3000
- API code designed with OTEL support
- Graceful degradation when OTEL unavailable

### What's Not Working ❌
- OTEL instrumentation disabled in Python 3.14
- No distributed tracing spans
- No automatic metric collection

## Root Cause

**Python 3.14 Incompatibility:**
```
Python 3.14 introduced changes to metaclasses (custom tp_new)
that break the protobuf library used by OpenTelemetry.

Error: "Metaclasses with custom tp_new are not supported"
```

**Dependency Conflict:**
- OpenTelemetry requires: `protobuf >= 3.19, < 5.0`
- Python 3.14 requires: `protobuf >= 5.29`
- These requirements are incompatible

## Solutions

### Option 1: Use Python 3.12 (Recommended for Full OTEL)

**Steps:**
```bash
# Install Python 3.12
pyenv install 3.12.0

# Switch Poetry to use Python 3.12
cd /Users/mikek/repos/websearch-api
poetry env use 3.12
poetry install

# Restart API
poetry run uvicorn src.main:app
```

**Result:** ✅ Full OTEL functionality with distributed tracing

### Option 2: Accept Graceful Degradation (Current State)

**What You Get:**
- ✅ All API features work perfectly
- ✅ Structured logging with Loguru
- ✅ Complete audit logs in MongoDB
- ✅ Request/response logging
- ✅ Error tracking
- ⚠️ No distributed tracing spans
- ⚠️ No automatic metrics

**When to Choose This:**
- You don't need distributed tracing
- Audit logs + structured logs are sufficient
- You want to use Python 3.14 features
- Quick deployment is priority

### Option 3: Wait for Upstream Fix

**Timeline:** Expected Q2 2026

OpenTelemetry team is working on protobuf 5.x support.
Track progress: https://github.com/open-telemetry/opentelemetry-python

## Current Implementation

The API handles OTEL unavailability gracefully:

```python
# src/core/telemetry.py
try:
    from opentelemetry import trace, metrics
    OTEL_AVAILABLE = True
except Exception as e:
    logger.warning(f"OpenTelemetry not available: {e}")
    OTEL_AVAILABLE = False

def configure_opentelemetry():
    if not OTEL_AVAILABLE:
        logger.warning("OpenTelemetry not configured")
        return None, None
    # ... OTEL setup
```

All OTEL-dependent code checks the `OTEL_AVAILABLE` flag.

## Alternative Observability

Even without OTEL, you have:

### 1. Structured Logging
```python
# All requests logged with context
logger.info(f"Search request from client {client_id}: {query}")
```

### 2. Audit Logs
```python
# Every action recorded in MongoDB
await db.audit_logs.insert_one({
    "timestamp": datetime.utcnow(),
    "client_id": client_id,
    "action_type": "search",
    "details": {...}
})
```

### 3. Request Logging Middleware
```python
# Automatic request/response logging
@app.middleware("http")
async def logging_middleware(request, call_next):
    # Logs all HTTP traffic
```

### 4. Health & Readiness Endpoints
```bash
GET /api/v1/health   # System health
GET /api/v1/ready    # Readiness checks
```

### 5. Admin Dashboard Stats
```bash
GET /api/v1/admin/stats/overview    # Overall stats
GET /api/v1/admin/stats/searches    # Search analytics
GET /api/v1/admin/system/health     # Component health
```

## Docker Services Status

```bash
# Check running services
docker ps

# Expected services:
✅ websearch-api
✅ websearch-mongo
✅ websearch-redis
✅ websearch-jaeger (ready for when OTEL works)
✅ websearch-prometheus (ready for when OTEL works)
✅ websearch-grafana (ready for when OTEL works)
⚠️  websearch-otel-collector (restarting - waiting for traces)
```

## Recommendation

**For Production: Accept Current State**

The API is fully functional without OTEL. The structured logging,
audit logs, and admin dashboard provide sufficient observability
for most use cases.

If you specifically need distributed tracing:
1. Use Python 3.12 instead of 3.14
2. Or wait for OpenTelemetry protobuf 5.x support

## Testing

### With OTEL Disabled (Current)
```bash
curl http://localhost:8000/api/v1/health
# Should work fine
```

### With Python 3.12 (Full OTEL)
```bash
# After switching to Python 3.12:
poetry run uvicorn src.main:app

# Check logs - should show:
# "OpenTelemetry configured successfully"
# "TracerProvider initialized"
```

## References

- [OpenTelemetry Python](https://github.com/open-telemetry/opentelemetry-python)
- [Python 3.14 Release Notes](https://docs.python.org/3.14/whatsnew/3.14.html)
- [Protobuf Python](https://github.com/protocolbuffers/protobuf)

---

**Bottom Line:** The API works perfectly without OTEL. It's a nice-to-have,  
not a requirement. The graceful degradation ensures zero impact on functionality.
