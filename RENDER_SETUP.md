# Render Deployment Setup - Complete Guide

## Step 1: Create Repository Secret Key

On your local machine, generate a secure SECRET_KEY:

```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

Copy the generated key - you'll need it in Step 3.

## Step 2: Deploy on Render

### 2a. Create Web Service

1. Go to [Render Dashboard](https://dashboard.render.com)
2. Click **New +** → **Web Service**
3. Select **Deploy from a Git repository**
4. Choose your GitHub account and authorize
5. Select `Zarchy23/FARMWISE` repository
6. Fill in details:
   - **Name**: `farmwise`
   - **Region**: Choose closest to you
   - **Branch**: `master`
   - **Runtime**: Leave as auto-detected (Python)

### 2b. Create PostgreSQL Database

1. Click **New +** → **PostgreSQL**
2. **Name**: `farmwise-db`
3. **PostgreSQL Version**: 15
4. Create database

The `DATABASE_URL` will be auto-generated.

## Step 3: Configure Environment Variables

In Render Dashboard for your Web Service, go to **Environment** tab and add:

| Key | Value | Required |
|-----|-------|----------|
| `SECRET_KEY` | Paste generated key from Step 1 | ✅ |
| `DEBUG` | `False` | ✅ |
| `ALLOWED_HOSTS` | Your Render URL (e.g., `farmwise.onrender.com`) | ✅ |
| `DATABASE_URL` | Auto-populated from PostgreSQL | ✅ |
| `SECURE_SSL_REDIRECT` | `True` | |
| `SESSION_COOKIE_SECURE` | `True` | |
| `CSRF_COOKIE_SECURE` | `True` | |

**To find your Render URL:**
- After creating web service, go to service settings
- The URL is shown at the top: `https://farmwise.onrender.com`

## Step 4: Deploy

1. **Manually Trigger Deploy:**
   - In Web Service dashboard
   - Click the **Deploy** button

2. **Monitor Deployment:**
   - Go to **Logs** tab to watch build progress
   - Wait for "Service is live" message

3. **Run Migrations (First Time Only):**
   ```
   - Click **Shell** in dashboard
   - Run: python manage.py migrate
   - Run: python manage.py createsuperuser
   ```

## Step 5: Access Your Application

- **Main App**: `https://farmwise.onrender.com`
- **Admin Panel**: `https://farmwise.onrender.com/admin`

Login with superuser credentials created in Step 4.

---

## Common Issues & Solutions

### ❌ "ModuleNotFoundError: No module named 'app'"

**Solution:** This usually means the start command is wrong or Python version mismatch.

1. Check render.yaml has `pythonVersion: 3.11`
2. Redeploy using the **Redeploy** button

### ❌ "SECRET_KEY not provided"

**Solution:** Add SECRET_KEY to Environment Variables

```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

### ❌ Database Connection Error

**Solution:** 
1. Ensure PostgreSQL service is created
2. Check `DATABASE_URL` is in Environment Variables
3. Manually run: `python manage.py migrate` in Shell

### ❌ Static Files Not Loading

**Solution:** Run in Shell tab:
```bash
python manage.py collectstatic --noinput --clear
```

### ❌ 502/503 Service Unavailable

**Solution:**
1. Check logs for errors
2. Redeploy entire service
3. If using free tier, may need to wait 15-30 seconds for cold start

---

## Advanced Configuration

### Enable Auto-Deploy on Git Push

1. Go to Web Service settings
2. Under **Deploy**, toggle **Auto-Deploy** = ON
3. Now every push to `master` triggers automatic deployment

### Upgrade to Paid Plan

Free tier includes:
- 0.5GB RAM
- Spins down after 15 minutes of inactivity (cold start)

Upgrade to **Pro** ($7/month) for:
- 1GB RAM
- No automatic cold starts
- Better performance

### Custom Domain

1. Add custom domain in Web Service settings
2. Update `ALLOWED_HOSTS` environment variable
3. Point DNS records to Render nameservers

---

## Production Checklist

- [ ] `SECRET_KEY` is set and secure
- [ ] `DEBUG = False`
- [ ] `ALLOWED_HOSTS` includes your domain
- [ ] Database migrations completed
- [ ] Superuser account created
- [ ] Static files collected
- [ ] Email configuration set (if needed)
- [ ] Backups configured
- [ ] Monitoring/logging enabled
- [ ] SSL/HTTPS enforced

---

## Quick Redeploy

If you make code changes:

```bash
# Commit and push to GitHub
git add .
git commit -m "Description of changes"
git push origin master

# If auto-deploy is enabled, Render will deploy automatically
# Otherwise, click Redeploy in Render Dashboard
```

---

## Get Help

- Check **Logs** tab in Render Dashboard
- Review [Render Django Docs](https://render.com/docs/django)
- Check [Django Deployment Guide](https://docs.djangoproject.com/en/6.0/howto/deployment/)
