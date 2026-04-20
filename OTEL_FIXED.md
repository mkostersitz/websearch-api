# OpenTelemetry Integration - FIXED ✅

**Status:** ✅ **WORKING**  
**Date Fixed:** 2026-04-16  
**Service in Jaeger:** `websearch-api` ✓

## Problem Summary

The `websearch-api` service was not appearing in Jaeger traces despite having OpenTelemetry dependencies installed.

### Root Causes Identified

1. **OTEL Endpoint Misconfiguration** ✅ Fixed
   - **Issue:** `.env` had `OTEL_EXPORTER_OTLP_ENDPOINT=http://otel-collector:4317`
   - **Problem:** Docker hostname won't work for local processes
   - **Fix:** Changed to `http://localhost:5317`

2. **setuptools Version Incompatibility** ✅ Fixed
   - **Issue:** setuptools 82.0.1 removed `pkg_resources` module
   - **Problem:** OpenTelemetry instrumentation packages still import `pkg_resources`
   - **Error:** `ModuleNotFoundError: No module named 'pkg_resources'`
   - **Fix:** Downgraded setuptools from `82.0.1` → `69.5.1`

3. **Python Version** ✅ Already Correct
   - **Using:** Python 3.12.13 (via Poetry virtual environment)
   - **Note:** System Python is 3.14.4, but Poetry correctly uses 3.12.13
   - **Status:** Perfect for OpenTelemetry compatibility

## The Fix

```bash
cd /Users/mikek/repos/websearch-api

# 1. Fix OTEL endpoint in .env
sed -i.bak 's|OTEL_EXPORTER_OTLP_ENDPOINT=http://otel-collector:4317|OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:5317|g' .env

# 2. Downgrade setuptools to restore pkg_resources
poetry remove setuptools
poetry add "setuptools<70"

# 3. Restart API
./run.sh stop
./run.sh api
```

## Verification

### Check Jaeger Services
```bash
curl http://localhost:17686/api/services | jq '.data[]'
```

**Expected Output:**
```json
"jaeger-all-in-one"
"websearch-api"     ← Should now appear!
```

### Check Traces
```bash
curl "http://localhost:17686/api/traces?service=websearch-api&limit=10" | jq '.data | length'
```

Should return number > 0

### View in Jaeger UI
- Open: http://localhost:17686
- Select Service: `websearch-api`
- Click "Find Traces"

You should see traces for:
- `GET /docs`
- `GET /openapi.json`
- `POST /api/v1/search`
- HTTP receive/send operations

## Current Status

✅ **OpenTelemetry Configured**
```
INFO | FastAPI app instrumented with OpenTelemetry
INFO | OpenTelemetry configured - Service: websearch-api
```

✅ **Traces Being Exported**
- Service appears in Jaeger
- Traces visible for all HTTP requests
- Auto-instrumentation working

✅ **All OTEL Services Running**
- Jaeger UI: http://localhost:17686
- Prometheus: http://localhost:9091
- Grafana: http://localhost:3002
- OTEL Collector: Receiving on port 5317

## Package Versions (Working Configuration)

```
Python: 3.12.13
setuptools: 69.5.1 (downgraded from 82.0.1)
opentelemetry-api: 1.22.0
opentelemetry-sdk: 1.22.0
opentelemetry-instrumentation-fastapi: 0.43b0
opentelemetry-exporter-otlp-proto-grpc: 1.22.0
protobuf: 4.25.9
grpcio: 1.80.0
```

## Important Notes

1. **pkg_resources Deprecation**
   - `pkg_resources` is deprecated in setuptools 68+
   - Completely removed in setuptools 82+
   - OpenTelemetry packages still depend on it
   - Solution: Pin setuptools to `<70` until OTEL packages migrate

2. **Python Version Management**
   - Poetry virtual environment uses Python 3.12.13 ✓
   - System Python is 3.14.4 (NOT used by Poetry)
   - This is the correct setup!

3. **OTEL Endpoint**
   - Local API → `http://localhost:5317` (gRPC)
   - Docker containers → `http://otel-collector:4317` (different network)

## Troubleshooting

### If traces stop appearing:

1. **Check OTEL Collector is running:**
   ```bash
   docker ps | grep otel-collector
   ```

2. **Verify endpoint configuration:**
   ```bash
   grep OTEL_EXPORTER_OTLP_ENDPOINT .env
   # Should be: http://localhost:5317
   ```

3. **Check API logs for OTEL warnings:**
   ```bash
   ./run.sh api
   # Should see: "OpenTelemetry configured - Service: websearch-api"
   ```

4. **Verify setuptools version:**
   ```bash
   poetry show setuptools
   # Should be: 69.5.1 (or < 70)
   ```

## Next Steps

1. ✅ OTEL integration working
2. ✅ Traces visible in Jaeger
3. ⏭️ Configure Grafana dashboards for metrics
4. ⏭️ Set up alerts in Prometheus
5. ⏭️ Add custom spans for detailed tracing

## References

- Jaeger UI: http://localhost:17686
- API Docs: http://localhost:8000/docs
- OTEL Docs: https://opentelemetry.io/docs/python/
