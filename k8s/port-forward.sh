#!/bin/bash

# ⚠️  DEPRECATED - Port forwarding is no longer needed!
# 
# With nginx-ingress-controller installed, services are accessible at:
#   Dashboard:  http://localhost/
#   API:        http://localhost/api/v1/
#
# This script is kept for backward compatibility and monitoring services only.
# 
# To access monitoring services, use these individual commands:
#   kubectl port-forward -n websearch-api svc/grafana 3001:3000
#   kubectl port-forward -n websearch-api svc/prometheus 9090:9090
#   kubectl port-forward -n websearch-api svc/jaeger 16686:16686

echo "╔════════════════════════════════════════════════════════════════╗"
echo "║                    ⚠️  SCRIPT DEPRECATED                       ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""
echo "Port-forwarding is NO LONGER NEEDED for the dashboard and API!"
echo ""
echo "📍 Access via Ingress (no port-forward required):"
echo ""
echo "  Dashboard:  http://localhost/"
echo "  API:        http://localhost/api/v1/"
echo ""
echo "This script now only forwards MONITORING services."
echo ""
read -p "Do you want to forward monitoring services? (y/N) " -n 1 -r
echo ""

if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Cancelled."
    exit 0
fi

echo ""
echo "=== Starting Port Forwards for Monitoring ==="
echo "Press Ctrl+C to stop all forwards"
echo ""

# Function to cleanup on exit
cleanup() {
    echo ""
    echo "=== Stopping Port Forwards ==="
    jobs -p | xargs -r kill 2>/dev/null
    exit 0
}

trap cleanup SIGINT SIGTERM

# Start port forwards for monitoring only
echo "Starting Grafana on localhost:3001..."
kubectl port-forward svc/grafana 3001:3000 -n websearch-api &

echo "Starting Prometheus on localhost:9090..."
kubectl port-forward svc/prometheus 9090:9090 -n websearch-api &

echo "Starting Jaeger on localhost:16686..."
kubectl port-forward svc/jaeger 16686:16686 -n websearch-api &

echo ""
echo "=== Port Forwards Active for Monitoring ==="
echo ""
echo "  Grafana:    http://localhost:3001 (admin/admin)"
echo "  Prometheus: http://localhost:9090"
echo "  Jaeger:     http://localhost:16686"
echo ""
echo "📍 Remember - Dashboard and API are available WITHOUT port-forward:"
echo ""
echo "  Dashboard:  http://localhost/"
echo "  API:        http://localhost/api/v1/"
echo ""
echo "Press Ctrl+C to stop all forwards"
echo ""

# Wait for all background jobs
wait

