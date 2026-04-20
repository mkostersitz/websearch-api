# Kubernetes Deployment for WebSearch API

This directory contains Kubernetes manifests to deploy the complete WebSearch API stack with nginx-ingress for external access.

## ⚡ Quick Start

```bash
cd k8s
./deploy.sh
```

**Access the dashboard:** http://localhost/ 

**Login:** admin / admin (change password on first login)

**No port-forwarding needed!** See [INGRESS_ACCESS.md](INGRESS_ACCESS.md) for details.

---

## Architecture

The deployment uses **nginx-ingress-controller** for clean external access:

```
Browser → localhost:80
    ↓
Ingress Controller (nginx)
    ↓
    ├─→ /api/v1/* → WebSearch API (ClusterIP)
    └─→ /*        → Dashboard (ClusterIP)
```

The deployment includes:

### Application Layer
- **API Server** (2 replicas) - FastAPI application
- **Dashboard** (2 replicas) - React admin dashboard

### Data Layer
- **MongoDB** (StatefulSet) - Primary database with persistent storage
- **Redis** (Deployment) - Caching and rate limiting

### Monitoring & Observability
- **OTEL Collector** - OpenTelemetry collector for traces and metrics
- **Prometheus** - Metrics storage and querying
- **Grafana** - Metrics visualization dashboards
- **Jaeger** - Distributed tracing UI

## Prerequisites

1. **Docker Desktop with Kubernetes enabled**
   ```bash
   # Verify Kubernetes is running
   kubectl cluster-info
   ```

2. **Built Docker images** (handled by deploy script)
   - `websearch-api:latest`
   - `websearch-dashboard:latest`

## Quick Start

### Deploy Everything

```bash
# Deploy to Kubernetes (builds images automatically)
./k8s/deploy.sh
```

This will:
1. Build Docker images for API and Dashboard
2. Install nginx-ingress-controller
3. Create the `websearch-api` namespace
4. Deploy MongoDB with persistent storage
5. Deploy all services with proper networking
6. Configure ingress for external access

Wait for all pods to be running (1-2 minutes):
```bash
kubectl get pods -n websearch-api -w
```

### Access Services

**Dashboard:** http://localhost/

**API:** http://localhost/api/v1/

**Health Check:** http://localhost/api/v1/health

**Monitoring (requires port-forward):**
```bash
kubectl port-forward -n websearch-api svc/grafana 3001:3000
kubectl port-forward -n websearch-api svc/prometheus 9090:9090  
kubectl port-forward -n websearch-api svc/jaeger 16686:16686
```


4. Deploy Redis for caching
5. Deploy OTEL Collector, Prometheus, Jaeger, Grafana
6. Deploy the API and Dashboard
7. Wait for all services to be ready

### Access Services

Once deployed, services are available via LoadBalancer:

- **API**: http://localhost:8000
- **Dashboard**: http://localhost:3000
- **Grafana**: http://localhost:3001 (admin/admin)
- **Prometheus**: http://localhost:9090
- **Jaeger**: http://localhost:16686

### Check Deployment Status

```bash
# View all pods
kubectl get pods -n websearch-api

# View all services
kubectl get svc -n websearch-api

# View persistent volumes
kubectl get pvc -n websearch-api

# Watch pod status
kubectl get pods -n websearch-api -w
```

### View Logs

```bash
# API logs
kubectl logs -f deployment/websearch-api -n websearch-api

# Dashboard logs
kubectl logs -f deployment/dashboard -n websearch-api

# MongoDB logs
kubectl logs -f statefulset/mongodb -n websearch-api

# All pods
kubectl logs -f -l app=websearch-api -n websearch-api
```

### Port Forwarding (Alternative Access)

If LoadBalancer IPs aren't assigned:

```bash
# API
kubectl port-forward svc/websearch-api 8000:8000 -n websearch-api

# Dashboard
kubectl port-forward svc/dashboard 3000:3000 -n websearch-api

# Grafana
kubectl port-forward svc/grafana 3001:3001 -n websearch-api

# Prometheus
kubectl port-forward svc/prometheus 9090:9090 -n websearch-api

# Jaeger
kubectl port-forward svc/jaeger 16686:16686 -n websearch-api
```

## Configuration

### Environment Variables

Edit `k8s/base/configmap.yaml` to configure:
- Database connection
- Redis URL
- OTEL endpoints
- Rate limiting
- Log levels

### Scaling

```bash
# Scale API replicas
kubectl scale deployment/websearch-api --replicas=3 -n websearch-api

# Scale dashboard
kubectl scale deployment/dashboard --replicas=3 -n websearch-api
```

### Resource Limits

Resource requests and limits are defined in deployment manifests:

**API Server:**
- Requests: 200m CPU, 256Mi memory
- Limits: 500m CPU, 512Mi memory

**Dashboard:**
- Requests: 50m CPU, 64Mi memory
- Limits: 100m CPU, 128Mi memory

**MongoDB:**
- Requests: 200m CPU, 256Mi memory
- Limits: 500m CPU, 512Mi memory
- Storage: 10Gi persistent volume

## Cleanup

To remove all deployed resources:

```bash
./k8s/cleanup.sh
```

This will delete:
- All deployments and services
- ConfigMaps and secrets
- Persistent volumes (MongoDB data will be lost!)
- The websearch-api namespace

## Updating

### Update API Code

```bash
# Rebuild API image
docker build -t websearch-api:latest -f Dockerfile .

# Restart API pods to use new image
kubectl rollout restart deployment/websearch-api -n websearch-api

# Watch rollout status
kubectl rollout status deployment/websearch-api -n websearch-api
```

### Update Dashboard Code

```bash
# Rebuild dashboard image
docker build -t websearch-dashboard:latest -f Dockerfile.dashboard .

# Restart dashboard pods
kubectl rollout restart deployment/dashboard -n websearch-api

# Watch rollout status
kubectl rollout status deployment/dashboard -n websearch-api
```

## Troubleshooting

### Pods not starting

```bash
# Describe pod to see events
kubectl describe pod <pod-name> -n websearch-api

# Check pod logs
kubectl logs <pod-name> -n websearch-api

# Check previous pod logs if crashed
kubectl logs <pod-name> -n websearch-api --previous
```

### Service connectivity issues

```bash
# Test service DNS
kubectl run -it --rm debug --image=busybox --restart=Never -n websearch-api -- nslookup mongodb

# Test service connectivity
kubectl run -it --rm debug --image=busybox --restart=Never -n websearch-api -- nc -zv mongodb 27017
```

### View all resources

```bash
kubectl get all -n websearch-api
```

### Reset MongoDB data

```bash
# Delete the PVC (will delete all data!)
kubectl delete pvc mongodb-pvc -n websearch-api

# Redeploy MongoDB
kubectl apply -f k8s/base/mongodb.yaml
```

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                      Kubernetes Cluster                      │
│  ┌────────────────────────────────────────────────────────┐ │
│  │              Namespace: websearch-api                  │ │
│  │                                                         │ │
│  │  ┌──────────────┐    ┌──────────────┐                │ │
│  │  │  Dashboard   │    │   API Server │                │ │
│  │  │  (2 replicas)│    │  (2 replicas)│                │ │
│  │  └──────┬───────┘    └───────┬──────┘                │ │
│  │         │                    │                         │ │
│  │         └────────┬───────────┘                         │ │
│  │                  │                                      │ │
│  │         ┌────────┴─────────┐                          │ │
│  │         │                  │                           │ │
│  │    ┌────▼─────┐      ┌────▼────┐                     │ │
│  │    │ MongoDB  │      │  Redis  │                      │ │
│  │    │(StatefulSet)    │         │                      │ │
│  │    └──────────┘      └─────────┘                      │ │
│  │                                                         │ │
│  │    ┌──────────────────────────────────────┐           │ │
│  │    │     Monitoring & Observability       │           │ │
│  │    │                                       │           │ │
│  │    │  ┌──────────┐  ┌──────────────┐     │           │ │
│  │    │  │   OTEL   │  │  Prometheus  │     │           │ │
│  │    │  │Collector │  │              │     │           │ │
│  │    │  └────┬─────┘  └──────┬───────┘     │           │ │
│  │    │       │               │              │           │ │
│  │    │  ┌────▼─────┐   ┌────▼────┐         │           │ │
│  │    │  │  Jaeger  │   │ Grafana │         │           │ │
│  │    │  │ (Traces) │   │(Dashboards)       │           │ │
│  │    │  └──────────┘   └─────────┘         │           │ │
│  │    └──────────────────────────────────────┘           │ │
│  └─────────────────────────────────────────────────────── │ │
└─────────────────────────────────────────────────────────────┘
```

## Default Credentials

- **MongoDB**: admin/admin123
- **Grafana**: admin/admin
- **Dashboard**: admin/admin (first login)

## Production Considerations

For production deployment, consider:

1. **Use Secrets** for sensitive data instead of ConfigMaps
2. **Enable TLS/SSL** for all services
3. **Configure Ingress** instead of LoadBalancer
4. **Use external databases** (managed MongoDB, Redis)
5. **Configure persistent volumes** properly (StorageClass)
6. **Set up monitoring alerts** in Grafana
7. **Implement backup strategy** for MongoDB
8. **Use image tags** instead of `latest`
9. **Configure resource quotas** at namespace level
10. **Enable network policies** for security
