# WebSearch API - Kubernetes Quick Start Guide

Get the WebSearch API running in Kubernetes in under 5 minutes!

## Prerequisites

- Docker Desktop with Kubernetes enabled
- kubectl command-line tool

## 1. Deploy

```bash
cd k8s
./deploy.sh
```

The script will:
- Build Docker images
- Install nginx-ingress-controller  
- Deploy all services to Kubernetes
- Wait for everything to be ready

## 2. Access

**Dashboard:** Open http://localhost/ in your browser

**API:** http://localhost/api/v1/

**No port-forwarding needed!** Ingress handles all routing.

## 3. Login

- **Username:** `admin`
- **Password:** `admin`

You'll be prompted to change the password on first login.

## That's It!

Your WebSearch API is now running in Kubernetes with:
- ✅ High availability (2 API replicas, 2 dashboard replicas)
- ✅ Persistent data storage (MongoDB with PVC)
- ✅ Monitoring (Prometheus, Grafana, Jaeger, OTEL)
- ✅ Clean URLs via ingress (no port conflicts)

---

## Access Monitoring

Grafana, Prometheus, and Jaeger require port-forwarding:

```bash
# Grafana (login: admin/admin)
kubectl port-forward -n websearch-api svc/grafana 3001:3000
# Then open http://localhost:3001

# Prometheus
kubectl port-forward -n websearch-api svc/prometheus 9090:9090
# Then open http://localhost:9090

# Jaeger
kubectl port-forward -n websearch-api svc/jaeger 16686:16686
# Then open http://localhost:16686
```

## Verify Deployment

```bash
# Check all pods
kubectl get pods -n websearch-api

# Check ingress
kubectl get ingress -n websearch-api

# Check services
kubectl get svc -n websearch-api
```

All pods should show `Running` status.

## Cleanup

To remove everything:

```bash
./cleanup.sh
```

## Troubleshooting

### Dashboard not loading

```bash
# Check ingress has an address
kubectl get ingress -n websearch-api

# Check pods are running
kubectl get pods -n websearch-api
```

### API not responding

```bash
# Check API logs
kubectl logs -n websearch-api deployment/websearch-api

# Check API service has endpoints
kubectl get endpoints -n websearch-api websearch-api
```

### Port 80 already in use

Check what's using port 80:
```bash
lsof -i :80
```

Stop the conflicting service or modify the ingress controller.

## More Information

- **Access Guide:** [INGRESS_ACCESS.md](INGRESS_ACCESS.md) - Detailed access instructions
- **Full README:** [README.md](README.md) - Complete deployment guide
- **Original Port-Forward:** The `port-forward.sh` script is deprecated but still available as a fallback

## API Examples

```bash
# Health check
curl http://localhost/api/v1/health

# Login
curl -X POST http://localhost/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin"}'

# Search (with API key)
curl -X POST http://localhost/api/v1/search \
  -H "X-API-Key: YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"query": "kubernetes", "max_results": 5}'
```

## Next Steps

1. **Change Admin Password:** Login and follow the password change prompt
2. **Create Users:** Use the dashboard to create additional users
3. **Configure Policies:** Set up search policies and rate limits
4. **View Metrics:** Access Grafana to see system metrics
5. **Add TLS:** See [INGRESS_ACCESS.md](INGRESS_ACCESS.md) for HTTPS setup

---

**Questions?** Check the main [README.md](README.md) for detailed documentation.
