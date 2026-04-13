# ⚡ QUICK START - GET RENDER WORKING IN 5 MINUTES

**Status:** ✅ All fixes implemented  
**You need:** 1 API key (free)  
**Time:** < 5 minutes to deploy  

---

## 🎯 DO THIS NOW (In Order)

### 1️⃣ GET YOUR API KEY (2 minutes)

**Click ONE link below:**

👉 **Gemini (RECOMMENDED):** https://ai.google.dev/ → Click "Get API Key"  
👉 **Groq (Alternative):** https://console.groq.com/ → Sign up → API Keys

Copy the key you get (looks like `AIzaSy...` or `gsk_...`)

---

### 2️⃣ ADD TO RENDER (2 minutes)

**In Render Dashboard:**

1. Click your Web Service
2. Go to **Settings**
3. Scroll to **Environment**
4. Click **Add Environment Variable**
5. Enter **ONE** of these:

```
GEMINI_API_KEY=<paste_key_here>
```

or

```
GROQ_API_KEY=<paste_key_here>
```

---

### 3️⃣ REDEPLOY (1 minute)

**In Render Dashboard:**

1. Click **Deploy** tab
2. Click **Manual Deploy**
3. Click **Deploy latest commit**
4. Wait for green checkmark (5-10 minutes)

---

### 4️⃣ TEST (1 minute)

**In Your Browser:**

1. Go to your FarmWise dashboard
2. Check **Weather widget** - should show temperature (not "N/A")
3. Upload a crop photo for **pest detection**
4. Should return analysis (not error)

✅ **If both work - you're done!**

---

## 🆘 STUCK?

| Problem | Solution |
|---------|----------|
| Weather still showing "N/A" | Refresh page (Ctrl+F5), wait for deploy |
| Pest detection error | Check API key is set + redeploy |
| "Still Deploying" | Wait 5-10 minutes |
| Deployment failed? | Click Manual Deploy again |

---

## 📊 WHAT YOU JUST DID

```
Weather API         → Now using Open-Meteo (free ✅)
Pest Detection      → Now using Gemini/Groq (free ✅)
Retry Logic         → Auto-retries on timeouts (added ✅)
Total Monthly Cost  → $0 (free tier) ✅
```

---

**Done! 🎉 Your FarmWise is now production-ready on Render free tier.**

For more details → See `RENDER_API_FIX_GUIDE.md`
