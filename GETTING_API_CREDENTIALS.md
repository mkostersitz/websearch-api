# How to Get Google Custom Search API Credentials

This guide will walk you through obtaining the credentials needed for the WebSearch API to perform Google searches.

## What You Need

1. **Google Custom Search API Key** - Authenticates your API requests
2. **Custom Search Engine ID (CX)** - Identifies your search engine configuration

**Time Required:** ~10 minutes  
**Cost:** Free tier available (100 searches/day)

---

## Step 1: Create Google Cloud Project

### 1.1 Go to Google Cloud Console
Visit: https://console.cloud.google.com/

### 1.2 Create a New Project (or select existing)
1. Click the project dropdown at the top
2. Click "NEW PROJECT"
3. Enter project name: `WebSearch-API` (or your preference)
4. Click "CREATE"
5. Wait for project creation (takes ~30 seconds)
6. Select your new project from the dropdown

---

## Step 2: Enable Custom Search API

### 2.1 Navigate to APIs & Services
1. In Google Cloud Console, click the hamburger menu (☰) top-left
2. Select **"APIs & Services"** → **"Library"**
3. Or visit directly: https://console.cloud.google.com/apis/library

### 2.2 Enable the API
1. In the search box, type: `Custom Search API`
2. Click on **"Custom Search API"** in results
3. Click the blue **"ENABLE"** button
4. Wait for activation (~10 seconds)

---

## Step 3: Create API Key

### 3.1 Go to Credentials
1. Click **"APIs & Services"** → **"Credentials"** from left menu
2. Or visit: https://console.cloud.google.com/apis/credentials

### 3.2 Create the API Key
1. Click **"+ CREATE CREDENTIALS"** at the top
2. Select **"API key"** from dropdown
3. A dialog will appear with your new API key

### 3.3 Copy Your API Key
```
Example: AIzaSyD1234567890abcdefghijklmnopqrstuv
```
⚠️ **Save this immediately** - you'll need it for your .env file

### 3.4 Restrict the API Key (Recommended for Security)
1. Click **"EDIT API KEY"** in the dialog (or click the key name later)
2. Under "API restrictions":
   - Select **"Restrict key"**
   - Choose **"Custom Search API"** from the dropdown
3. Under "Application restrictions" (optional but recommended):
   - Choose **"IP addresses"** to restrict to your server IPs
   - Or **"HTTP referrers"** if using from browser
4. Click **"SAVE"**

---

## Step 4: Create Custom Search Engine

### 4.1 Go to Programmable Search Engine
Visit: https://programmablesearchengine.google.com/

### 4.2 Create New Search Engine
1. Click **"Add"** or **"Get Started"**
2. If you don't see these, click **"Control Panel"** first

### 4.3 Configure Your Search Engine

**Search engine name:**
```
WebSearch API Search Engine
```

**What to search:**
- **Option A - Search the entire web:** 
  - Select "Search the entire web"
  - ✅ This is what you want for an AI agent search API
  
- **Option B - Search specific sites:**
  - Enter specific websites to search
  - Example: `wikipedia.org`, `github.com`
  - You can always change this later

**Search features:**
- ✅ Enable "Image search" (if you want image results)
- ✅ Enable "SafeSearch" (recommended)

### 4.4 Create the Search Engine
1. Click **"Create"**
2. You'll see a confirmation screen

### 4.5 Get Your Search Engine ID (CX)
1. On the confirmation screen, or go back to **Control Panel**
2. Click on your search engine name
3. In the left sidebar, click **"Overview"** or **"Setup"**
4. Look for **"Search engine ID"** - it looks like:
```
Example: 0123456789abcdef0:abcd1234567
```
Or sometimes just:
```
Example: 0123456789abcdef0
```
5. Click the **copy icon** next to it

---

## Step 5: Configure Your WebSearch API

### 5.1 Edit Your .env File
```bash
cd /Users/mikek/repos/websearch-api
nano .env  # or use your preferred editor
```

### 5.2 Add Your Credentials
Find these lines and update them:
```bash
# Search Providers
GOOGLE_API_KEY=AIzaSyD1234567890abcdefghijklmnopqrstuv
GOOGLE_SEARCH_ENGINE_ID=0123456789abcdef0:abcd1234567
BING_API_KEY=
```

Replace with your actual values from Steps 3 and 4.

### 5.3 Save and Restart
```bash
# Save the file (Ctrl+O, Enter, Ctrl+X in nano)

# Restart the API
docker-compose restart websearch-api
# Or if running locally:
poetry run uvicorn src.main:app --reload
```

---

## Step 6: Test Your Setup

### 6.1 Test with curl
```bash
curl -X POST http://localhost:8000/api/v1/search \
  -H "X-API-Key: GA_Incg4zEhpK-65G6PwL499t2kXvH2Cs-hWf6udtZU" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "artificial intelligence",
    "max_results": 5
  }' | jq .
```

### 6.2 Verify Results
You should see:
- ✅ `"total_results": 5` (or more)
- ✅ `"provider": "google"`
- ✅ `"results"` array with actual search results
- ✅ Each result has `title`, `url`, `snippet`

---

## Troubleshooting

### Error: "API key not valid"
- Double-check you copied the entire API key
- Verify Custom Search API is enabled
- Check API key restrictions (might be blocking localhost)

### Error: "Invalid request"
- Verify your Search Engine ID (CX) is correct
- Make sure there are no extra spaces in .env file

### Getting Empty Results
- Check that your Custom Search Engine is set to "Search the entire web"
- Verify both credentials are in .env and API is restarted

### API Key Quota Exceeded
Free tier limits:
- **100 queries/day** for free
- For more, you need to enable billing:
  - Go to: https://console.cloud.google.com/billing
  - Pricing: $5 per 1,000 queries (after free tier)

---

## Free Tier Limits

### Google Custom Search API
- **Free:** 100 searches/day
- **Paid:** $5 per 1,000 queries
- **Rate Limit:** 10 queries/second

### Pricing Calculator
For 10,000 searches/day:
- First 100: Free
- Remaining 9,900: $49.50/day
- Monthly: ~$1,485

💡 **Tip:** Consider using multiple providers (Google + Bing) for better coverage and failover!

---

## Getting Bing Search API (Alternative/Backup)

For redundancy, also configure Bing:

### 1. Go to Azure Portal
Visit: https://portal.azure.com/

### 2. Create Bing Search Resource
1. Search for "Bing Search" in the search bar
2. Select **"Bing Search v7"**
3. Click **"Create"**
4. Fill in details:
   - Resource group: Create new or select existing
   - Name: `websearch-bing-api`
   - Pricing tier: **F1 (Free)** - 3 calls/second, 1,000 calls/month
5. Click **"Review + Create"** → **"Create"**

### 3. Get API Key
1. Go to your new Bing Search resource
2. Click **"Keys and Endpoint"** in left menu
3. Copy **KEY 1**
4. Add to .env:
```bash
BING_API_KEY=your_bing_key_here
```

### Bing Free Tier
- **Free (F1):** 1,000 calls/month
- **Paid (S1):** $7 per 1,000 transactions

---

## Quick Reference

### Files to Edit
```bash
/Users/mikek/repos/websearch-api/.env
```

### Environment Variables
```bash
GOOGLE_API_KEY=<your-api-key>
GOOGLE_SEARCH_ENGINE_ID=<your-cx-id>
BING_API_KEY=<your-bing-key>
```

### Restart Command
```bash
# Docker
docker-compose restart websearch-api

# Local
poetry run uvicorn src.main:app --reload
```

### Test Command
```bash
curl -X POST http://localhost:8000/api/v1/search \
  -H "X-API-Key: GA_Incg4zEhpK-65G6PwL499t2kXvH2Cs-hWf6udtZU" \
  -H "Content-Type: application/json" \
  -d '{"query": "test", "max_results": 3}' | jq .
```

---

## Useful Links

- **Google Cloud Console:** https://console.cloud.google.com/
- **Custom Search Engine:** https://programmablesearchengine.google.com/
- **API Credentials:** https://console.cloud.google.com/apis/credentials
- **Custom Search API Docs:** https://developers.google.com/custom-search/v1/overview
- **Bing Search API:** https://portal.azure.com/

---

## Security Best Practices

1. ✅ **Restrict API keys** to specific APIs
2. ✅ **Restrict by IP** if possible (production servers)
3. ✅ **Rotate keys** periodically
4. ✅ **Monitor usage** in Google Cloud Console
5. ✅ **Set up billing alerts** to avoid unexpected charges
6. ❌ **Never commit** API keys to git (use .env only)

---

Need help? Check the logs:
```bash
# View API logs
docker-compose logs -f websearch-api

# Or if running locally
# Check terminal output
```

**Once configured, your WebSearch API will return real search results!** 🎉
