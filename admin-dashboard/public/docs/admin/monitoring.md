# Monitoring & System Health

Comprehensive guide to monitoring the WebSearch API infrastructure.

## Overview

The WebSearch API provides multiple monitoring layers:
- **Grafana:** Visual dashboards and metrics
- **Prometheus:** Time-series metrics storage
- **Jaeger:** Distributed tracing
- **Audit Logs:** Request-level tracking

## Access Points

| Service | URL | Credentials |
|---------|-----|-------------|
| Grafana | http://localhost:3001 | admin / admin |
| Prometheus | http://localhost:9090 | None |
| Jaeger | http://localhost:16686 | None |
| Admin Dashboard | http://localhost:3000 | API Key |

## Grafana Dashboards

### WebSearch API Overview

Access: **Grafana → Dashboards → WebSearch API - System Overview**

**Key Metrics:**
1. **HTTP Requests per Second** - Real-time request rate
2. **Response Times** - Average latency across all endpoints
3. **Total Requests** - Cumulative request counter
4. **Error Rate** - Percentage of 4xx/5xx responses
5. **Active Requests** - Currently processing requests
6. **Status Codes** - Distribution over time
7. **Request Rate by Endpoint** - Hotspot identification
8. **Top Endpoints** - Most frequently accessed APIs

### Custom Dashboards

Create custom dashboards for specific metrics:

1. Navigate to Grafana → Create → Dashboard
2. Add Panel → Select Visualization Type
3. Query Prometheus metrics
4. Save dashboard

**Example Query - Search Latency:**
```promql
histogram_quantile(0.95, 
  rate(http_server_duration_milliseconds_bucket{endpoint="/api/v1/search"}[5m]))
```

## Prometheus Metrics

### Available Metrics

**HTTP Metrics:**
- `http_server_requests_total` - Total request counter
- `http_server_duration_milliseconds` - Request duration histogram
- `http_server_active_requests` - Active request gauge

**Application Metrics:**
- `search_queries_total` - Search request counter
- `search_results_returned` - Results per search
- `policy_blocks_total` - Blocked requests by policy
- `quota_exceeded_total` - Rate limit hits

**System Metrics:**
- `process_cpu_seconds_total` - CPU usage
- `process_resident_memory_bytes` - Memory usage
- `python_gc_collections_total` - Garbage collection stats

### Query Examples

**Request Rate:**
```promql
rate(http_server_requests_total[5m])
```

**Error Rate:**
```promql
sum(rate(http_server_requests_total{status_code=~"5.."}[5m])) 
/ 
sum(rate(http_server_requests_total[5m])) * 100
```

**Top Slow Endpoints:**
```promql
topk(5, 
  avg by (endpoint) (
    rate(http_server_duration_milliseconds_sum[5m])
    /
    rate(http_server_duration_milliseconds_count[5m])
  )
)
```

## Distributed Tracing

### View Traces in Jaeger

1. Open http://localhost:16686
2. Select Service: **websearch-api**
3. Search by:
   - Operation (e.g., POST /api/v1/search)
   - Tags (e.g., http.status_code=403)
   - Trace ID (from API response or audit log)

### Trace Anatomy

Each trace shows:
- **Request Span:** HTTP request handling
- **Database Spans:** Query execution times
- **External API Spans:** Search provider calls
- **Policy Evaluation:** Filter and policy checks

### Debugging with Traces

**Find slow requests:**
1. Search by operation: POST /api/v1/search
2. Sort by Duration (descending)
3. Click trace to see breakdown
4. Identify bottleneck spans

**Investigate errors:**
1. Search with Tags: error=true
2. View error spans for stack traces
3. Correlate with audit logs

## Audit Logs

### Access Audit Logs

**Admin Dashboard:**
1. Navigate to **Audit Logs** page
2. Filter by:
   - Client ID
   - Date range
   - Status (allowed/blocked/error)
   - Query keywords

**API Endpoint:**
```bash
curl -H "X-API-Key: ADMIN_KEY" \
  "http://localhost:8000/api/v1/admin/audit-logs?limit=100"
```

### Audit Log Fields

Each log entry contains:
- **Timestamp:** Request time
- **Client ID:** Who made the request
- **Query:** Search query text
- **Status:** allowed, blocked, or error
- **Policy Applied:** Which policies were enforced
- **Trace ID:** Link to distributed trace
- **Response Time:** Request duration
- **Results Count:** Number of results returned
- **Filtered Count:** Results removed by policies

### Export Audit Logs

```bash
# Export last 7 days to CSV
curl -H "X-API-Key: ADMIN_KEY" \
  "http://localhost:8000/api/v1/admin/audit-logs?format=csv&days=7" \
  > audit_logs_$(date +%Y%m%d).csv
```

## Alerts & Notifications

### Grafana Alerts

**Create Alert Rule:**

1. Edit panel in Grafana dashboard
2. Click **Alert** tab
3. Define condition:
   ```
   WHEN avg() OF query(A, 5m, now) IS ABOVE 100
   ```
4. Set evaluation interval: 1m
5. Configure notification channel

**Alert Channels:**
- Email
- Slack
- PagerDuty
- Webhooks

### Prometheus Alertmanager

**Example Alert Rules:**

```yaml
# alerts.yml
groups:
  - name: websearch_api
    interval: 30s
    rules:
      - alert: HighErrorRate
        expr: |
          sum(rate(http_server_requests_total{status_code=~"5.."}[5m]))
          / 
          sum(rate(http_server_requests_total[5m])) * 100 > 5
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High error rate detected"
          description: "Error rate is {{ $value }}%"
      
      - alert: APIDown
        expr: up{job="websearch-api"} == 0
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "WebSearch API is down"
      
      - alert: HighLatency
        expr: |
          histogram_quantile(0.95,
            rate(http_server_duration_milliseconds_bucket[5m])
          ) > 1000
        for: 10m
        labels:
          severity: warning
        annotations:
          summary: "API latency is high"
          description: "95th percentile latency: {{ $value }}ms"
```

## System Health Dashboard

### Admin Dashboard Health Page

Access: **Admin Dashboard → System Health**

**Three Tabs:**

1. **Health Status**
   - API status (up/down)
   - Database connectivity
   - Search provider status
   - Cache status

2. **System Logs**
   - Recent audit logs (last 20)
   - Real-time updates
   - Quick filter and search

3. **Monitoring**
   - Links to Grafana, Prometheus, Jaeger
   - Quick access to all monitoring tools

### Health Check Endpoint

```bash
# Check API health
curl http://localhost:8000/api/v1/health

# Response
{
  "status": "healthy",
  "version": "1.0.0",
  "uptime_seconds": 86400,
  "components": {
    "database": "healthy",
    "search_provider": "healthy",
    "cache": "healthy"
  }
}
```

## Performance Monitoring

### Key Performance Indicators

**Response Time Targets:**
- p50 (median): < 200ms
- p95: < 500ms
- p99: < 1000ms

**Availability Target:**
- 99.9% uptime (< 43 minutes downtime/month)

**Error Rate Target:**
- < 1% of all requests

### Capacity Planning

**Monitor These Metrics:**
1. **CPU Usage:** Should stay < 70%
2. **Memory Usage:** Should stay < 80%
3. **Request Rate:** Plan scaling at 80% capacity
4. **Database Connections:** Monitor pool utilization

**Scaling Triggers:**
```promql
# CPU > 70% for 10 minutes
avg(rate(process_cpu_seconds_total[1m])) * 100 > 70

# Memory > 80%
process_resident_memory_bytes / process_virtual_memory_bytes * 100 > 80

# Request rate > 1000/sec
rate(http_server_requests_total[1m]) > 1000
```

## Log Management

### Application Logs

**Log Locations:**
- Docker: `docker-compose logs api`
- System: `/var/log/websearch/api.log`

**Log Levels:**
- DEBUG: Detailed diagnostic information
- INFO: General informational messages
- WARNING: Warning messages
- ERROR: Error events
- CRITICAL: Critical failures

**Structured Logging:**
```json
{
  "timestamp": "2026-04-19T23:30:00Z",
  "level": "INFO",
  "message": "Search request processed",
  "trace_id": "abc123",
  "client_id": "client_xyz",
  "duration_ms": 234,
  "results_count": 10
}
```

### Log Rotation

```bash
# /etc/logrotate.d/websearch-api
/var/log/websearch/*.log {
    daily
    rotate 30
    compress
    delaycompress
    notifempty
    create 0640 websearch websearch
    sharedscripts
    postrotate
        systemctl reload websearch-api
    endscript
}
```

## Troubleshooting

### High Error Rate

1. Check Grafana Error Rate panel
2. View recent audit logs for error patterns
3. Search Jaeger for error traces
4. Review application logs for stack traces

### Slow Performance

1. Check Grafana Response Time panel
2. Identify slow endpoints
3. View traces for slow requests
4. Check database query performance
5. Monitor search provider latency

### Database Issues

```bash
# Check database connections
docker-compose exec postgres psql -U websearch -c "
  SELECT count(*) FROM pg_stat_activity WHERE datname='websearch';
"

# Check slow queries
SELECT query, mean_exec_time 
FROM pg_stat_statements 
ORDER BY mean_exec_time DESC 
LIMIT 10;
```

### Search Provider Issues

```bash
# Check search provider status
curl http://localhost:8000/api/v1/admin/system/health

# Test direct provider connection
curl -H "Authorization: Bearer PROVIDER_KEY" \
  https://api.search-provider.com/v1/status
```

## Best Practices

### Monitoring Workflow

1. **Daily:** Review Grafana dashboard for anomalies
2. **Weekly:** Analyze audit logs for patterns
3. **Monthly:** Review capacity and plan scaling
4. **Quarterly:** Audit security and compliance logs

### Alert Fatigue Prevention

- Set appropriate thresholds
- Use alert grouping
- Implement alert escalation
- Regular alert rule review

### Data Retention

- **Metrics:** 90 days (Prometheus)
- **Traces:** 7 days (Jaeger)
- **Audit Logs:** 1 year (Database)
- **Application Logs:** 30 days (Disk)

## Next Steps

- Set up [Alert Rules](../guides/troubleshooting.md#alerts)
- Configure [Backup Strategy](installation.md#backup-strategy)
- Review [Security Monitoring](security.md#monitoring)
