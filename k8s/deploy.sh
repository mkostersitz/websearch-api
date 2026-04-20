#!/bin/bash

# Build and deploy WebSearch API to Kubernetes
set -e

# Get the directory where the script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
# Get the repo root (parent of k8s directory)
REPO_ROOT="$( cd "$SCRIPT_DIR/.." && pwd )"

echo "=== Building Docker Images ==="
echo "Repository root: $REPO_ROOT"

# Change to repo root for building
cd "$REPO_ROOT"

# Build API image
echo "Building API image..."
docker build -t websearch-api:latest -f Dockerfile .

# Build Dashboard image
echo "Building Dashboard image..."
docker build -t websearch-dashboard:latest -f Dockerfile.dashboard .

echo ""
echo "=== Deploying to Kubernetes ==="

# Change back to k8s directory for deployments
cd "$SCRIPT_DIR"

# Create namespace
echo "Creating namespace..."
kubectl apply -f base/namespace.yaml

# Apply ConfigMaps
echo "Applying ConfigMaps..."
kubectl apply -f base/configmap.yaml

# Deploy data layer
echo "Deploying MongoDB..."
kubectl apply -f base/mongodb.yaml

echo "Deploying Redis..."
kubectl apply -f base/redis.yaml

# Wait for data layer
echo "Waiting for data layer to be ready..."
kubectl wait --for=condition=ready pod -l app=mongodb -n websearch-api --timeout=120s || echo "MongoDB not ready yet, continuing..."
kubectl wait --for=condition=ready pod -l app=redis -n websearch-api --timeout=60s || echo "Redis not ready yet, continuing..."

# Deploy monitoring stack
echo "Deploying OTEL Collector..."
kubectl apply -f base/otel-collector.yaml

echo "Deploying Prometheus..."
kubectl apply -f base/prometheus.yaml

echo "Deploying Jaeger..."
kubectl apply -f base/jaeger.yaml

echo "Deploying Grafana..."
kubectl apply -f base/grafana.yaml

# Deploy application
echo "Deploying API..."
kubectl apply -f base/api-deployment.yaml

echo "Deploying Dashboard..."
kubectl apply -f base/dashboard-deployment.yaml

# Deploy ingress
echo "Deploying Ingress..."
kubectl apply -f base/ingress.yaml

# Install nginx-ingress-controller if not already installed
if ! kubectl get namespace ingress-nginx &> /dev/null; then
  echo "Installing nginx-ingress-controller..."
  kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/controller-v1.11.1/deploy/static/provider/cloud/deploy.yaml
  echo "Waiting for ingress controller..."
  kubectl wait --namespace ingress-nginx \
    --for=condition=ready pod \
    --selector=app.kubernetes.io/component=controller \
    --timeout=120s || echo "Ingress controller not ready yet"
else
  echo "nginx-ingress-controller already installed"
fi

echo ""
echo "=== Waiting for deployments ==="
kubectl wait --for=condition=available deployment/websearch-api -n websearch-api --timeout=180s || echo "API not ready yet"
kubectl wait --for=condition=available deployment/dashboard -n websearch-api --timeout=120s || echo "Dashboard not ready yet"
kubectl wait --for=condition=available deployment/grafana -n websearch-api --timeout=120s || echo "Grafana not ready yet"
kubectl wait --for=condition=available deployment/prometheus -n websearch-api --timeout=120s || echo "Prometheus not ready yet"

echo ""
echo "=== Deployment Complete! ==="
echo ""
echo "╔════════════════════════════════════════════════════════════════╗"
echo "║            🎉 WebSearch API Successfully Deployed!            ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""
echo "📍 ACCESS URLS (via Ingress - No Port-Forwarding Needed!):"
echo ""
echo "  Dashboard:  http://localhost/"
echo "  API:        http://localhost/api/v1/"
echo "  Health:     http://localhost/api/v1/health"
echo ""
echo "  Login: admin / admin (change password on first login)"
echo ""
echo "📊 MONITORING (requires port-forward):"
echo ""
echo "  Grafana:    kubectl port-forward -n websearch-api svc/grafana 3001:3000"
echo "              Then access: http://localhost:3001 (admin/admin)"
echo ""
echo "  Prometheus: kubectl port-forward -n websearch-api svc/prometheus 9090:9090"
echo "              Then access: http://localhost:9090"
echo ""
echo "  Jaeger:     kubectl port-forward -n websearch-api svc/jaeger 16686:16686"
echo "              Then access: http://localhost:16686"
echo ""
echo "🔍 USEFUL COMMANDS:"
echo ""
echo "  Watch pods:       kubectl get pods -n websearch-api -w"
echo "  Check ingress:    kubectl get ingress -n websearch-api"
echo "  API logs:         kubectl logs -f deployment/websearch-api -n websearch-api"
echo "  Dashboard logs:   kubectl logs -f deployment/dashboard -n websearch-api"
echo ""
echo "📚 DOCUMENTATION:"
echo ""
echo "  Quick Start:      k8s/QUICKSTART.md"
echo "  Ingress Guide:    k8s/INGRESS_ACCESS.md"
echo "  Full README:      k8s/README.md"
echo ""
