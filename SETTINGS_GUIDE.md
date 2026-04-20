# Settings & Configuration Guide

## Overview

The Admin Dashboard now includes a comprehensive Settings page for configuring system-wide policies, parental controls, observability integrations, and OpenTelemetry settings.

## Features

### 1. Pinnable Sidebar

The navigation sidebar can now be pinned or unpinned:

- **Pin Icon**: Click the pin icon in the sidebar header to toggle
- **Persistent**: Your preference is saved in localStorage
- **Desktop Only**: Feature is available on desktop (MD breakpoint and up)
- **Mobile**: On mobile devices, the sidebar behaves as a temporary overlay

**Benefits:**
- More screen space when unpinned
- Quick access when pinned
- Smooth transitions with Material-UI animations

### 2. OpenTelemetry Configuration

Configure the OTEL Collector endpoint for distributed tracing:

- **Endpoint URL**: Set the gRPC endpoint (default: `http://localhost:5317`)
- **Note**: Changes require service restart to take effect
- **Format**: `http://host:port` or `https://host:port`

**Example:**
```
http://localhost:5317       # Local development
http://otel-collector:4317  # Docker environment
https://otel.example.com    # Production
```

### 3. Enterprise Search Policies

Control content filtering for all search results:

#### Policy Levels

**Strict** (Maximum Filtering)
- Blocks: adult, explicit, violence, gambling, drugs, weapons, hate speech
- Best for: Educational institutions, government agencies
- Use case: Environments requiring maximum content safety

**Moderate** (Recommended - Balanced Filtering)
- Blocks: adult, explicit, violence, gambling
- Best for: General enterprise use
- Use case: Professional workplace environments

**Open** (Minimal Filtering)
- Blocks: adult, explicit content only
- Best for: Research environments, unrestricted access
- Use case: Academic research, content analysis

#### Configuration

```json
{
  "search_policy": {
    "level": "moderate",
    "enabled": true,
    "block_keywords": ["adult", "explicit", "violence", "gambling"]
  }
}
```

**Blocked Keywords**: Automatically updated based on policy level
**Enforcement**: Applied to all API clients unless explicitly overridden

### 4. Parental Controls

Age-appropriate content filtering:

#### Enable/Disable Toggle
Turn parental controls on or off system-wide

#### Age Restrictions
- **13+ (Teen)**: Basic content filtering
- **16+ (Young Adult)**: Moderate content filtering
- **18+ (Adult)**: Strict content filtering

#### Content Filters

Individual toggles for:
- ✅ **Block Adult Content**: Explicit sexual content
- ✅ **Block Violence & Gore**: Violent or disturbing content
- ✅ **Block Gambling**: Gaming and betting content (auto-enabled with parental controls)
- ✅ **Block Drugs**: Drug-related content (auto-enabled with parental controls)

**Note**: When parental controls are enabled, gambling and drug filters are automatically activated regardless of individual toggle states.

#### Example Configuration

```json
{
  "parental_controls": {
    "enabled": true,
    "age_restriction": 18,
    "block_adult_content": true,
    "block_violence": true,
    "block_gambling": true,
    "block_drugs": true
  }
}
```

### 5. Observability Integrations

Quick access to monitoring and observability tools:

#### Grafana
- **URL Configuration**: Set Grafana dashboard URL
- **Default**: `http://localhost:3002`
- **Quick Launch**: Click "Open Grafana" button
- **Purpose**: Metrics visualization and dashboards
- **Credentials**: admin / admin (default)

#### Prometheus
- **URL Configuration**: Set Prometheus server URL
- **Default**: `http://localhost:9091`
- **Quick Launch**: Click "Open Prometheus" button
- **Purpose**: Metrics collection and storage
- **Query**: Access PromQL query interface

#### Jaeger
- **URL Configuration**: Set Jaeger UI URL
- **Default**: `http://localhost:17686`
- **Quick Launch**: Click "Open Jaeger" button
- **Purpose**: Distributed tracing and monitoring
- **Features**: Trace search, service dependencies, performance analysis

## API Endpoints

### GET /api/v1/admin/settings

Get current system settings.

**Authentication**: Admin API Key required

**Response:**
```json
{
  "otel_endpoint": "http://localhost:5317",
  "search_policy": {
    "level": "moderate",
    "enabled": true,
    "block_keywords": ["adult", "explicit", "violence", "gambling"]
  },
  "parental_controls": {
    "enabled": false,
    "age_restriction": 13,
    "block_adult_content": true,
    "block_violence": true,
    "block_gambling": false,
    "block_drugs": false
  },
  "integrations": {
    "grafana_url": "http://localhost:3002",
    "prometheus_url": "http://localhost:9091",
    "jaeger_url": "http://localhost:17686"
  }
}
```

### PUT /api/v1/admin/settings

Update system settings.

**Authentication**: Admin API Key required

**Request Body:**
```json
{
  "otel_endpoint": "http://localhost:5317",
  "search_policy": {
    "level": "strict",
    "enabled": true,
    "block_keywords": ["adult", "explicit", "violence", "gambling", "drugs", "weapons", "hate"]
  },
  "parental_controls": {
    "enabled": true,
    "age_restriction": 18,
    "block_adult_content": true,
    "block_violence": true,
    "block_gambling": true,
    "block_drugs": true
  },
  "integrations": {
    "grafana_url": "http://localhost:3002",
    "prometheus_url": "http://localhost:9091",
    "jaeger_url": "http://localhost:17686"
  }
}
```

**Validation:**
- `search_policy.level`: Must be "strict", "moderate", or "open"
- `parental_controls.age_restriction`: Must be 13, 16, or 18
- `otel_endpoint`: Valid URL format

**Audit Logging**: All settings changes are logged to audit trail

## Testing

### From Command Line

```bash
# Get current settings
curl -X GET "http://localhost:8000/api/v1/admin/settings" \
  -H "X-API-Key: GA_Incg4zEhpK-65G6PwL499t2kXvH2Cs-hWf6udtZU"

# Update settings
curl -X PUT "http://localhost:8000/api/v1/admin/settings" \
  -H "X-API-Key: GA_Incg4zEhpK-65G6PwL499t2kXvH2Cs-hWf6udtZU" \
  -H "Content-Type: application/json" \
  -d @settings.json
```

### From Dashboard

1. Navigate to **Settings** page (gear icon in sidebar)
2. Modify any configuration section
3. Click **Save Changes**
4. Check for success notification

## Storage

Settings are stored in MongoDB:
- **Collection**: `system_settings`
- **Document ID**: `system`
- **Persistence**: Survives restarts
- **Defaults**: Loaded automatically if no settings exist

## Security

- **Admin Only**: All settings endpoints require admin role
- **Audit Trail**: All changes logged with timestamp and user
- **Validation**: Server-side validation of all inputs
- **API Key**: Must include admin API key in X-API-Key header

## Best Practices

1. **Start with Moderate**: Use moderate policy for general enterprise use
2. **Test Changes**: Use dev/staging environment before production
3. **Monitor Impact**: Check search logs after policy changes
4. **Document Decisions**: Note reasons for policy level choices
5. **Regular Review**: Periodically review parental control settings
6. **Coordinate Restarts**: Plan OTEL endpoint changes during maintenance windows

## Troubleshooting

### Settings not saving
- Verify admin API key is valid
- Check MongoDB connection
- Review server logs for validation errors

### OTEL changes not applied
- Settings require service restart
- Verify endpoint URL format
- Check network connectivity to OTEL collector

### Policy not filtering results
- Ensure policy is enabled
- Verify keywords are appropriate for level
- Check search logs for filter application

### Integration links not working
- Verify service URLs are correct
- Ensure services are running
- Check browser console for errors

## Future Enhancements

Potential additions:
- Custom keyword lists per policy level
- Client-specific policy overrides
- Scheduled policy changes
- Policy testing/preview mode
- Import/export settings
- Settings versioning and rollback
- Notification webhooks for settings changes
