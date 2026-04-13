# RENDER_ENV_SETUP_QUICK_REFERENCE.md

# ⚡ Render Environment Variables - Quick Setup

**Time Required:** 5 minutes  
**Complexity:** Easy  
**Status:** Required for API fixes

---

## 🚀 COPY-PASTE ENVIRONMENT VARIABLES

### For Render Dashboard:
Go to: **Web Service → Settings → Environment**

Then copy-paste ONE of the following configurations:

---

## ✅ OPTION 1: Use Google Gemini (RECOMMENDED)

**Why:** Free, powerful, specifically trained on agricultural images

```
DEBUG=false
SECURE_SSL_REDIRECT=true
SESSION_COOKIE_SECURE=true
CSRF_COOKIE_SECURE=true
SECURE_HSTS_SECONDS=31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS=true
SECURE_HSTS_PRELOAD=true

GEMINI_API_KEY=<PASTE_YOUR_KEY_HERE>
GROQ_API_KEY=
USE_OPENAI=false
OPENAI_API_KEY=

WEATHER_CACHE_TIMEOUT=3600
PYTHONUNBUFFERED=1
```

**How to Get Gemini Key (3 steps):**

1. Go to https://ai.google.dev/
2. Click "Get API Key" → Create new project
3. Copy the key and paste above where it says `<PASTE_YOUR_KEY_HERE>`

---

## ✅ OPTION 2: Use Groq (FAST ALTERNATIVE)

**Why:** Fast, unlimited free tier, good backup

```
DEBUG=false
SECURE_SSL_REDIRECT=true
SESSION_COOKIE_SECURE=true
CSRF_COOKIE_SECURE=true
SECURE_HSTS_SECONDS=31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS=true
SECURE_HSTS_PRELOAD=true

GEMINI_API_KEY=
GROQ_API_KEY=<PASTE_YOUR_KEY_HERE>
USE_OPENAI=false
OPENAI_API_KEY=

WEATHER_CACHE_TIMEOUT=3600
PYTHONUNBUFFERED=1
```

**How to Get Groq Key (3 steps):**

1. Go to https://console.groq.com/
2. Sign up → Go to API Keys
3. Create new key and paste above where it says `<PASTE_YOUR_KEY_HERE>`

---

## ✅ OPTION 3: Use BOTH (RECOMMENDED FOR PRODUCTION)

**Why:** Automatic fallback if one API limits out

```
DEBUG=false
SECURE_SSL_REDIRECT=true
SESSION_COOKIE_SECURE=true
CSRF_COOKIE_SECURE=true
SECURE_HSTS_SECONDS=31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS=true
SECURE_HSTS_PRELOAD=true

GEMINI_API_KEY=<PASTE_GEMINI_KEY>
GROQ_API_KEY=<PASTE_GROQ_KEY>
USE_OPENAI=false
OPENAI_API_KEY=

WEATHER_CACHE_TIMEOUT=3600
PYTHONUNBUFFERED=1
```

---

## 📋 STEP-BY-STEP SETUP PROCESS

### Step 1: Get Your API Keys

**Get Gemini Key:**
```
1. Open https://ai.google.dev/
2. Click "Get API Key" button
3. Select "Create API key in new project"
4. Copy the key (looks like: AIzaSy...)
5. Save it temporarily
```

**Get Groq Key (Optional):**
```
1. Open https://console.groq.com/
2. Sign up with email/Google
3. Go to API Keys section
4. Click "Create New API Key"
5. Copy the key (looks like: gsk_...)
6. Save it temporarily
```

### Step 2: Add to Render

```
1. Go to your Render dashboard
2. Click on your Web Service
3. Go to "Settings" tab
4. Scroll to "Environment"
5. Click "Add Environment Variables"
6. Copy the configuration from OPTION 1, 2, or 3 above
7. Paste it into the environment section
8. Click "Save Changes"
```

### Step 3: Redeploy

```
1. Go to "Deploy" tab (or wait for auto-deploy)
2. Click "Manual Deploy"
3. Select "Deploy latest commit"
4. Wait for deployment (5-10 minutes)
5. Check logs for errors
```

### Step 4: Verify

```
1. Go to your FarmWise dashboard
2. Check Weather widget - should show temperature
3. Upload a crop image for pest detection
4. Should return analysis (not error)
```

---

## 🔑 ENVIRONMENT VARIABLES EXPLAINED

| Variable | Required | What It Does | Default |
|----------|----------|-------------|---------|
| `DEBUG` | No | Enables/disables debug mode | `false` |
| `GEMINI_API_KEY` | ❌ (one required) | Google Gemini API key for pest detection | Empty |
| `GROQ_API_KEY` | ❌ (one required) | Groq API key for pest detection | Empty |
| `USE_OPENAI` | No | Whether to use OpenAI (not recommended) | `false` |
| `OPENAI_API_KEY` | No | OpenAI key (leave empty) | Empty |
| `SECURE_SSL_REDIRECT` | No | Force HTTPS | `true` |
| `SESSION_COOKIE_SECURE` | No | Secure session cookies | `true` |
| `WEATHER_CACHE_TIMEOUT` | No | Cache weather for X seconds | `3600` |

---

## ✅ VERIFICATION CHECKLIST

After setup, verify everything works:

```
□ Environment variables added to Render
□ Redeployed successfully (green checkmark in Deploy tab)
□ No errors in logs (check browser console)
□ Weather widget shows actual temperature (not "N/A")
□ Test farm upload works
□ Pest detection returns analysis (not error message)
□ Check Render logs for success messages
```

---

## 🆘 TROUBLESHOOTING QUICK FIXES

### "Weather showing N/A"
```
Open-Meteo doesn't require API key - this means API timeout
Solution: Refresh page, should work (it has fallback caching)
```

### "Pest detection error"
```
Check:
1. Is GEMINI_API_KEY or GROQ_API_KEY set?
2. Did you redeploy after adding keys?
3. Check Render logs for specific error
```

### "API Key invalid"
```
Solutions:
1. Generate new key from provider
2. Make sure you copied full key (no spaces)
3. Update in Render environment
4. Redeploy
```

### "Still not working after 10 minutes"
```
1. Wait - Render deploys take 5-10 minutes
2. Check Render logs in Deploy tab
3. Press Ctrl+Shift+R to hard refresh browser
4. Try different API provider (Groq if Gemini failing)
```

---

## 🎯 WHICH OPTION SHOULD I CHOOSE?

**Recommended:** OPTION 3 (Both Gemini and Groq)

**Because:**
- Automatic fallback if one provider limits out
- Gemini is better for image analysis
- Groq is faster for text analysis
- Free tier covers both
- ~5 minutes extra setup time

**Minimum:** OPTION 1 (Just Gemini)
- Simplest setup
- Powerful and reliable
- 60 requests/minute free tier
- Covers all typical farm usage

**Alternative:** OPTION 2 (Just Groq)
- If you prefer unlimited requests
- Fast responses
- Less specific for agricultural images
- Still covers most use cases

---

## 📊 API FREE TIER LIMITS (So You Don't Get Surprised)

### Google Gemini
- **Free Tier:** 60 requests/minute
- **Typical Farm Usage:** 5-20/month ✅ (Won't hit limit)
- **Estimated Cost:** ~$0 for small farms

### Groq
- **Free Tier:** Unlimited
- **Speed:** Very fast
- **Images:** Limited vision model support
- **Estimated Cost:** ~$0

### Open-Meteo (Weather)
- **Free Tier:** Unlimited
- **No API Key:** Required ✓
- **Typical Farm Usage:** 1-2/hour per user ✅
- **Estimated Cost:** ~$0

**Total Estimated Monthly Cost for FarmWise on Render Free Tier:** $0 ✅

---

## 🚀 AFTER SETUP

Your FarmWise will have:

✅ **Weather**
- Any location, no API key
- Updates hourly
- Agricultural forecasting included
- Completely free

✅ **Pest Detection**
- Upload any crop photo
- AI-powered analysis
- Works on Render free tier
- Fallback detection if API busy
- Completely free

✅ **Automatic Retries**
- Transient failures handled
- Exponential backoff
- Makes APIs more reliable on Render
- Zero additional setup needed

---

**Now you're ready! 🎉 Follow the steps above and you should be done in < 10 minutes.**
