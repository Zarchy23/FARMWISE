# 🔒 FarmWise Security & Backup Quick Setup Guide

**Last Updated:** April 11, 2026  
**Status:** Ready for Implementation  
**Difficulty:** Medium

---

## 🚀 QUICK START (5 Steps)

### Step 1: Update Django Settings
```bash
cd ~/farmwise
# Edit farmwise/settings.py and add security settings
# (See SECURITY_HARDENING_PLAN.md for exact settings)
```

### Step 2: Install Backup Dependencies
```bash
pip install boto3 python-decouple
```

### Step 3: Set Environment Variables
Create `.env` file in project root:
```bash
# Copy template
cp .env.example .env

# Edit with production values
nano .env
```

Required variables:
```
SECRET_KEY=your-super-secret-key-here
DEBUG=False
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com
DB_NAME=farmwise_prod
DB_USER=farmwise_user
DB_PASSWORD=your_strong_password
BACKUP_DIR=/backups/farmwise
S3_BACKUP_BUCKET=your-s3-bucket-name
AWS_ACCESS_KEY_ID=your-aws-key
AWS_SECRET_ACCESS_KEY=your-aws-secret
```

### Step 4: Run Setup Script

**For Linux/Mac:**
```bash
sudo bash backup_cron_setup.sh
```

**For Windows:**
```powershell
powershell -ExecutionPolicy Bypass -File backup_setup.ps1
```

### Step 5: Verify Installation
```bash
# Test backup manually
python manage.py shell << EOF
from core.backup_manager import BackupManager
mgr = BackupManager()
print(mgr.get_backup_status())
EOF
```

---

## 📋 SECURITY AUDIT CHECKLIST

### CRITICAL (Do First)
- [ ] Change `SECRET_KEY` in settings.py (generate new one)
- [ ] Set `DEBUG=False` in production
- [ ] Configure `ALLOWED_HOSTS` with actual domain
- [ ] Enable `SECURE_SSL_REDIRECT=True`
- [ ] Set `SESSION_COOKIE_SECURE=True`
- [ ] Set `CSRF_COOKIE_SECURE=True`
- [ ] Verify database password is strong (20+ chars)
- [ ] Check SSL certificate installed and valid

### HIGH PRIORITY (Week 1)
- [ ] Enable 2FA for all admin users
- [ ] Set up database backups (automated)
- [ ] Configure S3 bucket for backups
- [ ] Enable activity logging
- [ ] Set up monitoring/alerting
- [ ] Document incident response procedures
- [ ] Test backup restoration

### MEDIUM PRIORITY (Week 2)
- [ ] Enable rate limiting on API endpoints
- [ ] Configure security headers (HSTS, CSP, etc.)
- [ ] Set up log aggregation (ELK or CloudWatch)
- [ ] Configure DDoS protection (Cloudflare/Shield)
- [ ] Implement IP whitelisting for admin panel
- [ ] Document password rotation policy

### LOW PRIORITY (Ongoing)
- [ ] Monthly security audits
- [ ] Quarterly disaster recovery drills
- [ ] Annual penetration testing
- [ ] Update security documentation
- [ ] Team security training

---

## 🔧 DETAILED SETUP INSTRUCTIONS

### A. Django Settings Configuration

1. **Open settings.py:**
```bash
nano farmwise/settings.py
```

2. **Add after imports (line ~10):**
```python
import os
from decouple import config

# Security Settings (Production)
if not config('DEBUG', default=False, cast=bool):
    # HTTPS
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Strict'
    CSRF_COOKIE_SECURE = True
    CSRF_COOKIE_HTTPONLY = True
    
    # Headers
    SECURE_HSTS_SECONDS = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    SECURE_BROWSER_XSS_FILTER = True
    X_FRAME_OPTIONS = 'DENY'
    
    # CSP (Content Security Policy)
    SECURE_CONTENT_SECURITY_POLICY = {
        'default-src': ("'self'",),
        'script-src': ("'self'", "'unsafe-inline'"),
        'style-src': ("'self'", "'unsafe-inline'"),
        'img-src': ("'self'", "data:", "https:"),
    }
```

3. **Verify existing settings:**
```python
# Should already have these
SECURE_URL_PROTOCOL = 'https'
LOGIN_REDIRECT_URL = '/'
LOGIN_URL = 'login'
```

### B. Environment Variables (.env file)

1. **Create .env template:**
```bash
cat > .env << 'EOF'
# Django
SECRET_KEY=change-this-to-very-secret-key-min-50-chars
DEBUG=False
ALLOWED_HOSTS=localhost,127.0.0.1,yourdomain.com

# Database (PostgreSQL)
DB_ENGINE=postgresql
DB_NAME=farmwise_prod
DB_USER=farmwise_user
DB_PASSWORD=your_strong_db_password_here_min_20_chars
DB_HOST=db.yourdomain.com
DB_PORT=5432
DB_CONN_MAX_AGE=60

# Redis
REDIS_URL=redis://redis-host:6379/0

# Email (for alerts)
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password

# AWS S3 (for backups)
AWS_ACCESS_KEY_ID=your-aws-key-here
AWS_SECRET_ACCESS_KEY=your-aws-secret-here
S3_BACKUP_BUCKET=farmwise-backups-your-company
AWS_REGION=us-east-1

# Backup
BACKUP_DIR=/backups/farmwise
MEDIA_ROOT=/var/www/farmwise/media

# Security
SECURE_SSL_REDIRECT=True
SESSION_COOKIE_SECURE=True
CSRF_COOKIE_SECURE=True
SECURE_HSTS_SECONDS=31536000
ADMIN_IP_WHITELIST=203.0.113.1,203.0.113.2
EOF
```

2. **Generate SECRET_KEY:**
```python
python << 'EOF'
from django.core.management.utils import get_random_secret_key
print(get_random_secret_key())
EOF
```

3. **Set permissions:**
```bash
chmod 600 .env
```

### C. Database Backup Testing

1. **Test manual backup:**
```bash
python manage.py shell << 'EOF'
from core.backup_manager import BackupManager
manager = BackupManager()
backup_file = manager.backup_database()
print(f"Backup created: {backup_file}")
EOF
```

2. **Verify backup:**
```bash
# Check file exists and has content
ls -lh /backups/farmwise/

# Verify gzip integrity
gunzip -t /backups/farmwise/farmwise_db_*.sql.gz
```

3. **Test restore:**
```bash
python manage.py shell << 'EOF'
from core.backup_manager import BackupManager
manager = BackupManager()
# Get latest backup
import os
backups = sorted([f for f in os.listdir(manager.backup_dir) if f.endswith('.sql.gz')])
latest = os.path.join(manager.backup_dir, backups[-1])
new_db = manager.restore_database(latest, 'farmwise_restore_test')
print(f"Restored to: {new_db}")
EOF
```

### D. Set Up Automated Backups

**For Windows (FarmWise on Windows):**
```powershell
# Run as Administrator
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
powershell -ExecutionPolicy Bypass -File backup_setup.ps1
```

**For Linux/Mac:**
```bash
# Must run as root/sudo
sudo bash backup_cron_setup.sh
```

After setup, verify:
```bash
# View scheduled cron jobs
crontab -l

# Or on Windows: open Task Scheduler and look for FarmWise- tasks
```

### E. Monitor Backups

**Check backup status:**
```bash
python manage.py shell << 'EOF'
from core.backup_manager import BackupManager
manager = BackupManager()
status = manager.get_backup_status()
import json
print(json.dumps(status, indent=2))
EOF
```

**View backup logs:**
```bash
# Linux/Mac
tail -f /var/log/farmwise/backup.log

# Windows
Get-Content "$env:USERPROFILE\farmwise\logs\backup.log" -Tail 20 -Wait
```

---

## 🆘 TROUBLESHOOTING

### Backup fails with "database does not exist"
```bash
# Create database
createdb -U farmwise_user farmwise_prod

# Or in Windows
psql -U postgres -c "CREATE DATABASE farmwise_prod OWNER farmwise_user;"
```

### Backup too slow or large
- **Check what's growing:** `SELECT schemaname, tablename, pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) FROM pg_tables ORDER BY pg_total_relation_size DESC LIMIT 10;`
- **Clear old data:** Archive old records to separate storage
- **Exclude large tables:** Modify backup_manager.py

### S3 upload fails
```bash
# Test AWS credentials
aws s3 ls --profile farmwise

# Check IAM permissions (needs S3:PutObject)
# Verify bucket name and region
```

### Scheduled task not running
```bash
# Linux: check cron daemon
sudo service cron status

# Windows: check Task Scheduler logs
Get-ScheduledTaskInfo -TaskName "FarmWise-DatabaseBackup"
```

### Restore test fails
```bash
# Verify backup file isn't corrupted
gunzip -t /backups/farmwise/farmwise_db_latest.sql.gz

# Check PostgreSQL service is running
pg_isready -h localhost -U farmwise_user
```

---

## 📞 SUPPORT & ESCALATION

**Issue → Action:**

| Problem | Solution | Contact |
|---------|----------|---------|
| Backup missing | Check logs | Run verify script |
| Database error | Check permissions | DB Admin |
| S3 upload fails | Check credentials | AWS Support |
| Restore broken | Test backup integrity | Database team |
| Disk full | Cleanup/expand | Infrastructure |

---

## 🔄 MAINTENANCE SCHEDULE

### Daily
- ✅ Automatic backup at 2 AM
- ✅ Automatic verification at 7 AM
- ✅ Monitor backup logs

### Weekly
- ☐ Review backup sizes
- ☐ Check disk usage
- ☐ Review security alerts

### Monthly
- ☐ Test restore procedure
- ☐ Review access logs
- ☐ Update backup retention

### Quarterly
- ☐ Full disaster recovery drill
- ☐ Security audit
- ☐ Update procedures

### Annually
- ☐ Penetration test
- ☐ Compliance review
- ☐ Backup strategy review

---

## 📚 RELATED DOCUMENTATION

- `SECURITY_HARDENING_PLAN.md` - Complete security guide
- `SECURITY.md` - Existing security features
- `core/backup_manager.py` - Backup manager source
- `core/models.py` - LoginAttempt logging model
- `.env.example` - Environment variables template

---

**Questions?** Check the main `SECURITY_HARDENING_PLAN.md` or run:
```bash
python manage.py check --deploy
```
