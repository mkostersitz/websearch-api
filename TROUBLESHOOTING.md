# Troubleshooting Guide

## Python 3.14 Compatibility

### OpenTelemetry Disabled
**Symptom**: "OpenTelemetry not available" in logs

**Cause**: Python 3.14 protobuf compatibility issue

**Impact**: API works normally, but distributed tracing/metrics disabled

**Fix** (if you need OTEL):
- Use Python 3.11 or 3.12
- Or wait for protobuf update

## Common Issues

### Dependencies Not Installed
```bash
poetry install
```

### MongoDB Connection Failed
```bash
docker-compose up -d mongodb
sleep 10
docker-compose ps
```

### Redis Connection Failed  
```bash
docker-compose up -d redis
```

### Port 8000 In Use
```bash
# Use different port
poetry run uvicorn src.main:app --port 8001
```

## Reset Everything
```bash
docker-compose down -v
poetry env remove python
poetry install
docker-compose up -d mongodb redis
poetry run python scripts/create_admin.py
```
