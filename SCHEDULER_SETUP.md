# FarmWise Automation Scheduler Setup Guide

## Overview
FarmWise uses APScheduler to run automated task checks daily at **8:00 AM** and **2:00 PM**. This ensures farmers receive timely reminders for:
- Crop planting/harvest dates
- Livestock health checks and breeding dates
- Insurance policy renewals
- Payroll payment reminders

## Current Setup
✅ APScheduler installed  
✅ Management command created: `python manage.py runscheduler`  
✅ Two scheduled jobs configured:
- **8:00 AM** - Daily automation checks
- **2:00 PM** - Afternoon automation checks (for urgent reminders)

---

## Setup Options

### Option 1: Windows Task Scheduler (Recommended)
This allows Windows to automatically start the scheduler at boot.

#### Steps:
1. **Create a Batch File** (`c:\Users\Zarchy\farmwise\start_scheduler.bat`):
```batch
@echo off
cd c:\Users\Zarchy\farmwise
python manage.py runscheduler
```

2. **Open Task Scheduler**:
   - Press `Windows + R` → type `taskschd.msc` → Enter
   - Click **Create Basic Task**

3. **Configure**:
   - **Name**: FarmWise Automation Scheduler
   - **Trigger**: At system startup (or at specific time like 7:00 AM)
   - **Action**: 
     - Program: `python.exe`
     - Arguments: `manage.py runscheduler`
     - Start in: `c:\Users\Zarchy\farmwise`

4. **Optional**: Enable "Run with highest privileges" if needed

---

### Option 2: Run Manually (Development)
```bash
python manage.py runscheduler
```
Keep this terminal open. Scheduler will run in background.

---

### Option 3: Run as Background Service (Production)
Install **NSSM** (Non-Sucking Service Manager):
```bash
# Install NSSM
choco install nssm

# Register service
nssm install FarmWiseScheduler python manage.py runscheduler

# Start service
nssm start FarmWiseScheduler

# View logs
nssm get FarmWiseScheduler AppDirectory
```

---

## Docker/Render Deployment

If deployed to Render or Docker, update your **Procfile**:

```procfile
web: python manage.py migrate && gunicorn farmwise.wsgi
scheduler: python manage.py runscheduler
```

Then in Render dashboard:
1. Add a background worker
2. Set command to: `python manage.py runscheduler`
3. Save & deploy

---

## Monitoring

### Check Scheduler Status
```bash
# View scheduled jobs
python manage.py shell
>>> from core.scheduler import get_scheduled_jobs
>>> jobs = get_scheduled_jobs()
>>> for job in jobs:
...     print(f"{job['name']}: {job['next_run_time']}")
```

### View Logs
Logs are written to Django's logging system. Configure in `settings.py`:
```python
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': 'logs/scheduler.log',
        },
    },
    'loggers': {
        'core.scheduler': {
            'handlers': ['file'],
            'level': 'INFO',
            'propagate': True,
        },
    },
}
```

---

## Customizing Schedule

Edit `core/scheduler.py` to change times:

```python
# Change from 8 AM to 9 AM
scheduler.add_job(
    func=run_all_automations,
    trigger=CronTrigger(hour=9, minute=0),  # Changed from 8 to 9
    id='daily_automations',
    ...
)

# Run every 6 hours
scheduler.add_job(
    func=run_all_automations,
    trigger=CronTrigger(hour='*/6', minute=0),  # Every 6 hours
    ...
)

# Run Monday-Friday at 9 AM
scheduler.add_job(
    func=run_all_automations,
    trigger=CronTrigger(hour=9, minute=0, day_of_week='mon-fri'),
    ...
)
```

---

## Troubleshooting

### Scheduler not running
- Check if process is still running: `tasklist | findstr python`
- Check logs in `logs/scheduler.log`
- Restart with: `python manage.py runscheduler`

### Jobs not executing
- Verify timezone in `settings.py`: `TIME_ZONE = 'Africa/Nairobi'`
- Check next run time matches your timezone

### Windows Firewall Issues
- Go to Settings → Firewall → Allow an app
- Add Python to allowed apps

---

## Automation Checks Run
Each scheduled job executes: `python manage.py check_all_dates`

This checks:
✅ Crop planting/harvest dates  
✅ Livestock health and breeding schedules  
✅ Insurance policy renewals  
✅ Payroll payment due dates  

Results sent via in-app notifications + emails.

---

## Support
For issues, check:
- `logs/scheduler.log` (if configured)
- Django logs: `logs/django.log`
- Run manually: `python manage.py check_all_dates`
