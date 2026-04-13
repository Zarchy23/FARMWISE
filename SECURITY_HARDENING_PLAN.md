# 🔐 FarmWise Security Hardening & Disaster Recovery Plan

**Last Updated:** April 11, 2026  
**Priority:** CRITICAL  
**Status:** Implementation Guide

---

## 📋 EXECUTIVE SUMMARY

This document provides a complete security hardening checklist and disaster recovery procedures to prevent hacking, data loss, and system downtime.

**Defense Layers:**
1. ✅ Authentication & Access Control
2. ✅ Data Protection & Encryption
3. ✅ Input Validation & API Security
4. ✅ Infrastructure Hardening
5. ✅ Backup & Disaster Recovery
6. ✅ Monitoring & Incident Response
7. ✅ Compliance & Auditing

---

## 1️⃣ AUTHENTICATION & ACCESS HARDENING

### Current Implementations
- ✅ RBAC (Role-Based Access Control) with 9 roles
- ✅ Two-Factor Authentication (TOTP)
- ✅ Session management with 24-hour expiry
- ✅ Account lockout (5 failures → 15 min lock)
- ✅ Password hashing (Argon2 primary)

### Required Actions

#### A. Set Environment Variables (.env file)
```bash
# CRITICAL: Change these before production!
SECRET_KEY=your-super-secret-key-generate-new-one
DEBUG=False
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com

# Database
DB_ENGINE=postgresql
DB_NAME=farmwise_prod
DB_USER=farmwise_user
DB_PASSWORD=STRONG_PASSWORD_HERE_min_20_chars
DB_HOST=db.internal.example.com
DB_PORT=5432
DB_CONN_MAX_AGE=60

# Redis (for caching & sessions)
REDIS_URL=redis://secure-redis-host:6379/0

# Security Headers
SECURE_SSL_REDIRECT=True
SESSION_COOKIE_SECURE=True
CSRF_COOKIE_SECURE=True
SECURE_HSTS_SECONDS=31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS=True
SECURE_HSTS_PRELOAD=True
```

#### B. Force HTTPS and Security Headers
Add to `farmwise/settings.py`:
```python
# SSL/TLS Settings (Production)
if not DEBUG:
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Strict'
    CSRF_COOKIE_SECURE = True
    CSRF_COOKIE_HTTPONLY = True
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_SECURITY_POLICY = {
        'default-src': ("'self'",),
        'script-src': ("'self'", "'unsafe-inline'"),  # Tighten if possible
        'style-src': ("'self'", "'unsafe-inline'"),
        'img-src': ("'self'", "data:", "https:"),
    }
    SECURE_HSTS_SECONDS = 31536000  # 1 year
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    X_FRAME_OPTIONS = 'DENY'
```

#### C. Enforce 2FA for Admins
Update `core/models.py` User model:
```python
class User(AbstractUser):
    two_factor_enabled = models.BooleanField(default=False)
    is_admin_required_2fa = models.BooleanField(default=True)  # Force 2FA for admins
    otp_backup_codes = models.JSONField(default=list, blank=True)
    
    def is_2fa_required(self):
        return self.is_staff and self.is_admin_required_2fa
```

#### D. Enable IP Whitelisting for Admin Panel
```python
# core/views.py - Add to admin panel views
from functools import wraps

ADMIN_WHITELIST = config('ADMIN_IP_WHITELIST', default='', cast=Csv())

def require_admin_ip(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_staff:
            return redirect('login')
        
        if ADMIN_IP_WHITELIST:
            client_ip = get_client_ip(request)
            if client_ip not in ADMIN_IP_WHITELIST:
                logger.warning(f"Admin access attempt from unauthorized IP: {client_ip}")
                return HttpResponseForbidden("Access denied from this IP")
        
        return view_func(request, *args, **kwargs)
    return wrapper
```

---

## 2️⃣ DATA PROTECTION & ENCRYPTION

### Database Security

#### A. Encrypt Sensitive Fields
Create encryption utility:
```python
# core/encryption.py
from cryptography.fernet import Fernet
from django.conf import settings

cipher = Fernet(settings.ENCRYPTION_KEY.encode())

def encrypt_field(value):
    if value is None:
        return None
    return cipher.encrypt(str(value).encode()).decode()

def decrypt_field(encrypted_value):
    if encrypted_value is None:
        return None
    return cipher.decrypt(encrypted_value.encode()).decode()
```

#### B. Encrypt PII Fields in Models
```python
# core/models.py
from django.db import models
from core.encryption import encrypt_field, decrypt_field

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    _national_id = models.CharField(max_length=255, db_column='national_id')  # Encrypted
    _phone_encrypted = models.CharField(max_length=255, db_column='phone')
    
    @property
    def national_id(self):
        return decrypt_field(self._national_id)
    
    @national_id.setter
    def national_id(self, value):
        self._national_id = encrypt_field(value)
    
    # Same for phone, bank account, etc.
```

#### C. Regular Security Audits
```bash
# Run quarterly
python manage.py dbshell << EOF
-- Check for weak permissions
SELECT table_name, grantee, privilege_type 
FROM role_table_grants 
WHERE privilege_type NOT IN ('SELECT', 'INSERT', 'UPDATE', 'DELETE');

-- Check user access
\du
EOF
```

---

## 3️⃣ API & INPUT SECURITY

### Current Protection
- ✅ CSRF tokens on all forms
- ✅ Rate limiting on login (5 failures/5min)
- ✅ Input validation on all fields
- ✅ SQL injection prevention (ORM)
- ✅ XSS prevention (template escaping)

### Additional Hardening

#### A. API Rate Limiting
```python
# settings.py
REST_FRAMEWORK = {
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle'
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': '100/hour',        # Anonymous users
        'user': '1000/hour',       # Authenticated users
        'login': '5/hour',         # Login attempts
        'api_key': '10000/hour',   # API key requests
    }
}
```

#### B. DDoS Protection
- Use Cloudflare or similar CDN
- Enable rate limiting at reverse proxy
- Monitor for suspicious patterns

#### C. Dependency Scanning
```bash
# Weekly
pip install safety
safety check

# Or use Dependabot on GitHub
```

---

## 4️⃣ INFRASTRUCTURE HARDENING

### Web Server Security

#### A. Nginx Configuration
```nginx
# Hardened nginx config
server {
    listen 443 ssl http2;
    server_name farmwise.example.com;
    
    # SSL/TLS
    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;
    
    # Security Headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Frame-Options "DENY" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;
    
    # Rate Limiting
    limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;
    limit_req zone=api burst=20 nodelay;
    
    # Disable dangerous methods
    if ($request_method !~ ^(GET|HEAD|POST|PUT|DELETE|OPTIONS)$) {
        return 405;
    }
    
    location / {
        proxy_pass http://django:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

#### B. Database Hardening
```sql
-- postgresql security
CREATE ROLE farmwise_app LOGIN PASSWORD 'strong_password_here';
GRANT CONNECT ON DATABASE farmwise_prod TO farmwise_app;
GRANT USAGE ON SCHEMA public TO farmwise_app;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO farmwise_app;

-- Revoke admin access
REVOKE SUPERUSER, CREATEROLE, CREATEDB FROM farmwise_app;

-- Enable audit logging
CREATE EXTENSION pgaudit;
ALTER SYSTEM SET pgaudit.log = 'ALL';
```

---

## 5️⃣ BACKUP & DISASTER RECOVERY

### Backup Strategy: 3-2-1 Rule
- ✅ 3 copies of critical data
- ✅ 2 different storage media
- ✅ 1 copy offsite

### A. Daily Database Backups

```bash
#!/bin/bash
# backup_database.sh - Run daily via cron

BACKUP_DIR="/backups/farmwise"
DB_NAME="farmwise_prod"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/farmwise_$TIMESTAMP.sql.gz"

# Create backup
pg_dump -U farmwise_user -h localhost $DB_NAME | gzip > $BACKUP_FILE

# Verify backup integrity
if gunzip -t $BACKUP_FILE; then
    echo "✓ Backup successful: $BACKUP_FILE"
    
    # Remove backups older than 30 days
    find $BACKUP_DIR -name "*.sql.gz" -mtime +30 -delete
    
    # Upload to S3
    aws s3 cp $BACKUP_FILE s3://farmwise-backups/database/
else
    echo "✗ Backup failed!"
    exit 1
fi
```

### B. Automated Media Files Backup
```bash
#!/bin/bash
# backup_media.sh - Run daily

MEDIA_DIR="/var/www/farmwise/media"
BACKUP_DIR="/backups/farmwise/media"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# Sync to backup location
rsync -av --delete $MEDIA_DIR/ $BACKUP_DIR/

# Sync to S3
aws s3 sync $MEDIA_DIR s3://farmwise-backups/media/

# Sync to backup server (offsite)
rsync -av -e ssh $MEDIA_DIR/ backup-server:/remote-backup/media/
```

### C. Cron Jobs (.*/crontabs/root)
```cron
# Daily backups at 2 AM
0 2 * * * /usr/local/bin/backup_database.sh >> /var/log/backups.log 2>&1
15 2 * * * /usr/local/bin/backup_media.sh >> /var/log/backups.log 2>&1

# Weekly full backup at Sunday 1 AM
0 1 * * 0 /usr/local/bin/backup_full.sh >> /var/log/backups.log 2>&1

# Generate backup report Monday morning
0 6 * * 1 /usr/local/bin/backup_report.sh | mail -s "FarmWise Backup Report" admin@farmwise.com

# Test restore every month
0 3 1 * * /usr/local/bin/test_restore.sh >> /var/log/restore_test.log 2>&1
```

### D. Backup Verification Script
```bash
#!/bin/bash
# backup_verification.sh

BACKUP_DIR="/backups/farmwise"
THRESHOLD_SIZE=1000000  # 1MB minimum

echo "=== BACKUP VERIFICATION REPORT ===" >> /var/log/backup_verification.log
echo "Time: $(date)" >> /var/log/backup_verification.log

for backup in $BACKUP_DIR/*.sql.gz; do
    SIZE=$(stat -f%z "$backup" 2>/dev/null || stat -c%s "$backup" 2>/dev/null)
    
    if [ $SIZE -lt $THRESHOLD_SIZE ]; then
        echo "⚠️  WARNING: Backup too small: $backup ($SIZE bytes)" | mail -s "ALERT: Backup Verification Failed" admin@farmwise.com
    fi
    
    if ! gunzip -t "$backup" 2>/dev/null; then
        echo "❌ CRITICAL: Backup corrupted: $backup" | mail -s "ALERT: Corrupted Backup" admin@farmwise.com
    fi
done

echo "✓ Verification complete" >> /var/log/backup_verification.log
```

---

## 6️⃣ MONITORING & LOGGING

### A. Security Logging
```python
# settings.py
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '[{levelname}] {asctime} {name} {funcName}:{lineno} {message}',
            'style': '{',
        },
        'json': {
            '()': 'pythonjsonlogger.jsonlogger.JsonFormatter',
            'format': '%(asctime)s %(name)s %(levelname)s %(message)s'
        },
    },
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': '/var/log/farmwise/app.log',
            'maxBytes': 10485760,  # 10MB
            'backupCount': 10,
            'formatter': 'verbose',
        },
        'security_file': {
            'level': 'WARNING',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': '/var/log/farmwise/security.log',
            'maxBytes': 10485760,
            'backupCount': 20,
            'formatter': 'json',
        },
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'django.security': {
            'handlers': ['security_file'],
            'level': 'WARNING',
            'propagate': False,
        },
        'core': {
            'handlers': ['file', 'console'],
            'level': 'INFO',
        },
    },
}
```

### B. Monitor Failed Logins
```python
# core/models.py
class LoginAttempt(models.Model):
    user = models.ForeignKey(User, null=True, on_delete=models.SET_NULL)
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField()
    success = models.BooleanField(default=False)
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        indexes = [
            models.Index(fields=['-timestamp']),
            models.Index(fields=['ip_address', '-timestamp']),
        ]
    
    @staticmethod
    def log_failed_attempt(username, ip, user_agent):
        LoginAttempt.objects.create(
            user=User.objects.filter(username=username).first(),
            ip_address=ip,
            user_agent=user_agent,
            success=False
        )
        
        # Alert if > 10 failed attempts from same IP in 1 hour
        recent_failures = LoginAttempt.objects.filter(
            ip_address=ip,
            success=False,
            timestamp__gte=timezone.now() - timedelta(hours=1)
        ).count()
        
        if recent_failures > 10:
            send_admin_alert(f"Possible brute force attack from {ip}")
```

### C. Real-time Monitoring Dashboard
Create `core/admin_views.py`:
```python
@login_required
@user_passes_test(lambda u: u.is_staff)
def security_dashboard(request):
    context = {
        'failed_logins_24h': LoginAttempt.objects.filter(
            success=False,
            timestamp__gte=timezone.now() - timedelta(hours=24)
        ).count(),
        'failed_logins_by_ip': LoginAttempt.objects \
            .filter(success=False) \
            .values('ip_address') \
            .annotate(count=Count('id')) \
            .order_by('-count')[:10],
        'recent_admin_actions': AdminLog.objects.all()[:20],
        'suspicious_activities': SuspiciousActivity.objects.filter(
            resolved=False
        ),
    }
    return render(request, 'admin/security_dashboard.html', context)
```

---

## 7️⃣ INCIDENT RESPONSE PLAN

### Incident Severity Levels

| Level | Example | Response Time | Actions |
|-------|---------|----------------|---------|
| CRITICAL | Data breach, ransomware | 15 min | Activate incident team, isolate systems |
| HIGH | Unauthorized access | 1 hour | Investigate, revoke credentials |
| MEDIUM | Failed backup | 4 hours | Manual fix, monitor closely |
| LOW | Suspicious activity | 1 day | Log and monitor pattern |

### Response Procedures

#### A. Potential Breach Detected
```
1. ISOLATE (Immediate)
   - Take affected server offline
   - Preserve logs
   - DO NOT shut down (preserve evidence)

2. ASSESS (10 min)
   - Determine scope of compromise
   - Check backup integrity
   - Notify incident team

3. CONTAIN (30 min)
   - Revoke all active sessions
   - Force password resets
   - Reset API keys

4. ERADICATE (1-4 hours)
   - Find and patch vulnerability
   - Remove attacker access
   - Close security gaps

5. RECOVER (As needed)
   - Restore from clean backups
   - Rebuild systems if necessary
   - Test functionality

6. POST-MORTEM (24-48 hours)
   - Root cause analysis
   - Communication to affected users
   - Corrective actions
```

#### B. Ransomware Response
1. ✅ DO NOT PAY - Isolate immediately
2. ✅ Restore from backups
3. ✅ Preserve evidence
4. ✅ Report to authorities
5. ✅ Notify users

---

## 8️⃣ COMPLIANCE & AUDITING

### Security Checklist (Monthly)

- [ ] Review failed login attempts (> 10 from one IP?)
- [ ] Check database backups (size, age, integrity)
- [ ] Review admin panel access logs
- [ ] Verify SSL certificate expiry (> 30 days left?)
- [ ] Scan dependencies for vulnerabilities
- [ ] Test 2FA functionality
- [ ] Review user permissions (least privilege?)
- [ ] Verify firewall rules active
- [ ] Check disk space (backups, logs)
- [ ] Review access control policy

### Quarterly Security Audit

```bash
# Run full security analysis
python manage.py check --deploy

# Test password reset flow
# Test 2FA enrollment and usage
# Test API rate limiting
# Test CSRF protection
# Test file upload validation
# Verify HTTPS enforcement
# Check security headers
# Review database encryption
```

---

## 9️⃣ EMERGENCY CONTACTS & PROCEDURES

### On-Call Schedule
- **Primary Security Officer:** [Name] [Phone] [Email]
- **Database Administrator:** [Name] [Phone] [Email]
- **Infrastructure Lead:** [Name] [Phone] [Email]
- **Legal/Compliance:** [Name] [Phone] [Email]

### Escalation Chain
1. Technical team investigates
2. Security officer notified
3. CTO engaged if severity HIGH+
4. Legal notified if data breach
5. Users notified if required

### Communication Plan
- Internal: Slack #security-incidents
- Status page: status.farmwise.com
- Users: Email notification
- Media: Press release (if needed)

---

## 🔟 DEPLOYMENT CHECKLIST

Before going to production:

- [ ] Generate new SECRET_KEY
- [ ] Set DEBUG=False
- [ ] Configure allowed HOSTS
- [ ] Enable HTTPS/SSL
- [ ] Set strong database password
- [ ] Configure Redis for caching
- [ ] Enable 2FA for admins
- [ ] Set up backup scripts
- [ ] Configure monitoring/logging
- [ ] Test disaster recovery
- [ ] Document procedures
- [ ] Train team on procedures
- [ ] Obtain liability insurance
- [ ] Perform security audit
- [ ] Get compliance approval

---

## QUICK REFERENCE COMMANDS

```bash
# Check system security
python manage.py check --deploy

# View failed logins
python manage.py shell
>>> from core.models import LoginAttempt
>>> LoginAttempt.objects.filter(success=False).order_by('-timestamp')[:20]

# Test backup restoration
pg_restore -U farmwise_user -d backup_test /backups/farmwise_latest.sql.gz

# Check SSL certificate
openssl x509 -in /etc/ssl/certs/cert.pem -text -noout

# Monitor system resources
# Linux: top, df -h, netstat -tuln
# Windows: tasklist, Get-Volume, netstat

# View logs
tail -f /var/log/farmwise/app.log
tail -f /var/log/farmwise/security.log
```

---

**Last Review:** April 11, 2026  
**Next Review:** July 11, 2026 (Quarterly)  
**Owner:** Security Team  
**Distribution:** All Administrators
