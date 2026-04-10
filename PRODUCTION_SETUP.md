# Production Setup - Render Deployment

## Overview
This document contains critical steps for deploying FarmWise to production on Render with rate limiting protection for Gemini API.

## Current Status
✅ Production-safe pest detection implemented:
- Rate limiting (4 requests/60 seconds)
- Gemini API disabled on production by default
- Fallback to rule-based detection
- No more 429 errors for users

## Render Environment Variables (REQUIRED)

When deploying to Render, add these environment variables:

### Critical for Production Safety:
```
# AUTO-DETECTED from DEBUG setting, but you can override:
IS_PRODUCTION=True

# IMPORTANT: Disable Gemini on production to prevent rate limits
# This is the DEFAULT on production, but can be overridden if needed
DISABLE_GEMINI_ON_PRODUCTION=True
```

### Existing Variables (Keep as-is):
```
DEBUG=False
SECRET_KEY=<your-secret-key>
DATABASE_URL=<your-postgres-url>
REDIS_URL=<your-redis-url>
GEMINI_API_KEY=<your-api-key>  # Not used if DISABLE_GEMINI_ON_PRODUCTION=True
GROQ_API_KEY=<optional>
TOGETHER_API_KEY=<optional>
```

## How It Works

### On Production (Render):
1. Pest detection requests come in
2. Throttler checks if 4 requests already made in last 60 seconds
3. If throttled → Return fallback detection (rule-based)
4. If allowed AND Gemini disabled → Return rule-based detection
5. If allowed AND Gemini enabled → Call Gemini API

### On Development:
- `DEBUG=True` → `IS_PRODUCTION=False`
- `DISABLE_GEMINI_ON_PRODUCTION` defaults to `False`
- ✅ Gemini API works normally for testing

## Deployment Checklist

- [ ] Render environment variables configured
- [ ] Set `DEBUG=False` on Render
- [ ] Set `DISABLE_GEMINI_ON_PRODUCTION=True` on Render
- [ ] Deploy code to Render (git push or manual)
- [ ] Render auto-deploys and restarts
- [ ] Test pest detection (should show fallback results)
- [ ] Check Render logs for warnings about disabled Gemini
- [ ] Monitor for any 429 errors in logs

## Monitoring

### Expected Logs on Production:
```
[SETTINGS] ⚠️ PRODUCTION MODE: Gemini API disabled, using rule-based fallback only
[PEST_DETECTION] ⚠️ GEMINI DISABLED ON PRODUCTION - Using fallback only
[PEST_DETECTION] Production mode - Gemini disabled, using fallback
```

### Rate Limiting Logs (if enabled):
```
[THROTTLE] Rate limited: Too many pest detection requests, using fallback
```

## If You Want to Enable Gemini on Production

To test with Gemini on production (not recommended):
1. Set `DISABLE_GEMINI_ON_PRODUCTION=False` on Render
2. Gemini will still be protected by rate limiter (4 req/60 sec)
3. After 5 requests in one minute, rate limiter returns fallback
4. Users won't see error - fallback detection activates automatically

## Support

For issues:
1. Check Render logs: `Settings → Logs`
2. Look for rate limit errors (429)
3. Verify environment variables are set
4. Confirm `DEBUG=False`

## Files Modified

- `core/throttling.py` - NEW: Rate limiter implementation
- `core/views.py` - Added @throttle_pest_detection() decorator
- `core/services/pest_detection.py` - Added production flag checks
- `farmwise/settings.py` - Added IS_PRODUCTION and DISABLE_GEMINI_ON_PRODUCTION settings
