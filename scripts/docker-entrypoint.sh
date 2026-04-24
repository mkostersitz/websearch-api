#!/bin/sh
set -e

echo "Running database migrations..."
python /app/scripts/migrate_client_roles.py

echo "Starting application..."
exec uvicorn src.main:app --host 0.0.0.0 --port 8000
