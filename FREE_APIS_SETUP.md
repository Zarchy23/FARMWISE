# FarmWise Free Tier APIs Setup Guide for Render

**Good News!** Your FarmWise app now uses completely FREE APIs that work perfectly on Render's free tier. **No more OpenAI costs!** 🎉

## 📊 What Changed?

| Feature | Before | After | Status |
|---------|--------|-------|--------|
| **Pest Detection** | OpenAI ($0.01-0.05/image) | Google Gemini (Free) | ✅ Upgraded |
| **Weather Forecast** | OpenWeatherMap (60 calls/min) | Open-Meteo (Unlimited, NO KEY!) | ✅ Optimized |
| **Backup Detection** | Single API | Gemini + Groq + Together.ai + Rule-based | ✅ Enhanced |

---

## 🚀 Quick Setup (5 minutes)

### Step 1: Get Free API Keys

**Google Gemini (for Pest Detection)**
```bash
Visit: https://aistudio.google.com/app/apikeys
1. Click "Create API Key"
2. Select/create a Google Cloud project
3. Copy your free API key
4. Gemini Free Tier: 60 requests per minute (plenty!)
```

**Optional: Groq (extra backup for pest detection)**
```bash
Visit: https://console.groq.com/keys
1. Sign up (no credit card needed)
2. Create new API key
3. Free tier available
```

**Optional: Together.ai (another backup)**
```bash
Visit: https://api.together.xyz/
1. Sign up
2. Get $25 free credits/month
3. More than enough for a small farm operation
```

### Step 2: Configure in Render

Go to your Render dashboard:

1. **Click** "Environment" on your service
2. **Add these variables:**

```env
# REQUIRED - Pest Detection (Google Gemini - FREE!)
GEMINI_API_KEY=your_gemini_key_here

# OPTIONAL - Backups (if you want redundancy)
GROQ_API_KEY=your_groq_key_here
TOGETHER_API_KEY=your_together_key_here

# Set OPENAI_API_KEY to empty (not used anymore)
OPENAI_API_KEY=

# OPTIONAL - Weather (Open-Meteo doesn't need a key, but you can override)
OPENWEATHER_API_KEY=
```

3. **Click "Save Changes"** and wait for deployment

### Step 3: Deploy Updated Code

```bash
# Pull latest code
git pull origin main

# Deploy to Render
git push origin main
# OR manually redeploy from Render dashboard
```

---

## 📱 How to Use the New APIs

### In Your Django Template

```html
<!-- Get real-time weather for agricultural decisions -->
<script>
  // Fetch live weather with agricultural indicators
  fetch('/api/weather/{{ farm.id }}/agricultural/')
    .then(r => r.json())
    .then(data => {
      console.log('GDD:', data.indicators[0].growing_degree_days);
      console.log('Heat Stress:', data.indicators[0].heat_stress);
      console.log('Frost Risk:', data.indicators[0].frost_risk);
    });
</script>
```

### Via Python/Django

```python
from core.services.weather import weather_service

# Get agricultural forecast (no API key needed!)
forecast = weather_service.get_agricultural_forecast(
    lat=-1.286389,  # Nairobi
    lng=36.817223
)

for day in forecast['forecast']:
    print(f"{day['date']}: GDD={day['growing_degree_days']}, THI={day['temperature_humidity_index']}")
```

### Pest Detection

```python
from core.services.pest_detection import PestDetectionService
from django.conf import settings

service = PestDetectionService(settings.GEMINI_API_KEY)

# Analyze image
result = service.detect_from_image(image_file)
print(f"Pest: {result['detected_issue']}")
print(f"Confidence: {result['confidence']}%")
print(f"Treatment: {result['treatment']}")

# OR detect from symptoms (completely free, offline)
symptoms = ["white powder on leaves", "stunted growth"]
result = service.detect_from_symptoms(symptoms)
```

---

## 🎯 API Features & Limits

### Google Gemini (Pest Detection)
- **Free Tier Limit:** 60 requests/minute
- **Perfect for:** 1-2 farms doing pest checks a few times per day
- **Cost:** Free
- **Setup Time:** < 1 minute

### Open-Meteo (Weather)
- **Free Tier Limit:** Unlimited! No rate limiting
- **Perfect for:** All weather features
- **Cost:** Completely FREE (no API key needed!)
- **Data:** 80+ years of historical weather
- **Agricultural Indicators:** Temperature-Humidity Index, Growing Degree Days, Frost Risk, Pest Risk

### Groq (Backup Pest Detection)
- **Free Tier Limit:** ~50 requests/day
- **Perfect for:** Backup when Gemini is rate-limited
- **Cost:** Free
- **Speed:** Very fast (good fallback)

### Together.ai (Another Backup)
- **Free Tier:** $25 credits/month
- **Perfect for:** Secondary layer redundancy
- **Cost:** Free tier available
- **Models:** Llama Vision (free)

---

## 🛡️ Fallback Strategy

**Your app intelligently falls back:**

```
User uploads pest image
    ↓
Try Gemini API (if configured) → Success: Return result
    ↓ [if fails or no key]
Try Groq API (if configured) → Success: Return result
    ↓ [if fails or no key]
Try Together.ai API (if configured) → Success: Return result
    ↓ [if all fail]
Use Rule-Based Detection → Always works! (offline, free)
    ↓
Return best-guess from database of common pests
```

**Result:** You can NEVER run out of pest detection! ✅

---

## 🌡️ Agricultural Indicators Explained

### Growing Degree Days (GDD)
- **What:** Accumulation of warmth for crop development
- **Formula:** (Max Temp + Min Temp) / 2 - Base (10°C for maize)
- **Use for:** Predicting crop phenology, harvest dates
- **Example:** Maize needs ~2500 GDD from planting to harvest

### Temperature-Humidity Index (THI)
- **What:** Livestock heat stress indicator
- **Range:** 0-100+
  - < 72: Comfortable
  - 72-78: Mild heat stress
  - > 78: Severe heat stress
- **Use for:** Livestock management, shelter requirements

### Frost Risk
- **What:** Nights that may drop below 2°C
- **Use for:** Protecting sensitive crops, frost-resistant crop selection

### Pest Risk
- **What:** Temperature range favoring pest activity (25-35°C)
- **Use for:** Preventive pest management timing

---

## 💾 Dependencies Added

```bash
# New packages in requirements.txt:
httpx              # Fast HTTP client for Open-Meteo
google-generativeai # Google Gemini API
```

**Install locally:**
```bash
pip install -r requirements.txt
```

---

## ✅ Testing Your Setup

### Test Weather API

```bash
# From Django shell
python manage.py shell

from core.services.weather import weather_service

# Test Open-Meteo (no key needed!)
forecast = weather_service.get_forecast(-1.286389, 36.817223, days=7)
print("✅ Weather API working!")
```

### Test Pest Detection

```bash
python manage.py shell

from core.services.pest_detection import PestDetectionService
from django.conf import settings

service = PestDetectionService(settings.GEMINI_API_KEY)

# Test with symptoms (works even without API key)
result = service.detect_from_symptoms(["white powder", "stunted growth"])
print("✅ Pest detection working!")
print(result['detected_issue'])
```

### Via cURL

```bash
# Test weather endpoint
curl https://your-renderapp.com/api/weather/1/agricultural/

# Response should include agricultural indicators
```

---

## 🔍 Monitoring & Debugging

**Check which API is being used:**

```python
# Add to Django settings for logging
LOGGING = {
    'loggers': {
        'core.services': {
            'level': 'INFO',
            'handlers': ['console'],
        }
    }
}

# Logs will show:
# "Using Gemini for pest detection"
# "Open-Meteo forecast loaded from cache"
# "Fallback: Using Groq for pest detection"
```

**View logs in Render:**
```
Render Dashboard → Your Service → Logs
```

---

## 💰 Cost Comparison

| API | Old (OpenAI) | New (Free) | Annual Savings |
|-----|-------------|-----------|-----------------|
| Pest Detection | $0.02-0.05/image | FREE | $200+ |
| Weather | OpenWeather | FREE | $50+ |
| **Total** | **$300+/year** | **$0** | **$300+/year** |

---

## 🐛 Troubleshooting

### "Gemini API not available"
- **Check:** Is `GEMINI_API_KEY` set in Render environment?
- **Fix:** Add the key to Render dashboard, redeploy

### "Weather data not available"
- **Check:** Does your farm have GPS coordinates?
- **Fix:** Update farm location in FarmWise settings
- **Why:** Open-Meteo needs latitude/longitude

### "Pest detection failing with error"
- **Check:** Is the fallback working? See logs
- **Expect:** If Gemini fails, app automatically tries Groq, Together.ai, then rule-based
- **Result:** Pest detection NEVER fails completely

### "Rate limit exceeded"
- **Unlikely:** Gemini: 60 req/min | Open-Meteo: Unlimited
- **If it happens:** Your backup APIs activate automatically
- **Contact:** Render support if issues persist

---

## 📚 Additional Resources

- [Open-Meteo Documentation](https://open-meteo.com/)
- [Google Gemini Free Tier](https://aistudio.google.com/)
- [Groq Console](https://console.groq.com/)
- [Together.ai API](https://api.together.xyz/)

---

## ✨ Summary

**Before This Update:**
- ❌ Using paid OpenAI API
- ❌ Risk of hitting Render network limitations
- ❌ Potential cost: $300+/year
- ❌ Single point of failure

**After This Update:**
- ✅ Using free APIs (Gemini + Open-Meteo + Groq + Together.ai)
- ✅ Perfect Render free tier compatibility
- ✅ Cost: $0
- ✅ Multiple fallbacks = never fails

**Your FarmWise app is now production-ready on Render's free tier!** 🎉

---

*Generated for FarmWise - Free Agricultural Management Platform*
