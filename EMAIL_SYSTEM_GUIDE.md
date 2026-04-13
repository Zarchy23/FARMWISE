# FarmWise Health Reminder Email System - Implementation Guide

## Overview

The Health Reminder Email System is a comprehensive automated solution for sending health management reminders and alerts to farmers and administrators. The system includes:

- **Email Templates** - Branded HTML email templates for different health reminder types
- **Email Service** - Centralized email sending service with multiple reminder types
- **Celery Tasks** - Automated scheduled tasks for sending reminders and alerts
- **Admin Alerts** - Critical alerts for farm administrators and staff
- **Notification Integration** - In-app notifications alongside email reminders
- **Testing Tools** - Management commands for testing the system

## Architecture

### Components

```
┌─────────────────────────────────────────────────────────────┐
│                    Celery Beat Scheduler                     │
│  (Triggers periodic tasks - Daily & Twice Daily)            │
└────────────────┬──────────────────────────────────┬──────────┘
                 │                                  │
    ┌────────────▼─────────────┐      ┌────────────▼─────────────┐
    │ send_health_reminder_     │      │ send_overdue_health_     │
    │      emails()             │      │      emails()            │
    │ (Due in 0-7 days)         │      │ (Overdue - Any days)     │
    └────────────┬──────────────┘      └────────────┬─────────────┘
                 │                                  │
    ┌────────────▼──────────────────────────────────▼──────────┐
    │              HealthRecord Database Query                  │
    │     Filter by next_due_date and animal status            │
    └────────────┬──────────────────────────────────┬──────────┘
                 │                                  │
    ┌────────────▼─────────────┐      ┌────────────▼─────────────┐
    │   EmailService Methods   │      │  AdminAlertService       │
    │ - send_vaccination_*     │      │ - send_critical_alert    │
    │ - send_feed_supp_*       │      │ - send_multiple_overdue  │
    │ - send_health_checkup_*  │      │ - send_email_failure     │
    │ - send_parasite_*        │      └────────────┬─────────────┘
    │ - send_medication_*      │                   │
    └────────────┬─────────────┘                   │
                 │                                  │
    ┌────────────▼──────────────────────────────────▼──────────┐
    │            Email Sending to Users/Admins                 │
    │  (SendGrid or SMTP Backend depending on settings)        │
    └────────────┬──────────────────────────────────┬──────────┘
                 │                                  │
    ┌────────────▼──────────────┐      ┌───────────▼──────────────┐
    │   Create In-App Notifications  │     Create Admin Alerts    │
    │   (For Each User/Farm)         │   (For Staff/Superusers)   │
    └────────────────────────────────┘    └────────────────────────┘
```

## Email Templates

### Available Templates

1. **Vaccination Reminder** (`vaccination_reminder.html`)
   - Subject: 💉 Vaccination Due
   - Content: Animal details, vaccination type, days until due
   - Action Link: Link to health record page

2. **Feed Supplementation Reminder** (`feed_supplementation_reminder.html`)
   - Subject: 🌾 Feed Supplementation Due
   - Content: Supplement details, schedule
   - Action Link: Link to record supplementation

3. **Health Checkup Reminder** (`health_checkup_reminder.html`)
   - Subject: 🏥 Health Checkup Due
   - Content: Checkup type, recommended frequency
   - Action Link: Link to schedule checkup

4. **Parasite Control Reminder** (`parasite_control_reminder.html`)
   - Subject: 🛡️ Parasite Control Due
   - Content: Treatment type, dosage guidelines
   - Action Link: Link to record treatment

5. **General Medication Reminder** (`medication_reminder.html`)
   - Subject: 💊 Medication Reminder
   - Content: Medication name, schedule
   - Action Link: Link to log medication

6. **Urgent Overdue Health** (`urgent_health_overdue.html`)
   - Subject: ⚠️ URGENT: Health Record Overdue
   - Content: Days overdue, critical indicator
   - Action Link: Link to record immediately

### Admin Alert Templates

7. **Critical Health Alert** (`admin_critical_health_alert.html`)
   - Sent when single animal has >14 days overdue health record
   - Recommended actions included

8. **Multiple Overdue Alert** (`admin_multiple_overdue_alert.html`)
   - Sent when farm has 3+ animals with overdue records
   - Aggregate farm-level view

9. **Email Failure Alert** (`admin_email_failure_alert.html`)
   - Sent when email sending system fails
   - Error summary and troubleshooting included

10. **High Priority Alert** (`admin_high_priority_alert.html`)
    - General-purpose alert for critical animal issues
    - Customizable reason field

## Email Service

### EmailService Class

Located in: `core/services/email_service.py`

#### Key Methods

```python
# Vaccination reminder
EmailService.send_vaccination_reminder_email(user, animal, health_record)

# Feed supplementation reminder
EmailService.send_feed_supplementation_reminder_email(user, animal, health_record)

# Health checkup reminder
EmailService.send_health_checkup_reminder_email(user, animal, health_record)

# Parasite control reminder
EmailService.send_parasite_control_reminder_email(user, animal, health_record)

# General medication reminder
EmailService.send_medication_reminder_email(user, animal, health_record)
```

#### Context Variables

Each method passes these variables to the template:
- `user` - The recipient user object
- `animal` - The animal object
- `health_record` - The health record object
- `days_until` - Days until due date
- `action_link` - Deep link to relevant page
- `support_email` - Support email address

## Celery Tasks

### Task: send_health_reminder_emails()

**Schedule:** Daily (24 hours)

**Trigger:** Celery Beat

**Function:**
1. Queries all health records due within 7 days
2. Sends appropriate reminder emails to farm owners
3. Creates in-app notifications
4. Logs all activity

**Returns:** Summary of emails and notifications sent

```
Example: "Sent 12 health reminder emails and 12 notifications"
```

### Task: send_overdue_health_emails()

**Schedule:** Twice daily (12 hours)

**Trigger:** Celery Beat

**Function:**
1. Queries all overdue health records
2. Sends urgent reminder emails to farm owners
3. Creates urgent in-app notifications
4. Checks for critical situations (>14 days overdue)
5. Sends admin alerts if farm has 3+ overdue records
6. Logs all activity

**Returns:** Summary of emails, notifications, and admin alerts sent

```
Example: "Sent 3 overdue health reminder emails and 3 notifications"
```

### Configuration

Tasks are configured in `farmwise/settings.py`:

```python
CELERY_BEAT_SCHEDULE = {
    'send-health-reminder-emails': {
        'task': 'core.tasks.send_health_reminder_emails',
        'schedule': timedelta(hours=24),  # Daily
    },
    'send-overdue-health-emails': {
        'task': 'core.tasks.send_overdue_health_emails',
        'schedule': timedelta(hours=12),  # Twice daily
    },
}
```

## Admin Alert Service

Located in: `core/services/admin_alert_service.py`

### Key Methods

```python
# Send alert for single critical overdue animal
AdminAlertService.send_critical_health_alert(animal, days_overdue)

# Send alert for multiple overdue records on farm
AdminAlertService.send_multiple_overdue_alert(farm, overdue_count)

# Send alert for email sending failures
AdminAlertService.send_email_failure_alert(farm, failed_count, error_summary)

# Send high-priority animal alert
AdminAlertService.send_high_priority_animal_alert(animal, priority_reason)
```

### Alert Recipients

- **Critical Health Alerts** → Farm staff (is_staff=True) + Superusers
- **Multiple Overdue Alerts** → Farm staff + Superusers  
- **Email Failure Alerts** → System superusers only
- **High Priority Alerts** → Farm staff + Superusers

## Integration Points

### Database Models

Health reminders are based on the `HealthRecord` model:

```python
class HealthRecord(models.Model):
    animal = ForeignKey(Animal, on_delete=models.CASCADE)
    record_type = CharField(
        choices=[
            ('vaccination', 'Vaccination'),
            ('feed_supplementation', 'Feed Supplementation'),
            ('health_checkup', 'Health Checkup'),
            ('parasite_control', 'Parasite Control'),
            ('medication', 'Medication'),
        ]
    )
    medication_name = CharField(max_length=255)
    next_due_date = DateField()  # Key field for reminders
    # ... other fields
```

### Notification Model

In-app notifications are created in `Notification` model:

```python
Notification.objects.create(
    user=user,
    notification_type='reminder',  # or 'alert'
    title='...',
    message='...',
    link='/livestock/{animal_id}/'
)
```

## Testing

### Management Command

Test the system with:

```bash
python manage.py test_health_reminder_emails --test-type full
```

#### Options

- `--test-type`: Choose test (full, reminders, overdue, admin-alerts, email-service)
- `--farm-id`: Test with specific farm
- `--animal-id`: Test with specific animal
- `--verbose`: Show detailed output

#### Test Types

1. **email-service** - Tests all email methods
2. **reminders** - Tests send_health_reminder_emails() task
3. **overdue** - Tests send_overdue_health_emails() task
4. **admin-alerts** - Tests admin alert service
5. **full** - Runs all tests (default)

### Manual Testing

```python
# From Django shell
from core.services.email_service import EmailService
from core.models import Animal, HealthRecord

# Get test data
animal = Animal.objects.first()
user = animal.farm.owner
health_record = HealthRecord.objects.filter(animal=animal).first()

# Send test email
EmailService.send_vaccination_reminder_email(user, animal, health_record)
```

## Configuration

### Email Backend

Set in `farmwise/settings.py`:

```python
# Production (SendGrid)
EMAIL_BACKEND = 'sendgrid_backend.SendgridBackend'
SENDGRID_API_KEY = config('SENDGRID_API_KEY')
DEFAULT_FROM_EMAIL = 'noreply@farmwise.com'

# Development (Console)
if DEBUG:
    EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
```

### App URL

For email links to work, set `APP_URL` in settings:

```python
APP_URL = config('APP_URL', default='https://app.farmwise.com')
```

## Monitoring

### Health Check Dashboard

Admins can monitor:
1. Email sending success rates
2. Overdue health records count
3. Failed reminder emails
4. Alert history

### Logs

All activities are logged to `logger` in:
- Email sending: `logger.info()` / `logger.error()`
- Task execution: `logger.info()` / `logger.error()`
- Admin alerts: `logger.info()` / `logger.error()`

### Email Delivery Verification

For SendGrid, you can:
1. Check SendGrid dashboard for bounce/spam
2. Monitor email logs in FarmWise admin panel
3. Review user email settings regularly

## Troubleshooting

### No Emails Sent

1. **Check Celery Status**
   ```bash
   celery -A farmwise inspect active
   ```

2. **Verify Tasks Are Scheduled**
   ```bash
   python manage.py shell
   >>> from django_celery_beat.models import PeriodicTask
   >>> PeriodicTask.objects.all()
   ```

3. **Check Email Backend Configuration**
   - Verify SENDGRID_API_KEY is set
   - Check DEFAULT_FROM_EMAIL value
   - Test email backend: `python manage.py shell` → `send_mail(...)`

4. **Review Celery Logs**
   - Check for task errors
   - Verify task is running at correct time

### Emails Bouncing

1. Check SendGrid bounce report
2. Verify user email addresses are correct
3. Check email templates for broken links

### Admin Alerts Not Sending

1. Verify farm staff/superuser accounts exist
2. Check admin email addresses are set
3. Review AdminAlertService logs

## Performance Considerations

- **Email Volume**: System sends max ~1 email per animal per task
- **Batch Size**: Tasks process all matching records in single batch
- **Rate Limiting**: Consider SendGrid rate limits (500 emails/second)
- **Database Queries**: Optimized with select_related/prefetch_related

## Future Enhancements

Potential improvements:
1. SMS notifications for urgent alerts
2. Email preference/frequency settings per user
3. Custom alert thresholds per farm
4. Report on reminder effectiveness
5. Integration with calendar apps
6. Bulk health record import
7. Email retry mechanism for failures
