# API Reference

Complete reference for all WebSearch API endpoints.

## Base URL

```
http://localhost:8000/api/v1
```

## Authentication

All API requests require authentication using one of these methods:

### API Key (Header)
```http
X-API-Key: your_api_key_here
```

### Client Certificate
- Requires mTLS configuration
- Certificate CN must match registered client

### OAuth Token (Bearer)
```http
Authorization: Bearer your_oauth_token
```

---

## Search Endpoints

### POST /search

Execute a web search with policy enforcement and filtering.

**Request Body:**
```json
{
  "query": "search query string",
  "max_results": 10,
  "safe_search": "moderate",
  "filters": {
    "domains": ["edu", "org"],
    "exclude_domains": ["spam.com"],
    "content_types": ["html", "pdf"],
    "language": "en",
    "date_range": {
      "start": "2026-01-01",
      "end": "2026-12-31"
    }
  }
}
```

**Parameters:**
- `query` (required, string): Search query (1-500 characters)
- `max_results` (optional, integer): Number of results (1-100, default: 10)
- `safe_search` (optional, string): Safety level - `off`, `moderate`, `strict` (default: `moderate`)
- `filters` (optional, object): Result filtering options

**Response (200):**
```json
{
  "query": "artificial intelligence",
  "results": [
    {
      "title": "Page Title",
      "url": "https://example.com/page",
      "snippet": "Brief description of the page content...",
      "relevance_score": 0.95,
      "domain": "example.com",
      "content_type": "html",
      "published_date": "2026-03-15"
    }
  ],
  "total_results": 10,
  "search_time_ms": 234,
  "trace_id": "abc123-def456-ghi789",
  "policies_applied": ["enterprise_safe_search", "content_filter"],
  "filtered_count": 2
}
```

**Response Fields:**
- `query`: Original search query
- `results`: Array of search results
- `total_results`: Number of results returned
- `search_time_ms`: Search execution time
- `trace_id`: Distributed tracing ID (use for debugging)
- `policies_applied`: List of policies enforced
- `filtered_count`: Number of results filtered by policies

**Error Responses:**

**400 Bad Request:**
```json
{
  "error": "invalid_query",
  "message": "Query exceeds maximum length of 500 characters"
}
```

**403 Forbidden:**
```json
{
  "error": "policy_violation",
  "message": "Query blocked by enterprise search policy",
  "policy": "restricted_keywords",
  "trace_id": "xyz789"
}
```

**429 Too Many Requests:**
```json
{
  "error": "rate_limit_exceeded",
  "message": "Quota exceeded: 60 requests per minute",
  "retry_after": 42,
  "quota": {
    "limit": 60,
    "remaining": 0,
    "reset_time": "2026-04-19T23:59:00Z"
  }
}
```

---

### GET /search/suggestions

Get search query suggestions (autocomplete).

**Query Parameters:**
- `q` (required, string): Partial query (min 2 characters)
- `limit` (optional, integer): Max suggestions (1-10, default: 5)

**Example:**
```http
GET /api/v1/search/suggestions?q=machine+learn&limit=5
```

**Response (200):**
```json
{
  "query": "machine learn",
  "suggestions": [
    "machine learning",
    "machine learning algorithms",
    "machine learning python",
    "machine learning tutorial",
    "machine learning applications"
  ]
}
```

---

## Quota & Usage

### GET /quota

Check current API quota status.

**Response (200):**
```json
{
  "client_id": "client_abc123",
  "quotas": {
    "requests_per_minute": {
      "limit": 60,
      "remaining": 45,
      "reset_time": "2026-04-19T23:59:00Z"
    },
    "requests_per_day": {
      "limit": 5000,
      "remaining": 4321,
      "reset_time": "2026-04-20T00:00:00Z"
    }
  }
}
```

### GET /usage

Get usage statistics for your API key.

**Query Parameters:**
- `start_date` (optional, string): Start date (ISO 8601)
- `end_date` (optional, string): End date (ISO 8601)
- `granularity` (optional, string): `hour`, `day`, `week`, `month` (default: `day`)

**Example:**
```http
GET /api/v1/usage?start_date=2026-04-01&end_date=2026-04-19&granularity=day
```

**Response (200):**
```json
{
  "client_id": "client_abc123",
  "period": {
    "start": "2026-04-01T00:00:00Z",
    "end": "2026-04-19T23:59:59Z"
  },
  "total_requests": 1250,
  "successful_requests": 1180,
  "blocked_requests": 45,
  "error_requests": 25,
  "daily_breakdown": [
    {
      "date": "2026-04-01",
      "requests": 67,
      "blocked": 2,
      "errors": 1
    }
  ]
}
```

---

## Health & Status

### GET /health

Check API health status (no authentication required).

**Response (200):**
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "uptime_seconds": 86400,
  "timestamp": "2026-04-19T23:30:00Z"
}
```

**Response (503):**
```json
{
  "status": "unhealthy",
  "issues": [
    "search_provider_unavailable",
    "database_connection_slow"
  ]
}
```

---

## Admin Endpoints

These endpoints require admin privileges.

### GET /admin/clients

List all registered API clients.

**Headers:**
```http
X-API-Key: admin_api_key
```

**Response (200):**
```json
{
  "clients": [
    {
      "id": "client_abc123",
      "name": "AI Research Team",
      "email": "team@example.com",
      "created_at": "2026-03-01T10:00:00Z",
      "status": "active",
      "quota_tier": "standard"
    }
  ],
  "total": 5
}
```

### POST /admin/clients

Create a new API client.

**Request Body:**
```json
{
  "name": "New Client Name",
  "email": "client@example.com",
  "organization": "Example Corp",
  "quota_tier": "standard"
}
```

**Response (201):**
```json
{
  "client_id": "client_xyz789",
  "api_key": "GK_newkey123...",
  "message": "Client created successfully"
}
```

### GET /admin/audit-logs

Retrieve audit logs with filtering.

**Query Parameters:**
- `client_id` (optional): Filter by client
- `start_date` (optional): Start date
- `end_date` (optional): End date
- `status` (optional): `allowed`, `blocked`, `error`
- `limit` (optional): Max records (default: 100)
- `offset` (optional): Pagination offset

**Response (200):**
```json
{
  "logs": [
    {
      "id": "log_abc123",
      "timestamp": "2026-04-19T23:30:00Z",
      "client_id": "client_abc123",
      "query": "sensitive query",
      "status": "blocked",
      "reason": "Policy violation",
      "policy": "restricted_keywords",
      "trace_id": "trace_xyz789"
    }
  ],
  "total": 1523,
  "limit": 100,
  "offset": 0
}
```

---

## Rate Limits

### Default Quotas

| Tier | Requests/Min | Requests/Day | Burst Limit |
|------|--------------|--------------|-------------|
| Free | 10 | 1000 | 20 |
| Standard | 60 | 5000 | 100 |
| Premium | 300 | 50000 | 500 |
| Enterprise | Custom | Custom | Custom |

### Rate Limit Headers

All responses include rate limit headers:

```http
X-RateLimit-Limit: 60
X-RateLimit-Remaining: 45
X-RateLimit-Reset: 1713567540
```

---

## Tracing & Debugging

### Trace IDs

Every request generates a unique trace ID included in:
- Response JSON: `trace_id` field
- Response header: `X-Trace-ID`

**View Traces:**
- Jaeger UI: `http://localhost:16686`
- Search by trace ID to see full request lifecycle

### Debug Mode

Add `X-Debug: true` header for additional debugging information:

```http
X-Debug: true
X-API-Key: your_api_key
```

Response includes:
- Policy evaluation details
- Filter reasoning
- Performance metrics
- Upstream provider info

---

## Webhooks (Coming Soon)

### POST /webhooks

Register a webhook for quota alerts and policy violations.

**Request Body:**
```json
{
  "url": "https://your-server.com/webhook",
  "events": ["quota_alert", "policy_violation"],
  "secret": "webhook_secret_key"
}
```

---

## SDKs & Libraries

### Official SDKs
- Python: `pip install websearch-api-client`
- Node.js: `npm install @websearch/api-client`
- Go: `go get github.com/websearch/go-client`

### Community SDKs
- Ruby: [github.com/example/websearch-ruby](https://github.com)
- PHP: [github.com/example/websearch-php](https://github.com)

---

## OpenAPI Specification

Download the full OpenAPI 3.0 specification:

```bash
curl http://localhost:8000/openapi.json > websearch-api.json
```

Import into tools like Postman, Insomnia, or Swagger Editor.

---

## Support

- **API Issues:** Include trace ID in support requests
- **Feature Requests:** Submit via GitHub Issues
- **Security:** security@websearch-api.local
