#!/bin/bash

# Start WebSearch API
cd "$(dirname "$0")/.."

echo "🚀 Starting WebSearch API..."
echo "Environment: development"
echo "Port: 8000"
echo ""

# Start services if not running
docker-compose ps mongodb | grep -q "Up" || {
    echo "Starting Docker services..."
    docker-compose up -d mongodb redis jaeger otel-collector
    echo "Waiting for services to be ready..."
    sleep 10
}

echo "Starting API server..."
poetry run uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload
