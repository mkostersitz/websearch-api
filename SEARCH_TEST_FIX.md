# Search Test Fix

## Issue
The `./run.sh test` command was returning a 422 error:
```
[ERROR] Search failed (HTTP 422)
{"detail":[{"type":"missing","loc":["query","args"],"msg":"Field required"...
```

## Root Cause
The `@trace_function` decorator in `/src/middleware/tracing.py` was not using `@wraps(func)` from functools. This caused FastAPI to lose the original function signature when inspecting decorated endpoints for dependency injection.

Without `@wraps`, FastAPI couldn't properly match the request body to the `SearchRequest` model and was instead seeing generic `*args, **kwargs` parameters.

## Fix
Updated `/src/middleware/tracing.py`:

```python
from functools import wraps
import asyncio

if asyncio.iscoroutinefunction(func):
    @wraps(func)  # <-- Added this
    async def async_wrapper(*args, **kwargs):
        # ... tracing code ...
    return async_wrapper
else:
    @wraps(func)  # <-- Added this  
    def sync_wrapper(*args, **kwargs):
        # ... tracing code ...
    return sync_wrapper
```

The `@wraps(func)` decorator:
1. Preserves the original function's `__name__`, `__doc__`, and `__annotations__`
2. Maintains the function signature for FastAPI's dependency injection
3. Allows Pydantic to properly validate request bodies

## Testing

### Test with run.sh
```bash
# Pretty formatted output
./run.sh test --pretty

# JSON output (includes status messages)
./run.sh test --json

# Both now work correctly! ✅
```

### Direct API test
```bash
curl -X POST http://localhost:8000/api/v1/search \
  -H "X-API-Key: GA_Incg4zEhpK-65G6PwL499t2kXvH2Cs-hWf6udtZU" \
  -H "Content-Type: application/json" \
  -d '{"query": "OpenTelemetry", "max_results": 5}'

# Returns proper search results ✅
```

## Verification

✅ Search endpoint working  
✅ OpenTelemetry tracing preserved  
✅ FastAPI dependency injection working  
✅ Pydantic validation working  
✅ `./run.sh test --pretty` displays formatted results  
✅ `./run.sh test --json` displays JSON results  

## Sample Output

```
════════════════════════════════════════════════════════════
Search Results for: OpenTelemetry
════════════════════════════════════════════════════════════

Provider: duckduckgo
Total Results: 5
Response Time: 1144.21ms

────────────────────────────────────────────────────────────

[1] OpenTelemetry
    URL: https://en.wikipedia.org/wiki/OpenTelemetry
    The Cloud Native Computing Foundation (CNCF) is a subsidiary...

[2] OpenTelemetry
    URL: https://grokipedia.com/page/OpenTelemetry
    OpenTelemetry (often abbreviated as OTel) is an open-source...

[3] OpenTelemetry
    URL: https://opentelemetry.io/
    OpenTelemetry is an open source observability framework...

[4] OpenTelemetry - CNCF · GitHub
    URL: https://github.com/open-telemetry
    OpenTelemetry is a CNCF incubating project that provides...

[5] OpenTelemetry - CNCF
    URL: https://www.cncf.io/projects/opentelemetry/
    OpenTelemetry OpenTelemetry community content OpenTelemetry...

────────────────────────────────────────────────────────────
Rate Limit: 64/60 remaining
Monthly Quota: 299,975/300,000 remaining
════════════════════════════════════════════════════════════
```

## Related Files

- `/src/middleware/tracing.py` - Fixed trace_function decorator
- `/src/api/routes/search.py` - Uses @trace_function decorator
- `/run.sh` - Test command with --pretty and --json flags

## Lesson Learned

When creating decorators for FastAPI endpoints:
1. **Always use `@wraps(func)`** to preserve function metadata
2. Test with FastAPI's dependency injection (query params, body models, etc.)
3. OpenTelemetry decorators need special care with async functions
4. Pydantic validation depends on proper function signatures

## Status

✅ **FIXED** - All search functionality working correctly
