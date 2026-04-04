# 🔒 FARMWISE - SECURITY QUICK REFERENCE FOR DEVELOPERS

**Purpose:** Quick lookup guide for security best practices  
**Audience:** All developers  
**Last Updated:** April 4, 2026

---

## 🚨 GOLDEN RULES

### Rule 1: Never Trust User Input
```python
# ❌ BAD - User input directly in query
user_data = request.GET.get('search')
results = User.objects.filter(name=user_data)

# ✅ GOOD - Input validated first
from django.db.models import Q
search = request.GET.get('search', '').strip()
if len(search) < 3 or len(search) > 100:
    return error_response("Invalid search length")
results = User.objects.filter(Q(name__icontains=search))
```

### Rule 2: Always Check Permissions
```python
# ❌ BAD - No ownership check
@login_required
def edit_farm(request, farm_id):
    farm = Farm.objects.get(id=farm_id)
    # User could edit anyone's farm!

# ✅ GOOD - Ownership validation
@login_required
def edit_farm(request, farm_id):
    farm = Farm.objects.get(id=farm_id)
    if farm.owner != request.user and not request.user.is_superuser:
        return HttpResponseForbidden("You don't have permission")
    # Safe to proceed
```

### Rule 3: Use Parameterized Queries
```python
# ❌ BAD - String concatenation (SQL Injection!)
query = f"SELECT * FROM user WHERE username = '{username}'"
cursor.execute(query)

# ✅ GOOD - Parameterized query
cursor.execute("SELECT * FROM user WHERE username = %s", [username])
```

### Rule 4: Escape Output to Template
```python
# ❌ BAD - User input rendered as HTML
{{ user_comment|safe }}  <!-- XSS vulnerability! -->

# ✅ GOOD - Automatic escaping
{{ user_comment }}  <!-- Automatically escaped -->

# When you NEED to render HTML:
{{ user_comment|escape }}
{% autoescape off %}{{ trusted_html }}{% endautoescape %}
```

### Rule 5: Log Security Events
```python
# ✅ ALWAYS LOG:
- Login attempts (success/failure)
- Password changes
- Permission changes
- API key usage
- Data exports
- Admin actions

# ❌ NEVER LOG:
- Passwords
- Credit cards
- Authentication tokens
- Full personal data
```

---

## 📝 VALIDATION CHECKLIST

Before committing code that handles user input:

- [ ] Input length validated (min/max)
- [ ] Input type validated (string/int/date)
- [ ] Special characters handled
- [ ] HTML tags escaped or removed
- [ ] SQL injection protected (parameterized queries)
- [ ] Quotas/rate limits enforced
- [ ] Error messages don't expose internals
- [ ] Output properly escaped in templates

---

## 🔐 AUTHENTICATION & AUTHORIZATION

### Check Current User Permissions
```python
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden

@login_required
def my_view(request):
    # Check specific permission
    if not request.user.has_perm('core.change_farm'):
        return HttpResponseForbidden("No permission")
    
    # Check ownership
    farm = Farm.objects.get(id=farm_id)
    if farm.owner != request.user:
        return HttpResponseForbidden("Not your resource")
```

### User Types
```python
# Check by user type
if request.user.user_type == 'admin':
    # Admin-only code
elif request.user.user_type == 'farmer':
    # Farmer-only code
elif request.user.is_superuser:
    # System admin
```

### CSRF Protection
```html
<!-- ✅ ALWAYS include in forms -->
<form method="POST">
    {% csrf_token %}
    <!-- form fields -->
</form>
```

---

## 🛡️ INPUT VALIDATION

### Text Fields
```python
from django.core.validators import validate_slug
from django.core.exceptions import ValidationError

def validate_text_field(value):
    # Remove HTML
    from django.utils.html import escape
    cleaned = escape(value).strip()
    
    # Check length
    if len(cleaned) < 1 or len(cleaned) > 500:
        raise ValidationError("Invalid length")
    
    # Block SQL keywords
    sql_keywords = ['SELECT', 'DROP', 'INSERT', 'DELETE', 'UNION']
    if any(keyword in cleaned.upper() for keyword in sql_keywords):
        raise ValidationError("Invalid content")
    
    return cleaned
```

### Numeric Fields
```python
def validate_numeric_field(value):
    try:
        num = float(value)
    except (ValueError, TypeError):
        raise ValidationError("Must be a number")
    
    if num < 0 or num > 1000000:
        raise ValidationError("Out of range")
    
    return num
```

### Email Fields
```python
from django.core.validators import EmailValidator

def validate_email_field(email):
    validator = EmailValidator()
    validator(email)
    
    # Check for disposable domains
    disposable_domains = ['mailinator.com', '10minutemail.com']
    domain = email.split('@')[1].lower()
    if domain in disposable_domains:
        raise ValidationError("Disposable email not allowed")
    
    return email
```

### File Uploads
```python
from django.core.exceptions import ValidationError
import magic

def validate_file_upload(file):
    # Check size (5MB max)
    if file.size > 5 * 1024 * 1024:
        raise ValidationError("File too large")
    
    # Check MIME type
    allowed_types = ['image/jpeg', 'image/png', 'image/gif']
    file_mime = magic.from_buffer(file.read(1024), mime=True)
    if file_mime not in allowed_types:
        raise ValidationError("Invalid file type")
    
    # Check for magic bytes
    file.seek(0)
    magic_bytes = file.read(4)
    if not (magic_bytes.startswith(b'\xff\xd8\xff\xe0') or  # JPEG
            magic_bytes.startswith(b'\x89PNG')):  # PNG
        raise ValidationError("Invalid file format")
    
    # Reset file pointer
    file.seek(0)
    return file
```

---

## 🔒 DATABASE SECURITY

### Use Django ORM (Safe)
```python
# ✅ SAFE - Django ORM handles parameterization
User.objects.filter(name='John')
User.objects.raw('SELECT * FROM auth_user WHERE username = %s', [username])
```

### Raw Queries Must Be Parameterized
```python
# ❌ DANGEROUS - String concatenation
query = f"SELECT * FROM user WHERE id = {user_id}"
cursor.execute(query)

# ✅ SAFE - Parameterized
cursor.execute("SELECT * FROM user WHERE id = %s", [user_id])
```

### Sensitive Data in Models
```python
from django.db import models
from cryptography.fernet import Fernet

class User(models.Model):
    # Encrypt at field level
    api_key = models.CharField(max_length=255)  # Store encrypted
    
    def set_api_key(self, key):
        cipher = Fernet(get_encryption_key())
        self.api_key = cipher.encrypt(key.encode()).decode()
    
    def get_api_key(self):
        cipher = Fernet(get_encryption_key())
        return cipher.decrypt(self.api_key.encode()).decode()
```

---

## 🌐 API SECURITY

### Authentication Required
```python
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def my_api_view(request):
    # User must be authenticated
    user = request.user
```

### Check Rate Limiting
```python
from django_ratelimit.decorators import ratelimit

@ratelimit(key='user', rate='100/h', method='GET')
def my_api_view(request):
    # Limited to 100 requests per hour per user
    pass
```

### Validate Request
```python
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_item(request):
    # Validate Content-Type
    if request.content_type != 'application/json':
        return Response({'error': 'Invalid content type'}, status=400)
    
    # Validate request size
    if len(request.body) > 10 * 1024 * 1024:  # 10MB max
        return Response({'error': 'Request too large'}, status=413)
    
    # Validate required fields
    required = ['name', 'description']
    for field in required:
        if field not in request.data:
            return Response({'error': f'{field} required'}, status=400)
```

---

## 📊 LOGGING

### What to Log
```python
import logging
from django.contrib.auth.signals import user_login_failed, user_logged_in

logger = logging.getLogger(__name__)

# Log successful login
@receiver(user_logged_in)
def log_user_login(sender, request, user, **kwargs):
    logger.info(f"User {user.id} logged in from {request.META.get('REMOTE_ADDR')}")

# Log failed login
@receiver(user_login_failed)
def log_failed_login(sender, credentials, request, **kwargs):
    logger.warning(f"Failed login attempt from {request.META.get('REMOTE_ADDR')}")

# Log data changes
@receiver(post_save, sender=Farm)
def log_farm_change(sender, instance, created, **kwargs):
    action = "created" if created else "updated"
    logger.info(f"Farm {instance.id} {action} by user {instance.owner.id}")

# Log permission changes
@receiver(post_save, sender=UserPermission)
def log_permission_change(sender, instance, created, **kwargs):
    action = "granted" if created else "updated"
    logger.info(f"Permission {instance.permission} {action} to user {instance.user.id}")
```

### Never Log
```python
# ❌ BAD - Never log passwords
logger.info(f"User password: {password}")

# ❌ BAD - Never log tokens
logger.debug(f"API token: {token}")

# ✅ GOOD - Log action, not sensitive data
logger.info(f"User password changed")
logger.info(f"API token regenerated")
```

---

## ⚠️ COMMON VULNERABILITIES

### SQL Injection
```python
# ❌ VULNERABLE
query = f"SELECT * FROM users WHERE id = {user_id}"

# ✅ SAFE
User.objects.filter(id=user_id)
```

### Cross-Site Scripting (XSS)
```python
# ❌ VULNERABLE
{{ user_comment|safe }}

# ✅ SAFE
{{ user_comment }}
```

### CSRF Attack
```python
# ❌ VULNERABLE
<form method="POST">
    <input name="amount" value="1000">
</form>

# ✅ SAFE
<form method="POST">
    {% csrf_token %}
    <input name="amount" value="1000">
</form>
```

### Path Traversal
```python
# ❌ VULNERABLE
file_path = request.GET.get('file')
with open(f'uploads/{file_path}') as f:
    # User could request '../../../etc/passwd'

# ✅ SAFE
import os
file_path = os.path.basename(request.GET.get('file'))
allowed_dir = '/path/to/uploads'
full_path = os.path.join(allowed_dir, file_path)
if not full_path.startswith(allowed_dir):
    return error_response("Invalid path")
```

### Command Injection
```python
# ❌ VULNERABLE
import subprocess
filename = request.GET.get('file')
subprocess.run(f'convert {filename} output.jpg')

# ✅ SAFE
subprocess.run(['convert', filename, 'output.jpg'])
```

---

## 🔧 SECURITY CHECKLIST FOR CODE REVIEW

Before approving a PR:

- [ ] All user input validated
- [ ] No SQL injection vulnerabilities
- [ ] No XSS vulnerabilities
- [ ] CSRF protection present on forms
- [ ] Permissions checked before access
- [ ] Ownership validated where needed
- [ ] Passwords never logged
- [ ] Error messages don't expose internals
- [ ] File uploads properly validated
- [ ] Rate limiting considered
- [ ] Security headers present
- [ ] No hardcoded credentials
- [ ] Dependencies up to date

---

## 📚 QUICK LINKS

- **Django Security:** https://docs.djangoproject.com/en/stable/topics/security/
- **OWASP:** https://owasp.org/
- **Main Security Doc:** `SECURITY.md`
- **Checklist:** `SECURITY_IMPLEMENTATION_CHECKLIST.md`

---

## 🚀 Getting Help

For security questions:
1. Check this quick reference first
2. Review main `SECURITY.md` document
3. Ask security lead in team chat
4. For bugs: Report to security@farmwise.local (never public GitHub)

---

**Last Updated:** April 4, 2026
