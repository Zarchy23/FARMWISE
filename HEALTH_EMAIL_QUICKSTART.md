# FarmWise Health Email System - Quick Start Guide

## Quick Setup

### 1. Environment Variables

Ensure these are set in `.env`:

```env
SENDGRID_API_KEY=your_sendgrid_api_key
DEFAULT_FROM_EMAIL=noreply@farmwise.com
APP_URL=https://app.farmwise.com  # or localhost for dev
DEBUG=False  # In production
```

### 2. Start Services

```bash
# Terminal 1: Start Django
python manage.py runserver

# Terminal 2: Start Celery Worker
celery -A farmwise worker -l info

# Terminal 3: Start Celery Beat
celery -A farmwise beat -l info
```

### 3. Verify Setup

```bash
# Check Celery is running
celery -A farmwise inspect active

# Check scheduled tasks
python manage.py shell
>>> from django_celery_beat.models import PeriodicTask
>>> PeriodicTask.objects.filter(name__contains='health').values()
```

## Testing the System

### Option 1: Run Full Test Suite

```bash
python manage.py test_health_reminder_emails --test-type full --verbose
```

### Option 2: Test Individual Components

```bash
# Test email service only
python manage.py test_health_reminder_emails --test-type email-service

# Test reminder task
python manage.py test_health_reminder_emails --test-type reminders

# Test overdue task
python manage.py test_health_reminder_emails --test-type overdue

# Test admin alerts
python manage.py test_health_reminder_emails --test-type admin-alerts
```

### Option 3: Manual Testing

```bash
# Create test data
python manage.py shell

>>> from core.models import Farm, Animal, HealthRecord, AnimalType
>>> from django.utils import timezone
>>> from datetime import timedelta

# Get or create farm
>>> farm = Farm.objects.first()
>>> if not farm: print("Create a farm first!")

# Get or create animal
>>> animal = Animal.objects.filter(farm=farm, status='alive').first()
>>> if not animal: print("Create an animal first!")

# Create health record due soon
>>> today = timezone.now().date()
>>> health_record = HealthRecord.objects.create(
...     animal=animal,
...     record_type='vaccination',
...     medication_name='Live Attenuated Vaccine',
...     dosage='2ml',
...     next_due_date=today + timedelta(days=2)
... )

# Test email sending
>>> from core.services.email_service import EmailService
>>> user = farm.owner
>>> EmailService.send_vaccination_reminder_email(user, animal, health_record)
```

## Monitoring

### Check Email Queue Status

```bash
# In Django shell
from celery.result import AsyncResult

# View pending tasks
celery -A farmwise inspect active

# View task results
from django_celery_results.models import TaskResult
TaskResult.objects.filter(task='core.tasks.send_health_reminder_emails').order_by('-date_done')[:5]
```

### View Email Logs

```bash
# In Django admin
# Navigate to: /admin/django_celery_results/taskresult/

# Or via shell
from django_celery_results.models import TaskResult
tasks = TaskResult.objects.all().order_by('-date_done')[:10]
for task in tasks:
    print(f"{task.task}: {task.status} - {task.result}")
```

## Development Mode Testing

### Using Console Email Backend

```python
# In settings.py for development
if DEBUG:
    EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
```

With this setting, emails print to console instead of sending via SendGrid.

## Production Checklist

- [ ] SENDGRID_API_KEY set in production environment
- [ ] DEFAULT_FROM_EMAIL configured correctly
- [ ] APP_URL points to production domain
- [ ] Celery worker running in background
- [ ] Celery beat scheduler running
- [ ] Email backend set to SendGrid (not console)
- [ ] Error logging configured
- [ ] Admin users have valid email addresses
- [ ] Farm staff users have valid email addresses
- [ ] Database backed up regularly
- [ ] Task results database monitored
- [ ] Email logs monitored for failures

## Debugging

### Common Issues

#### "No health reminder emails sent"

1. Check if health records exist with next_due_date set
2. Verify animal status is 'alive'
3. Check if users have valid email addresses
4. Verify Celery beat is running
5. Check task logs in Django admin

#### "Celery tasks not running"

```bash
# Start Celery beat with timezone
celery -A farmwise beat --scheduler django_celery_beat.schedulers:DatabaseScheduler

# Check scheduled tasks
python manage.py shell
>>> from django_celery_beat.models import PeriodicTask
>>> PeriodicTask.objects.all()
```

#### "SendGrid API key error"

```python
# Verify in Django shell
from django.conf import settings
print(settings.SENDGRID_API_KEY)
print(settings.EMAIL_BACKEND)
```

#### "Admin alerts not sending"

1. Verify superusers/staff users exist
2. Check their email addresses are valid
3. Verify >14 day overdue condition or 3+ farms condition
4. Check AdminAlertService logs

## Files Changed/Added

### Email Templates
- `templates/emails/base_email.html` - Base template
- `templates/emails/vaccination_reminder.html`
- `templates/emails/feed_supplementation_reminder.html`
- `templates/emails/health_checkup_reminder.html`
- `templates/emails/parasite_control_reminder.html`
- `templates/emails/medication_reminder.html`
- `templates/emails/urgent_health_overdue.html`
- `templates/emails/admin_critical_health_alert.html`
- `templates/emails/admin_multiple_overdue_alert.html`
- `templates/emails/admin_email_failure_alert.html`
- `templates/emails/admin_high_priority_alert.html`

### Services
- `core/services/email_service.py` - Added 5 new email methods
- `core/services/admin_alert_service.py` - New admin alert service

### Tasks
- `core/tasks.py` - Added 2 new Celery tasks
  - `send_health_reminder_emails()`
  - `send_overdue_health_emails()`

### Configuration
- `farmwise/settings.py` - Added 2 tasks to CELERY_BEAT_SCHEDULE

### Testing
- `core/management/commands/test_health_reminder_emails.py` - Test management command
- `EMAIL_SYSTEM_GUIDE.md` - Comprehensive documentation

## Next Steps

1. Deploy code to production
2. Configure environment variables
3. Run migration if needed (migrations already created)
4. Restart services
5. Run test suite to verify
6. Monitor first email sends
7. Configure any custom alerts as needed

---

For detailed documentation, see [EMAIL_SYSTEM_GUIDE.md](EMAIL_SYSTEM_GUIDE.md)
