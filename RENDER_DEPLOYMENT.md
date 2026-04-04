# FarmWise - Render Deployment Guide

## Prerequisites

Before deploying to Render, ensure you have:

1. **Render Account** - Sign up at https://render.com
2. **GitHub Repository** - Your code pushed to GitHub (already done)
3. **Environment Variables** - Required secrets and configs

## Deployment Steps

### 1. Connect GitHub to Render

1. Go to [Render Dashboard](https://dashboard.render.com)
2. Click **New +** and select **Web Service**
3. Select **Deploy from a Git repository**
4. Connect your GitHub account and authorize Render
5. Select the `Zarchy23/FARMWISE` repository

### 2. Configure Web Service

**Basic Settings:**
- **Name**: `farmwise` (or your preferred name)
- **Root Directory**: Leave empty (root of repo)
- **Runtime**: `Python 3`
- **Build Command**: 
  ```
  pip install -r requirements.txt && python manage.py collectstatic --noinput
  ```
- **Start Command**:
  ```
  gunicorn farmwise.wsgi:application --bind 0.0.0.0:8000
  ```

### 3. Add Environment Variables

Add these in **Environment** tab:

| Key | Value | Notes |
|-----|-------|-------|
| `DEBUG` | `False` | Never True in production |
| `ALLOWED_HOSTS` | `<your-render-url>.onrender.com` | Get URL from Render |
| `DJANGO_SETTINGS_MODULE` | `farmwise.settings` | |
| `PYTHON_VERSION` | `3.11.0` | |
| `SECRET_KEY` | `<generate-new-key>` | Generate from Django |
| `DATABASE_URL` | Auto-populated | From PostgreSQL instance |

### 4. Create PostgreSQL Database

1. In Render Dashboard, click **New +** → **PostgreSQL**
2. **Name**: `farmwise-db`
3. **Region**: Choose closest to you
4. **PostgreSQL Version**: 15
5. Create the database

The `DATABASE_URL` will be auto-populated in your web service environment.

### 5. Deploy

1. Click **Create Web Service**
2. Render will automatically:
   - Install dependencies from `requirements.txt`
   - Run the build command
   - Start the web service
3. Monitor logs in the **Logs** tab

### 6. Run Initial Migrations

After first deployment:

1. Go to **Shell** tab in Render
2. Run:
   ```bash
   python manage.py migrate
   python manage.py createsuperuser
   ```

## Post-Deployment Checklist

- [ ] Test the application at your Render URL
- [ ] Create a superuser account
- [ ] Update `ALLOWED_HOSTS` with your actual Render URL
- [ ] Enable automatic deployments (optional - enable auto-deploy on git push)
- [ ] Set up custom domain (if needed)
- [ ] Configure email settings (SendGrid, etc.)
- [ ] Set up static/media file storage (AWS S3 recommended)

## Files Included for Render

| File | Purpose |
|------|---------|
| `Dockerfile` | Container configuration (optional - Render can use native Python) |
| `.dockerignore` | Optimize Docker builds |
| `Procfile` | Process configuration (used by Render) |
| `render.yaml` | Render deployment manifest |
| `runtime.txt` | Python version specification |
| `requirements.txt` | Python dependencies |

## Troubleshooting

### Application won't start
- Check logs for errors
- Verify all environment variables are set
- Ensure `SECRET_KEY` is set
- Check database migrations ran successfully

### 502/503 Errors
- Review application logs
- Check if database is reachable
- Verify resource limits (may need to upgrade plan)

### Static files not loading
- Run `python manage.py collectstatic --noinput`
- Configure S3 for static files in production

### Database connection issues
- Verify `DATABASE_URL` is set
- Check if PostgreSQL instance is running
- Ensure IP is whitelisted (Render handles this automatically)

## Additional Resources

- [Render Docs - Django](https://render.com/docs/django)
- [Django Deployment Guide](https://docs.djangoproject.com/en/6.0/howto/deployment/)
- [Render Dashboard](https://dashboard.render.com)

## Need Help?

For Render-specific issues, check:
1. Application logs in Render Dashboard
2. [Render Community Docs](https://render.com/docs)
3. Render Support Chat
