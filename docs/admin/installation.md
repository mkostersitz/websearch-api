# Installation & Setup

Complete guide to installing and configuring the WebSearch API.

## System Requirements

### Minimum Requirements
- **CPU:** 2 cores
- **RAM:** 4 GB
- **Disk:** 20 GB
- **OS:** Linux, macOS, or Windows (with WSL2)

### Recommended for Production
- **CPU:** 4+ cores
- **RAM:** 8+ GB
- **Disk:** 50+ GB SSD
- **OS:** Ubuntu 22.04 LTS or similar

### Software Dependencies
- Docker 24+ and Docker Compose 2.0+
- Python 3.11+
- Node.js 18+ (for admin dashboard)
- PostgreSQL 15+ (or use Docker)

---

## Quick Start (Docker)

### 1. Clone Repository
```bash
git clone https://github.com/your-org/websearch-api.git
cd websearch-api
```

### 2. Configure Environment
```bash
cp .env.example .env
# Edit .env with your settings
nano .env
```

**Required Environment Variables:**
```bash
# Database
DATABASE_URL=postgresql://websearch:password@localhost:5432/websearch

# Security
SECRET_KEY=your-secret-key-here-change-this
JWT_SECRET=your-jwt-secret-here

# OAuth (optional)
OKTA_DOMAIN=your-domain.okta.com
OKTA_CLIENT_ID=your_client_id
OKTA_CLIENT_SECRET=your_client_secret

AZURE_TENANT_ID=your_tenant_id
AZURE_CLIENT_ID=your_client_id
AZURE_CLIENT_SECRET=your_client_secret

# Search Provider
SEARCH_PROVIDER=brave  # or bing, google
SEARCH_API_KEY=your_search_api_key

# Monitoring (optional)
OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4317
JAEGER_ENDPOINT=http://localhost:14268/api/traces
```

### 3. Start Services
```bash
# Start all services
./run.sh start

# Or manually with docker-compose
docker-compose up -d
```

### 4. Initialize Database
```bash
# Run migrations
./run.sh migrate

# Create admin user
./run.sh create-admin \
  --email admin@example.com \
  --password Admin123!
```

### 5. Verify Installation
```bash
# Check API health
curl http://localhost:8000/api/v1/health

# Check admin dashboard
open http://localhost:3000
```

---

## Manual Installation

### 1. Install Dependencies

**Python:**
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

**Node.js (Admin Dashboard):**
```bash
cd admin-dashboard
npm install
```

### 2. Setup Database

**Install PostgreSQL:**
```bash
# Ubuntu/Debian
sudo apt install postgresql postgresql-contrib

# macOS
brew install postgresql@15
```

**Create Database:**
```bash
sudo -u postgres psql

CREATE DATABASE websearch;
CREATE USER websearch WITH PASSWORD 'secure_password';
GRANT ALL PRIVILEGES ON DATABASE websearch TO websearch;
\q
```

**Run Migrations:**
```bash
alembic upgrade head
```

### 3. Configure Services

**API Server (systemd):**
```bash
sudo nano /etc/systemd/system/websearch-api.service
```

```ini
[Unit]
Description=WebSearch API Server
After=network.target postgresql.service

[Service]
Type=simple
User=websearch
WorkingDirectory=/opt/websearch-api
Environment="PATH=/opt/websearch-api/venv/bin"
ExecStart=/opt/websearch-api/venv/bin/uvicorn src.main:app --host 0.0.0.0 --port 8000
Restart=always

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable websearch-api
sudo systemctl start websearch-api
```

**Admin Dashboard (systemd):**
```bash
sudo nano /etc/systemd/system/websearch-dashboard.service
```

```ini
[Unit]
Description=WebSearch Admin Dashboard
After=network.target

[Service]
Type=simple
User=websearch
WorkingDirectory=/opt/websearch-api/admin-dashboard
ExecStart=/usr/bin/npm start
Environment="PORT=3000"
Restart=always

[Install]
WantedBy=multi-user.target
```

---

## Production Configuration

### Reverse Proxy (Nginx)

```nginx
# /etc/nginx/sites-available/websearch-api

upstream api_backend {
    server localhost:8000;
    keepalive 32;
}

upstream dashboard_backend {
    server localhost:3000;
    keepalive 32;
}

server {
    listen 443 ssl http2;
    server_name api.example.com;

    ssl_certificate /etc/ssl/certs/api.example.com.crt;
    ssl_certificate_key /etc/ssl/private/api.example.com.key;

    # Security headers
    add_header Strict-Transport-Security "max-age=31536000" always;
    add_header X-Frame-Options "DENY" always;
    add_header X-Content-Type-Options "nosniff" always;

    location /api/v1/ {
        proxy_pass http://api_backend;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
}

server {
    listen 443 ssl http2;
    server_name dashboard.example.com;

    ssl_certificate /etc/ssl/certs/dashboard.example.com.crt;
    ssl_certificate_key /etc/ssl/private/dashboard.example.com.key;

    location / {
        proxy_pass http://dashboard_backend;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

### SSL/TLS Configuration

**Generate Self-Signed Certificate (Dev):**
```bash
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout /etc/ssl/private/websearch.key \
  -out /etc/ssl/certs/websearch.crt
```

**Let's Encrypt (Production):**
```bash
sudo certbot --nginx -d api.example.com -d dashboard.example.com
```

### Client Certificate Authentication

**Enable mTLS:**
```bash
# Generate CA
openssl genrsa -out ca.key 4096
openssl req -new -x509 -days 365 -key ca.key -out ca.crt

# Generate client certificate
openssl genrsa -out client.key 2048
openssl req -new -key client.key -out client.csr
openssl x509 -req -days 365 -in client.csr -CA ca.crt -CAkey ca.key -set_serial 01 -out client.crt
```

**Configure API:**
```python
# .env
CLIENT_CERT_REQUIRED=true
CLIENT_CERT_CA=/path/to/ca.crt
```

---

## Monitoring Setup

### OpenTelemetry Collector

**Configuration:**
```yaml
# otel-collector-config.yaml
receivers:
  otlp:
    protocols:
      grpc:
        endpoint: 0.0.0.0:4317
      http:
        endpoint: 0.0.0.0:4318

processors:
  batch:
    timeout: 10s
    send_batch_size: 1024

exporters:
  jaeger:
    endpoint: jaeger:14250
    tls:
      insecure: true
  
  prometheus:
    endpoint: "0.0.0.0:8888"

service:
  pipelines:
    traces:
      receivers: [otlp]
      processors: [batch]
      exporters: [jaeger]
    
    metrics:
      receivers: [otlp]
      processors: [batch]
      exporters: [prometheus]
```

### Prometheus

**Configuration:**
```yaml
# prometheus.yml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: 'websearch-api'
    static_configs:
      - targets: ['localhost:8000']
  
  - job_name: 'otel-collector'
    static_configs:
      - targets: ['localhost:8888']
```

### Grafana

**Provisioning:**
```yaml
# grafana/provisioning/datasources/prometheus.yml
apiVersion: 1

datasources:
  - name: Prometheus
    type: prometheus
    access: proxy
    url: http://prometheus:9090
    isDefault: true
```

---

## Database Optimization

### Connection Pooling
```python
# database.py
engine = create_engine(
    DATABASE_URL,
    pool_size=20,
    max_overflow=10,
    pool_pre_ping=True,
    pool_recycle=3600
)
```

### Indexes
```sql
-- Create indexes for common queries
CREATE INDEX idx_audit_client_timestamp ON audit_logs(client_id, timestamp DESC);
CREATE INDEX idx_audit_trace ON audit_logs(trace_id);
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_api_keys_hash ON api_keys(key_hash);
```

### Backup Strategy
```bash
#!/bin/bash
# backup.sh

BACKUP_DIR="/var/backups/websearch"
DATE=$(date +%Y%m%d_%H%M%S)

# Backup database
pg_dump -U websearch -h localhost websearch | gzip > "$BACKUP_DIR/db_$DATE.sql.gz"

# Backup config files
tar czf "$BACKUP_DIR/config_$DATE.tar.gz" /opt/websearch-api/.env

# Retain last 30 days
find "$BACKUP_DIR" -name "*.gz" -mtime +30 -delete
```

Add to crontab:
```bash
0 2 * * * /opt/websearch-api/scripts/backup.sh
```

---

## Security Hardening

### Firewall Rules
```bash
# Allow SSH
sudo ufw allow 22/tcp

# Allow HTTPS
sudo ufw allow 443/tcp

# Block direct API access (use reverse proxy)
sudo ufw deny 8000/tcp

# Enable firewall
sudo ufw enable
```

### Fail2Ban Configuration
```ini
# /etc/fail2ban/jail.local
[websearch-api]
enabled = true
port = 443
filter = websearch-api
logpath = /var/log/websearch/api.log
maxretry = 5
bantime = 3600
```

### Rate Limiting
```python
# Configure in .env
RATE_LIMIT_PER_MINUTE=60
RATE_LIMIT_PER_DAY=5000
RATE_LIMIT_BURST=100
```

---

## Scaling

### Horizontal Scaling

**Load Balancer (HAProxy):**
```
# haproxy.cfg
frontend api_frontend
    bind *:443 ssl crt /etc/ssl/certs/api.pem
    default_backend api_backend

backend api_backend
    balance roundrobin
    option httpchk GET /health
    server api1 10.0.1.10:8000 check
    server api2 10.0.1.11:8000 check
    server api3 10.0.1.12:8000 check
```

### Caching Layer

**Redis Configuration:**
```python
# cache.py
import redis

redis_client = redis.Redis(
    host='localhost',
    port=6379,
    db=0,
    decode_responses=True
)

# Cache search results for 1 hour
def cache_search(query, results):
    key = f"search:{hash(query)}"
    redis_client.setex(key, 3600, json.dumps(results))
```

---

## Troubleshooting

### Check Logs
```bash
# API logs
tail -f /var/log/websearch/api.log

# Docker logs
docker-compose logs -f api

# System logs
journalctl -u websearch-api -f
```

### Common Issues

**Database Connection Error:**
```bash
# Test connection
psql -U websearch -h localhost -d websearch

# Check PostgreSQL status
sudo systemctl status postgresql
```

**Port Already in Use:**
```bash
# Find process using port
lsof -i :8000

# Kill process
kill -9 PID
```

**Permission Denied:**
```bash
# Fix ownership
sudo chown -R websearch:websearch /opt/websearch-api

# Fix permissions
chmod 600 .env
chmod 755 run.sh
```

---

## Next Steps

- Configure [User Management](user-management.md)
- Set up [Search Policies](policy-management.md)
- Enable [Monitoring](monitoring.md)
- Review [Security Best Practices](security.md)
