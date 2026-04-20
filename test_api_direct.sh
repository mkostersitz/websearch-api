#!/bin/bash
cd /Users/mikek/repos/websearch-api
export PYTHONPATH=/Users/mikek/repos/websearch-api
poetry run uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload &
PID=$!
echo "Started API with PID: $PID"
sleep 10

echo "Testing API..."
curl -s http://localhost:8000/api/v1/health | python3 -m json.tool

echo ""
echo "API is running at http://localhost:8000"
echo "To stop: kill $PID"
