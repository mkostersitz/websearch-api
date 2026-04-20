# Grafana Dashboard - WebSearch API

## Overview

A comprehensive Grafana dashboard has been created to visualize all metrics collected from the WebSearch API system. The dashboard provides real-time monitoring with click-through links to raw Prometheus data for deep analysis.

## Dashboard Panels

### 1. HTTP Requests per Second
**What it shows:** Real-time request rate across all endpoints
- Active requests currently being processed
- Request rate calculated over 5-minute windows
- Grouped by HTTP method and endpoint

**Click-through:** Direct link to Prometheus query explorer

### 2. HTTP Response Times
**What it shows:** Average request duration in milliseconds
- Calculated as sum/count from histogram metrics
- Shows average response time across all endpoints
- Real-time latency monitoring

**Use case:** Identify slow endpoints and performance degradation

### 3. Total Requests (Stat Panel)
**What it shows:** Total HTTP requests since API start
- Direct counter value (not rate-based)
- Color-coded thresholds:
  - Green: < 100 requests
  - Yellow: 100-1,000 requests
  - Red: > 1,000 requests
- Includes sparkline graph for trend visualization

### 4. Error Rate (Stat Panel)
**What it shows:** Percentage of failed requests (4xx and 5xx)
- Color-coded thresholds:
  - Green: < 1% error rate
  - Yellow: 1-5% error rate
  - Red: > 5% error rate

**Use case:** Quick health check for API stability

### 5. Active Requests (Stat Panel)
**What it shows:** Currently processing requests
- Real-time view of concurrent request load
- Threshold alerts:
  - Green: < 10 active
  - Yellow: 10-50 active
  - Red: > 50 active

### 6. HTTP Status Codes
**What it shows:** Distribution of response codes over time
- Stacked area chart showing all status codes
- Identifies patterns in success/failure rates
- Shows: 200, 400, 403, 404, 500, 503, etc.

### 7. Request Rate by Endpoint
**What it shows:** Which API endpoints are most active
- Breakdown of requests per second by endpoint path
- Includes summary statistics (mean, max)

**Use case:** Identify hotspots and optimize high-traffic endpoints

### 8. Top Endpoints Table (Removed - OTEL Collector panel removed)
**What it shows:** Top 10 endpoints by total request count
- Sortable table with method and endpoint
- Instant query showing current totals
- Updated in real-time

**Use case:** Identify most-used API endpoints

## Features

### Time Range Selector
- Quick ranges: Last 5m, 15m, 30m, 1h, 6h, 12h, 24h, 7d
- Custom range picker
- Auto-refresh: 30 seconds (configurable)

### Template Variables
- **Rate Interval:** Uses fixed 1m intervals for rate calculations
- Auto-refresh: 30 seconds
- Time range: Last 1 hour (default)

### Click-Through Links (Note: Not yet implemented)
Future enhancement to add "View in Prometheus" links from each panel

### Dashboard Refresh
- Auto-refresh every 30 seconds
- Manual refresh button in toolbar
- Real-time data visualization

## Accessing the Dashboard

### 1. Start Monitoring Stack
```bash
./run.sh monitoring
# Or
docker-compose up -d grafana prometheus otel-collector jaeger
```

### 2. Open Grafana
- URL: http://localhost:3001
- Username: `admin`
- Password: `admin`
- Dashboard auto-loads on login

### 3. From Admin Dashboard
1. Navigate to System Health page
2. Click "Monitoring" tab
3. Click "Open Grafana" button
4. Dashboard loads automatically

## Dashboard Files

### Created Files
```
grafana/
├── datasources/
│   └── prometheus.yml          # Prometheus datasource config
└── dashboards/
    ├── dashboard-provider.yml  # Dashboard provisioning config
    └── websearch-api-overview.json  # Main dashboard definition
```

### docker-compose.yml Updates
- Added volume mounts for dashboard/datasource provisioning
- Set default home dashboard
- Grafana now auto-loads WebSearch API dashboard on startup

## Metrics Available

### HTTP Metrics (from FastAPI + OTEL)
- `http_server_requests_total` - Total request counter
- `http_server_duration_milliseconds` - Request duration histogram
- `http_server_active_requests` - Current active requests gauge

### OTEL Collector Metrics
- `otelcol_receiver_accepted_spans` - Tracing spans received
- `otelcol_receiver_accepted_metric_points` - Metrics received
- `otelcol_exporter_sent_spans` - Spans exported to Jaeger

### System Metrics
- `process_cpu_seconds_total` - CPU time consumed
- `process_resident_memory_bytes` - Memory usage

## Prometheus Query Examples

### Request Rate
```promql
rate(http_server_requests_total{job="websearch-api"}[5m])
```

### Error Rate Percentage
```promql
sum(rate(http_server_requests_total{job="websearch-api",status_code=~"4..|5.."}[5m])) / 
sum(rate(http_server_requests_total{job="websearch-api"}[5m])) * 100
```

### 95th Percentile Latency (Note: Using average instead)
```promql
# Average latency
http_server_duration_milliseconds_sum / http_server_duration_milliseconds_count
```

### Top Endpoints
```promql
topk(10, sum by (endpoint, method) 
  (increase(http_server_requests_total{job="websearch-api"}[1h])))
```

## Customization

### Adding New Panels
1. Click "+ Add" in Grafana toolbar
2. Select "Visualization"
3. Choose panel type (Graph, Stat, Table, etc.)
4. Write Prometheus query
5. Configure visualization options
6. Save dashboard

### Modifying Thresholds
1. Edit panel
2. Go to "Overrides" or "Thresholds"
3. Adjust color breakpoints
4. Save changes

### Creating Alerts
1. Edit panel
2. Click "Alert" tab
3. Define alert conditions
4. Configure notification channels
5. Save alert rule

## Best Practices

### Monitoring Workflow
1. **Dashboard Overview** - Check all panels for anomalies
2. **Drill Down** - Click panels with issues
3. **Raw Metrics** - Use Prometheus links for detailed analysis
4. **Correlate** - Cross-reference with Jaeger traces
5. **Investigate** - Check Audit Logs for specific requests

### Performance Analysis
1. Identify slow endpoints in Response Times panel
2. Click through to see raw histogram data
3. Correlate with Request Rate to find high-traffic slow endpoints
4. Use trace IDs from Audit Logs to view in Jaeger
5. Optimize identified bottlenecks

### Capacity Planning
1. Monitor System Resource Usage trends
2. Check Active Requests during peak hours
3. Review Total Requests growth over time
4. Plan scaling based on resource consumption patterns

## Troubleshooting

### Dashboard Not Loading
```bash
# Check Grafana is running
docker ps | grep grafana

# Check logs
docker logs websearch-grafana

# Restart Grafana
docker-compose restart grafana
```

### No Data Showing
```bash
# Verify Prometheus is scraping
curl http://localhost:9090/api/v1/targets

# Check OTEL Collector
curl http://localhost:8888/metrics

# Verify API is running
curl http://localhost:8000/health
```

### Datasource Issues
1. Go to Configuration → Data Sources
2. Select Prometheus
3. Click "Test" button
4. Should show "Data source is working"

## Next Steps

### Enhance Monitoring
- Add custom business metrics
- Create alert rules for critical thresholds
- Set up notification channels (Slack, PagerDuty, Email)
- Add annotation markers for deployments

### Additional Dashboards
- Search-specific metrics dashboard
- Client quota usage dashboard
- Policy enforcement dashboard
- Error analysis dashboard

### Advanced Features
- Set up Grafana Loki for log aggregation
- Configure distributed tracing panels
- Create custom alert channels
- Implement SLO/SLI tracking

## Reference Links

- **Grafana Documentation:** https://grafana.com/docs/grafana/latest/
- **Prometheus Query Language:** https://prometheus.io/docs/prometheus/latest/querying/basics/
- **OpenTelemetry Metrics:** https://opentelemetry.io/docs/concepts/signals/metrics/
- **FastAPI Instrumentation:** https://opentelemetry.io/docs/instrumentation/python/automatic/

---

**Dashboard Version:** 1.0  
**Last Updated:** 2026-04-19  
**Maintainer:** WebSearch API Team
