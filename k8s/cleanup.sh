#!/bin/bash

# Delete all Kubernetes resources
set -e

# Get the directory where the script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Change to k8s directory
cd "$SCRIPT_DIR"

echo "=== Deleting WebSearch API from Kubernetes ==="

echo "Deleting ingress..."
kubectl delete -f base/ingress.yaml --ignore-not-found=true

echo "Deleting application deployments..."
kubectl delete -f base/dashboard-deployment.yaml --ignore-not-found=true
kubectl delete -f base/api-deployment.yaml --ignore-not-found=true

echo "Deleting monitoring stack..."
kubectl delete -f base/grafana.yaml --ignore-not-found=true
kubectl delete -f base/jaeger.yaml --ignore-not-found=true
kubectl delete -f base/prometheus.yaml --ignore-not-found=true
kubectl delete -f base/otel-collector.yaml --ignore-not-found=true

echo "Deleting data layer..."
kubectl delete -f base/redis.yaml --ignore-not-found=true
kubectl delete -f base/mongodb.yaml --ignore-not-found=true

echo "Deleting ConfigMaps..."
kubectl delete -f base/configmap.yaml --ignore-not-found=true

echo ""
echo "Waiting for pods to terminate..."
kubectl wait --for=delete pod --all -n websearch-api --timeout=120s || true

echo ""
echo "Deleting namespace..."
kubectl delete -f base/namespace.yaml --ignore-not-found=true

echo ""
echo "=== Optional: Remove nginx-ingress-controller ==="
echo ""
echo "The nginx-ingress-controller is still installed and can be used by other projects."
echo "To remove it, run:"
echo ""
echo "  kubectl delete namespace ingress-nginx"
echo ""

echo ""
echo "╔════════════════════════════════════════════════════════════════╗"
echo "║                    🗑️  Cleanup Complete!                      ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""
echo "All WebSearch API resources have been removed from Kubernetes."
echo ""
