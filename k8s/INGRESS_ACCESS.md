# Kubernetes Deployment with Ingress - Access Guide

## Overview

The WebSearch API is now deployed with **nginx-ingress-controller** which eliminates the need for port-forwarding. All services are accessible through a single entry point at **http://localhost/** (port 80).

## Architecture

```
Browser (localhost:80)
    ↓
Ingress Controller (nginx)
    ↓
    ├─→ /api/v1/* → WebSearch API Service (internal)
    └─→ /*        → Dashboard Service (internal)
```

## Access URLs

All services are accessible directly via localhost:

| Service | URL | Description |
|---------|-----|-------------|
| **Dashboard** | http://localhost/ | Main admin dashboard UI |
| **API** | http://localhost/api/v1 | REST API endpoints |
| **Health Check** | http://localhost/api/v1/health | API health status |
| **Grafana** | Forward required: `kubectl port-forward -n websearch-api svc/grafana 3001:3000` | Metrics visualization |
| **Prometheus** | Forward required: `kubectl port-forward -n websearch-api svc/prometheus 9090:9090` | Metrics storage |
| **Jaeger** | Forward required: `kubectl port-forward -n websearch-api svc/jaeger 16686:16686` | Distributed tracing |

## Login Credentials

- **Username:** `admin`
- **Password:** `admin`

**Note:** First login requires password change.

## Quick Start

### 1. Deploy the Cluster

```bash
cd k8s
./deploy.sh
```

### 2. Wait for All Pods to be Ready

```bash
kubectl get pods -n websearch-api -w
```

All pods should show `Running` status (may take 1-2 minutes).

### 3. Access the Dashboard

Open your browser and navigate to:

```
http://localhost/
```

**No port-forwarding needed!** The ingress controller handles all routing.

### 4. Login

1. Enter username: `admin`
2. Enter password: `admin`
3. You'll be prompted to change your password
4. After password change, you'll receive an API key
5. You're now logged into the dashboard!

## How It Works

### Ingress Controller

The nginx-ingress-controller creates a LoadBalancer service that listens on `localhost:80` and routes traffic based on URL paths:

- Requests to `/api/v1/*` are forwarded to the API service
- All other requests (`/*`) are forwarded to the Dashboard service

### Services

All application services use **ClusterIP** type (internal only). The ingress controller is the only service exposed externally.

```bash
# Check ingress status
kubectl get ingress -n websearch-api

# Check ingress controller
kubectl get svc -n ingress-nginx
```

### Same-Origin Benefits

Since both the dashboard and API are served from the same origin (`localhost`), there are:
- ✅ No CORS issues
- ✅ No need for absolute URLs
- ✅ Simplified configuration
- ✅ Production-ready pattern

## Troubleshooting

### Dashboard Not Loading

Check ingress status:
```bash
kubectl get ingress -n websearch-api
```

Should show an ADDRESS (e.g., `172.20.0.9`).

### API Returning 404

Check that API service has endpoints:
```bash
kubectl get endpoints -n websearch-api websearch-api
```

Should show pod IPs.

### Login Failing

1. Check API logs:
```bash
kubectl logs -n websearch-api deployment/websearch-api --tail=50
```

2. Reset admin password if needed:
```bash
kubectl exec mongodb-0 -n websearch-api -- mongosh -u admin -p admin123 --eval '
db.getSiblingDB("websearch_api").users.updateOne(
  {username: "admin"},
  {$set: {
    password_hash: "$2b$12$Ki6iRnSTRcp8M/DWBcG2DuoKhqxtM00C2pdcYjxqrQaUvVgvKqg.W",
    first_login: true,
    api_key_hash: null
  }}
);
'
```

### Port 80 Already in Use

If another service is using port 80, the ingress controller LoadBalancer won't start. Check with:

```bash
lsof -i :80
```

Stop the conflicting service or change the ingress controller service port.

## Monitoring Services

Grafana, Prometheus, and Jaeger are not exposed through ingress. To access them, use port-forwarding:

```bash
# Grafana
kubectl port-forward -n websearch-api svc/grafana 3001:3000
# Access at http://localhost:3001 (admin/admin)

# Prometheus  
kubectl port-forward -n websearch-api svc/prometheus 9090:9090
# Access at http://localhost:9090

# Jaeger
kubectl port-forward -n websearch-api svc/jaeger 16686:16686
# Access at http://localhost:16686
```

## Cleanup

To remove the entire deployment:

```bash
cd k8s
./cleanup.sh
```

This will delete:
- All application resources in `websearch-api` namespace
- The namespace itself
- The nginx-ingress-controller (optional - comment out in cleanup.sh to keep)

## Advantages Over Port-Forwarding

| Port-Forwarding | Ingress |
|-----------------|---------|
| Must manually forward each service | Single entry point |
| Process must stay running | Always available |
| Different ports for each service | Clean URLs on port 80 |
| CORS issues possible | Same-origin, no CORS |
| Not production-ready | Production pattern |
| Local development only | Works on any Kubernetes |

## Next Steps

### Add TLS/HTTPS

Create a self-signed certificate and update ingress:

```bash
# Generate certificate
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout tls.key -out tls.crt \
  -subj "/CN=localhost"

# Create secret
kubectl create secret tls websearch-tls \
  --key tls.key --cert tls.crt \
  -n websearch-api

# Update ingress to use TLS
kubectl patch ingress websearch-ingress -n websearch-api --type='json' \
  -p='[{"op": "add", "path": "/spec/tls", "value": [{"hosts": ["localhost"], "secretName": "websearch-tls"}]}]'
```

Access at `https://localhost/` (accept self-signed cert warning).

### Use Custom Domain

Add to `/etc/hosts`:
```
127.0.0.1 websearch.local
```

Update ingress to specify host:
```yaml
spec:
  rules:
  - host: websearch.local
    http:
      paths: ...
```

Access at `http://websearch.local/`

### Add Basic Auth

Add authentication at ingress level:

```bash
# Create htpasswd
htpasswd -c auth admin

# Create secret
kubectl create secret generic basic-auth \
  --from-file=auth \
  -n websearch-api

# Update ingress annotations
kubectl patch ingress websearch-ingress -n websearch-api --type='json' \
  -p='[{"op": "add", "path": "/metadata/annotations/nginx.ingress.kubernetes.io~1auth-type", "value": "basic"}, {"op": "add", "path": "/metadata/annotations/nginx.ingress.kubernetes.io~1auth-secret", "value": "basic-auth"}]'
```

## Documentation

- **Full README:** `k8s/README.md` - Complete Kubernetes deployment guide
- **Quick Start:** `k8s/QUICKSTART.md` - Fast deployment instructions
- **This Guide:** `k8s/INGRESS_ACCESS.md` - Ingress-based access (you are here)

## Support

For issues or questions, check:
1. Ingress controller logs: `kubectl logs -n ingress-nginx deployment/ingress-nginx-controller`
2. Application logs: `kubectl logs -n websearch-api deployment/websearch-api`
3. Pod status: `kubectl get pods -n websearch-api`
4. Service endpoints: `kubectl get endpoints -n websearch-api`
