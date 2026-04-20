# Authentication

Learn about the different authentication methods supported by the WebSearch API.

## Supported Methods

The WebSearch API supports multiple authentication methods to integrate seamlessly with your existing infrastructure:

1. **API Keys** - Simple, secure keys for programmatic access
2. **OAuth 2.0** - Enterprise SSO with Okta, Entra ID (Azure AD)
3. **Client Certificates** - mTLS for highest security requirements

---

## API Keys

### How It Works

API keys are the simplest authentication method. Each key is tied to a specific client and quota tier.

**Key Format:**
```
GA_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx  (Admin keys, prefix: GA_)
UK_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx  (User keys, prefix: UK_)
```

### Request an API Key

1. Navigate to **Request API Key** in the admin dashboard
2. Fill in your details (name, email, organization, purpose)
3. Submit request
4. Administrator reviews and approves
5. Receive key via email

### Using API Keys

**Header Authentication:**
```bash
curl -X POST http://localhost:8000/api/v1/search \
  -H "X-API-Key: UK_your_api_key_here" \
  -H "Content-Type: application/json" \
  -d '{"query": "example search"}'
```

**Query Parameter (Not Recommended for Production):**
```bash
curl "http://localhost:8000/api/v1/search?api_key=UK_your_key&query=example"
```

### Key Security Best Practices

* ✅ **DO:** Store keys in environment variables
* ✅ **DO:** Rotate keys every 90 days
* ✅ **DO:** Use different keys for dev/staging/production
* ✅ **DO:** Implement key rotation without downtime
* ❌ **DON'T:** Commit keys to version control
* ❌ **DON'T:** Share keys via email or chat
* ❌ **DON'T:** Use the same key across multiple applications

---

## OAuth 2.0

### Okta Integration

**Configuration:**
```bash
# .env
OKTA_DOMAIN=your-domain.okta.com
OKTA_CLIENT_ID=your_client_id
OKTA_CLIENT_SECRET=your_client_secret
OKTA_REDIRECT_URI=http://localhost:8000/auth/okta/callback
```

**Authentication Flow:**

1. User initiates login
2. Redirect to Okta authorization endpoint
3. User authenticates with Okta credentials
4. Okta redirects back with authorization code
5. Exchange code for access token
6. Use access token for API requests

**Example Request:**
```bash
curl -X POST http://localhost:8000/api/v1/search \
  -H "Authorization: Bearer eyJhbGc...your_okta_token" \
  -H "Content-Type: application/json" \
  -d '{"query": "example search"}'
```

### Azure AD / Entra ID

**Configuration:**
```bash
# .env
AZURE_TENANT_ID=your_tenant_id
AZURE_CLIENT_ID=your_client_id
AZURE_CLIENT_SECRET=your_client_secret
AZURE_REDIRECT_URI=http://localhost:8000/auth/azure/callback
```

**Authentication Flow:**

1. User initiates login
2. Redirect to Microsoft identity platform
3. User signs in with Microsoft credentials
4. Microsoft redirects with authorization code
5. Exchange code for access token
6. Use access token for API requests

---

## Client Certificates (mTLS)

### How It Works

Mutual TLS (mTLS) provides the highest level of security by requiring both client and server to authenticate using X.509 certificates.

**Setup Steps:**

1. **Generate CA Certificate** (if you don't have one)
2. **Generate Client Certificate** signed by CA
3. **Register Client Certificate** in WebSearch API
4. **Configure Client** to use certificate

### Generate Certificates

```bash
# Generate CA
openssl genrsa -out ca.key 4096
openssl req -new -x509 -days 365 -key ca.key -out ca.crt \
  -subj "/C=US/ST=State/L=City/O=Organization/CN=WebSearch CA"

# Generate client key
openssl genrsa -out client.key 2048

# Generate CSR
openssl req -new -key client.key -out client.csr \
  -subj "/C=US/ST=State/L=City/O=Organization/CN=client-name"

# Sign with CA
openssl x509 -req -days 365 -in client.csr \
  -CA ca.crt -CAkey ca.key -set_serial 01 -out client.crt
```

### Register Certificate

```bash
# Register client certificate with API
curl -X POST http://localhost:8000/api/v1/admin/clients/certificates \
  -H "X-API-Key: ADMIN_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "My Application",
    "certificate": "-----BEGIN CERTIFICATE-----\n...\n-----END CERTIFICATE-----"
  }'
```

### Use Certificate

```bash
curl -X POST https://api.example.com/api/v1/search \
  --cert client.crt \
  --key client.key \
  --cacert ca.crt \
  -H "Content-Type: application/json" \
  -d '{"query": "example search"}'
```

**Python Example:**
```python
import requests

response = requests.post(
    'https://api.example.com/api/v1/search',
    cert=('client.crt', 'client.key'),
    verify='ca.crt',
    json={'query': 'example search'}
)
```

---

## Token Lifecycle

### API Keys
- **Validity:** Indefinite (until revoked)
- **Rotation:** Recommended every 90 days
- **Revocation:** Instant via admin dashboard

### OAuth Tokens
- **Validity:** 1 hour (default)
- **Refresh:** Automatic with refresh token
- **Expiration:** 24 hours (refresh token)

### Client Certificates
- **Validity:** Set at creation (typically 1 year)
- **Renewal:** Must generate new certificate before expiration
- **Revocation:** Instant via certificate revocation list (CRL)

---

## Rate Limiting by Auth Method

| Method | Default Tier | Requests/Min | Requests/Day |
|--------|--------------|--------------|--------------|
| API Key (Free) | Free | 10 | 1000 |
| API Key (Standard) | Standard | 60 | 5000 |
| OAuth 2.0 | Standard | 60 | 5000 |
| Client Certificate | Premium | 300 | 50000 |

---

## Multi-Factor Authentication

### Enable MFA for API Keys

For enhanced security, require MFA when requesting new API keys:

1. Navigate to **Settings → Security**
2. Enable **Require MFA for API Key Requests**
3. Users must verify email + TOTP code to receive keys

### OAuth MFA

MFA is enforced by your identity provider (Okta, Azure AD). Configure MFA policies in your IdP.

---

## Service Accounts

Create service accounts for machine-to-machine authentication:

```bash
curl -X POST http://localhost:8000/api/v1/admin/service-accounts \
  -H "X-API-Key: ADMIN_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "CI/CD Pipeline",
    "description": "Automated testing service",
    "quota_tier": "standard",
    "permissions": ["search", "usage"]
  }'
```

Response includes API key for the service account.

---

## Troubleshooting

### Invalid API Key

**Error:** `401 Unauthorized: Invalid API key`

**Solutions:**
- Verify key hasn't been revoked
- Check key format (must include prefix: UK_ or GA_)
- Ensure header name is exactly `X-API-Key`

### OAuth Token Expired

**Error:** `401 Unauthorized: Token expired`

**Solutions:**
- Refresh access token using refresh token
- Re-authenticate if refresh token also expired

### Certificate Validation Failed

**Error:** `403 Forbidden: Client certificate invalid`

**Solutions:**
- Verify certificate hasn't expired
- Ensure certificate is signed by registered CA
- Check CN matches registered client name

---

## Next Steps

- Review [API Reference](../api/reference.md) for endpoint details
- Learn about [Best Practices](best-practices.md) for production use
- Set up [Monitoring](../admin/monitoring.md) to track authentication events
