# Getting Started

This guide will help you start using the WebSearch API in minutes.

## Overview

The WebSearch API provides secure, traceable web search capabilities for AI agents and applications. All searches are governed by enterprise policies, filtered for safety, and fully auditable.

## Step 1: Obtain an API Key

### Request Access
1. Navigate to the Admin Dashboard
2. Click **Request API Key** in the navigation menu
3. Fill in your details:
   - **Name:** Your full name
   - **Email:** Your email address
   - **Organization:** Your company or team name
   - **Purpose:** Brief description of your use case
4. Submit your request

### Receive Your Key
- An administrator will review and approve your request
- You'll receive your API key via email
- **Important:** Store your API key securely - it won't be shown again

## Step 2: Test Your Connection

### Using cURL
```bash
curl -X POST http://localhost:8000/api/v1/search \
  -H "X-API-Key: YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "latest developments in artificial intelligence",
    "max_results": 5
  }'
```

### Expected Response
```json
{
  "query": "latest developments in artificial intelligence",
  "results": [
    {
      "title": "AI Breakthrough...",
      "url": "https://example.com/ai-news",
      "snippet": "Recent advances in...",
      "relevance_score": 0.95
    }
  ],
  "total_results": 5,
  "search_time_ms": 342,
  "trace_id": "abc123..."
}
```

## Step 3: Understand Your Limits

### Check Your Quota
```bash
curl -X GET http://localhost:8000/api/v1/quota \
  -H "X-API-Key: YOUR_API_KEY"
```

Response:
```json
{
  "requests_per_minute": 60,
  "requests_per_day": 5000,
  "remaining_today": 4999,
  "reset_time": "2026-04-20T00:00:00Z"
}
```

### Quota Limits
- **Default:** 60 requests/minute, 5000 requests/day
- **Rate Limited:** HTTP 429 when quota exceeded
- **Contact Admin:** Request quota increases if needed

## Step 4: Implement Error Handling

### Handle Common Errors

```python
import requests

def search_web(query, api_key):
    try:
        response = requests.post(
            'http://localhost:8000/api/v1/search',
            headers={'X-API-Key': api_key},
            json={'query': query, 'max_results': 10}
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 401:
            print("Invalid API key")
        elif e.response.status_code == 403:
            print("Search blocked by policy")
        elif e.response.status_code == 429:
            print("Rate limit exceeded")
        else:
            print(f"Error: {e}")
    except requests.exceptions.RequestException as e:
        print(f"Connection error: {e}")
```

### Error Codes
- **400:** Bad request (invalid query format)
- **401:** Unauthorized (invalid or missing API key)
- **403:** Forbidden (blocked by search policy)
- **429:** Too many requests (quota exceeded)
- **500:** Internal server error
- **503:** Service unavailable

## Step 5: Advanced Features

### Filter by Domain
```json
{
  "query": "machine learning tutorials",
  "max_results": 10,
  "filters": {
    "domains": ["edu", "org"],
    "exclude_domains": ["example.com"]
  }
}
```

### Set Safe Search Level
```json
{
  "query": "health information",
  "safe_search": "strict"
}
```

Options: `off`, `moderate`, `strict`

### Request Specific Content Types
```json
{
  "query": "quarterly report",
  "content_types": ["pdf", "doc"]
}
```

## Best Practices

### 1. Cache Results
- Store search results locally when appropriate
- Reduces API calls and improves response times
- Respect cache TTL (typically 1 hour for search results)

### 2. Use Specific Queries
- **Good:** "OpenAI GPT-4 release date and features"
- **Poor:** "AI stuff"
- Specific queries return better results and are less likely to be blocked

### 3. Handle Tracing
- Every response includes a `trace_id`
- Save trace IDs for debugging and support requests
- View traces in Jaeger: `http://localhost:16686`

### 4. Implement Retries
- Use exponential backoff for 429 (rate limit) errors
- Don't retry 403 (policy blocked) - query violates policy
- Max 3 retries for 500/503 errors

### 5. Monitor Your Usage
```bash
# Check recent requests
curl -X GET http://localhost:8000/api/v1/usage \
  -H "X-API-Key: YOUR_API_KEY"
```

## Example Integration

### Python
```python
from typing import Optional
import requests
import time

class WebSearchClient:
    def __init__(self, api_key: str, base_url: str = "http://localhost:8000/api/v1"):
        self.api_key = api_key
        self.base_url = base_url
    
    def search(self, query: str, max_results: int = 10, retries: int = 3) -> Optional[dict]:
        """Search with automatic retry logic."""
        for attempt in range(retries):
            try:
                response = requests.post(
                    f"{self.base_url}/search",
                    headers={"X-API-Key": self.api_key},
                    json={"query": query, "max_results": max_results},
                    timeout=30
                )
                
                if response.status_code == 429:
                    # Rate limited - exponential backoff
                    wait_time = 2 ** attempt
                    time.sleep(wait_time)
                    continue
                
                response.raise_for_status()
                return response.json()
                
            except requests.exceptions.RequestException as e:
                if attempt == retries - 1:
                    raise
                time.sleep(1)
        
        return None
    
    def check_quota(self) -> dict:
        """Check remaining quota."""
        response = requests.get(
            f"{self.base_url}/quota",
            headers={"X-API-Key": self.api_key}
        )
        response.raise_for_status()
        return response.json()

# Usage
client = WebSearchClient(api_key="YOUR_API_KEY")
results = client.search("climate change research 2026")
print(f"Found {results['total_results']} results")
```

### JavaScript/Node.js
```javascript
const axios = require('axios');

class WebSearchClient {
  constructor(apiKey, baseUrl = 'http://localhost:8000/api/v1') {
    this.apiKey = apiKey;
    this.baseUrl = baseUrl;
  }

  async search(query, maxResults = 10) {
    try {
      const response = await axios.post(`${this.baseUrl}/search`, {
        query,
        max_results: maxResults
      }, {
        headers: { 'X-API-Key': this.apiKey },
        timeout: 30000
      });
      
      return response.data;
    } catch (error) {
      if (error.response?.status === 403) {
        throw new Error('Search blocked by policy');
      }
      if (error.response?.status === 429) {
        throw new Error('Rate limit exceeded');
      }
      throw error;
    }
  }

  async checkQuota() {
    const response = await axios.get(`${this.baseUrl}/quota`, {
      headers: { 'X-API-Key': this.apiKey }
    });
    return response.data;
  }
}

// Usage
const client = new WebSearchClient('YOUR_API_KEY');
const results = await client.search('quantum computing breakthroughs');
console.log(`Found ${results.total_results} results`);
```

## Next Steps

- Read the [API Reference](../api/reference.md) for complete endpoint documentation
- Learn about [Authentication Methods](authentication.md)
- Review [Best Practices](best-practices.md) for production use
- Check [Search Policies](../guides/search-policies.md) to understand what's filtered

## Need Help?

- **Technical Issues:** Check the [Troubleshooting Guide](../guides/troubleshooting.md)
- **Policy Questions:** Review [Search Policies](../guides/search-policies.md)
- **Quota Increases:** Contact your administrator
- **Bug Reports:** Include your trace ID for faster resolution
