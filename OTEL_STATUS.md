# OpenTelemetry Integration Status

**Last Updated:** 2026-04-16  
**Status:** ⚠️ DISABLED (Python 3.14 Compatibility Issue)

## Current Situation

### What's Working
✅ API is fully functional  
✅ All search endpoints working  
✅ Rate limiting and quotas operational  
✅ MongoDB and Redis connections healthy  

### What's Not Working
❌ OpenTelemetry automatic instrumentation disabled  
❌ No traces being sent to Jaeger  
❌ No metrics being exported to Prometheus  

## Root Cause

### Issue #1: OTEL Endpoint Configuration ✅ FIXED
- **Problem:** `.env` file had `OTEL_EXPORTER_OTLP_ENDPOINT=http://otel-collector:4317`
- **Solution:** Changed to `http://localhost:5317` (correct for local OTEL collector)
- **Status:** ✅ Fixed

### Issue #2: Python 3.14 Compatibility ⚠️ BLOCKING
- **Problem:** Python 3.14.4 is too new for current OpenTelemetry packages
- **Error:** `"Metaclasses with custom tp_new are not supported"`
- **Cause:** Incompatibility between Python 3.14, protobuf, and gRPC libraries
- **Status:** ⚠️ Waiting for library updates

#### Technical Details
```
Python version: 3.14.4
Protobuf required: <6.0 (by OTEL packages)
Protobuf available: >=6.31.1 (with latest gRPC)
Result: Version conflict preventing OTEL instrumentation
```

## Services in Jaeger

Currently visible:
- ✅ `jaeger-all-in-one` (Jaeger itself)
- ✅ `test-service` (from test script using compatible Python/libraries)
- ❌ `websearch-api` (NOT visible - OTEL disabled due to compatibility)

## Workaround Options

### Option 1: Use Python 3.11 or 3.12 (RECOMMENDED)

```bash
# Install Python 3.12
brew install python@3.12

# Configure Poetry to use Python 3.12
cd /Users/mikek/repos/websearch-api
poetry env use python3.12

# Reinstall dependencies
poetry install

# Restart API
./run.sh stop
./run.sh api
```

This will enable full OpenTelemetry instrumentation.

### Option 2: Wait for Library Updates

Monitor these packages for Python 3.14 support:
- `opentelemetry-exporter-otlp-proto-grpc`
- `grpcio`
- `protobuf`

Check: https://github.com/open-telemetry/opentelemetry-python

### Option 3: Manual Instrumentation (Advanced)

Add manual trace context without auto-instrumentation:

```python
# Workaround for Python 3.14
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import ConsoleSpanExporter, SimpleSpanProcessor

# Manual setup without gRPC exporter
provider = TracerProvider()
processor = SimpleSpanProcessor(ConsoleSpanExporter())
provider.add_span_processor(processor)
trace.set_tracer_provider(provider)
```

## Current Logs

API startup shows:
```
WARNING  | src.core.telemetry:<module>:24 - OpenTelemetry not available: Metaclasses with custom tp_new are not supported.
WARNING  | src.core.telemetry:instrument_app:98 - Skipping OpenTelemetry instrumentation - not available
WARNING  | src.core.telemetry:configure_opentelemetry:38 | OpenTelemetry not configured - tracing and metrics disabled
```

## Verification

### Check Current Status
```bash
# View API logs
tail -f /tmp/api_fixed.log | grep -i "otel\|telemetry"

# Check Jaeger services
curl http://localhost:17686/api/services | jq '.data[]'

# Test API
./run.sh test --pretty
```

### Expected After Fix
Once Python version is corrected, you should see:
```
INFO | OpenTelemetry configured - Service: websearch-api
INFO | FastAPI app instrumented with OpenTelemetry
```

And in Jaeger:
```json
{
  "data": [
    "jaeger-all-in-one",
    "test-service",
    "websearch-api"  ← This will appear
  ]
}
```

## Recommended Action

**Switch to Python 3.12** for full OTEL support:

```bash
cd /Users/mikek/repos/websearch-api
poetry env use $(which python3.12)
poetry install
./run.sh stop
./run.sh api
```

Then verify:
```bash
./run.sh test --pretty
curl http://localhost:17686/api/services | jq '.data[]'
```

You should then see `websearch-api` traces in Jaeger at http://localhost:17686

## Notes

- The API is fully functional even without OTEL
- OTEL is for observability/monitoring only
- "test-service" appears because the test script uses system Python (not 3.14)
- This is a temporary issue until libraries catch up with Python 3.14
