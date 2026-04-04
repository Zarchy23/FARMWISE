# FarmWise - Complete Render Deployment Guide

## Issue: Python 3.14.3 Module Error

If you're seeing: `ModuleNotFoundError: No module named 'app'` with Python 3.14.3, follow these exact steps.

---

## Complete Setup (Start Fresh)

### Step 1: Delete Current Render Service

1. Go to [Render Dashboard](https://dashboard.render.com)
2. Select your **farmwise** web service
3. Scroll to bottom → **Delete Service**
4. Type the confirmation text and delete
5. Wait 1-2 minutes for deletion

### Step 2: Delete PostgreSQL Database (Optional)

If you want a fresh database:
1. Go to Dashboard
2. Select **farmwise-db** PostgreSQL
3. Delete (or keep to preserve data)

### Step 3: Create New Web Service

1. Click **New +** → **Web Service**
2. **Connect to:** Select your GitHub account (if not already connected)
3. **Repository:** Choose `Zarchy23/FARMWISE`
4. Click **Create Web Service** (at bottom)

### Step 4: Configure Web Service

Fill in the form:
- **Name:** `farmwise`
- **Region:** Choose location closest to you (e.g., `us-east-1`)
- **Branch:** `master`
- **Runtime:** Leave as auto-detected
- **Build Command:**
  ```
  pip install -r requirements.txt && python manage.py migrate --noinput && python manage.py collectstatic --noinput --clear
  ```
- **Start Command:**
  ```
  python -m gunicorn farmwise.wsgi:application --bind 0.0.0.0:8000 --workers 3
  ```
- **Plan:** Free

### Step 5: Add Environment Variables

**CRITICAL:** Do this BEFORE clicking "Create Web Service"

Scroll down to **Environment** section and add:

| Key | Value |
|-----|-------|
| `DEBUG` | `False` |
| `ALLOWED_HOSTS` | `localhost,127.0.0.1,*.onrender.com` |
| `SECRET_KEY` | Generate at terminal: `python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"` |

**⚠️ IMPORTANT:** Add `SECRET_KEY` BEFORE deploying!

### Step 6: Create PostgreSQL Database

Don't click "Create Web Service" yet!

1. In same dashboard, click **New +** → **PostgreSQL**
2. **Name:** `farmwise-db`
3. **PostgreSQL Version:** 15
4. **Region:** Same as web service
5. **Plan:** Free
6. Click **Create Database**

Wait for database to be created (1-2 mins).

### Step 7: Connect Database to Web Service

1. Go back to your unfinished **Web Service** form
2. Scroll to **Database** section
3. Select `farmwise-db`
4. The `DATABASE_URL` will auto-populate in Environment Variables

Now click **Create Web Service!**

---

## Step 8: Monitor Deployment

1. You'll see the **Logs** tab
2. Watch for **"Build started"** → **"Running migrations"** → **"Service is live"**
3. This takes 3-5 minutes

### Common Build Messages (Normal):
```
⠼ Building...
📥 Downloaded build image
🔨 Building...
✅ Migrations completed successfully
✅ Static files collected
🚀 Service is live
```

### If You See Errors:

1. **Check logs** for specific error messages
2. Common fixes:
   ```bash
   # Manually migrate in Shell
   python manage.py migrate
   
   # Check static files
   python manage.py collectstatic --noinput --clear
   ```

---

## Step 9: Get Your App URL & Update ALLOWED_HOSTS

1. Once deployed, copy your Render URL (e.g., `https://farmwise-abc123.onrender.com`)
2. Go to Web Service → **Environment**
3. Update `ALLOWED_HOSTS` to:
   ```
   localhost,127.0.0.1,farmwise-abc123.onrender.com
   ```
4. Click **Save**
5. Service will auto-redeploy

---

## Step 10: Create Superuser (First Time Only)

### Option A: Using Render Shell (Recommended)

1. Go to Web Service → **Shell**
2. Run:
   ```bash
   python manage.py createsuperuser
   ```
3. Enter username, email, password

### Option B: Using Django Admin

If you have setup a script:
```bash
python manage.py shell
```

---

## Step 11: Access Your App

1. **Main App:** `https://your-render-url.onrender.com`
2. **Admin Panel:** `https://your-render-url.onrender.com/admin`
3. Login with superuser credentials from Step 10

---

## Using Your Existing Database

If you want to keep your local database data:

### Backup Local Database:
```bash
# On your local machine
python manage.py dumpdata > backup.json
```

### Restore to Render:

1. Upload `backup.json` to Render Shell
2. In Render Shell:
   ```bash
   python manage.py migrate  # Create schema
   python manage.py loaddata backup.json  # Load data
   ```

---

## File Reference

| File | Purpose |
|------|---------|
| `.python-version` | Forces Python 3.11 (not 3.14.3) |
| `Procfile` | Tells Render how to build & run app |
| `runtime.txt` | Specifies Python 3.11.0 |
| `requirements.txt` | All Python dependencies |
| `farmwise/wsgi.py` | Django WSGI entry point |

---

## Troubleshooting

### ❌ "ModuleNotFoundError: No module named 'app'"
**Solution:** 
- Delete service and start fresh (you're likely on Python 3.14)
- Use exact build/start commands above
- Ensure .python-version exists in your repo

### ❌ "SECRET_KEY not set"
**Solution:**
- Generate: `python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"`
- Add to Environment Variables BEFORE deploying

### ❌ "Connection refused - Can't connect to database"
**Solution:**
- DatabaseURL should auto-populate from PostgreSQL
- Check it exists in Environment Variables
- Restart service (Menu → Restart)

### ❌ "Static files not loading (404)"
**Solution:**
- In Shell: `python manage.py collectstatic --noinput --clear`
- Update `STATIC_ROOT` in settings.py if needed

### ❌ "Service won't stay running / keeps crashing"
**Solution:**
- Check Logs for actual error
- Increase memory (upgrade to Pro plan)
- Try manual redeploy: Service Menu → Redeploy

---

## Production Checklist

- [ ] `SECRET_KEY` is set (not default)
- [ ] `DEBUG = False` (never True in production)
- [ ] `ALLOWED_HOSTS` configured correctly
- [ ] PostgreSQL database created & connected
- [ ] Migrations ran successfully
- [ ] Superuser account created
- [ ] Static files collected
- [ ] `.python-version` is `3.11.0` (not 3.14.3)
- [ ] `Procfile` uses correct Python command
- [ ] Database backup taken (if migrating data)

---

## Quick Redeploy

After code changes on local machine:
```bash
git add .
git commit -m "Description of changes"
git push origin master

# If auto-deploy enabled, Render auto-deploys
# Otherwise, click Redeploy in Render Dashboard
```

---

## Auto-Deploy Setup

For automatic deployment on each git push:
1. Web Service → **Settings**
2. Under **Deploy**, toggle **Auto-Deploy** = ON
3. Now every push to master auto-deploys

---

## Still Having Issues?

1. **Check Render Logs** - Most detailed info there
2. **Review Django Logs** using `python manage.py` in Shell
3. **Verify all files in repo** - run `git status` locally
4. **Test locally first** - `python manage.py runserver` should work
5. **Contact Render Support** - They're helpful!

---

## Useful Links

- [Render Docs - Django](https://render.com/docs/django)
- [Render Docs - Python Version](https://render.com/docs/python-version)
- [Django Deployment Guide](https://docs.djangoproject.com/en/6.0/howto/deployment/)
- [FarmWise GitHub](https://github.com/Zarchy23/FARMWISE)
