# FarmWise Scheduler Quick Reference

## Start Scheduler
```bash
python manage.py runscheduler
```

## Run Automations Manually (One-Time)
```bash
python manage.py check_all_dates              # All automations
python manage.py check_crop_dates             # Crop automations only
python manage.py check_livestock_dates        # Livestock automations only
python manage.py check_insurance_renewals     # Insurance automations only
python manage.py check_payroll_payments       # Payroll automations only
```

## View Scheduled Jobs
```bash
python manage.py shell
>>> from core.scheduler import get_scheduled_jobs
>>> for job in get_scheduled_jobs():
...     print(f"{job['name']}: {job['next_run_time']}")
```

## Windows Task Scheduler Setup (Easy)
1. Open Task Scheduler (`Win+R` → `taskschd.msc`)
2. Create Basic Task
3. Name: `FarmWise Scheduler`
4. Trigger: At startup (or daily at 7:00 AM)
5. Action:
   - Program: `c:\Users\Zarchy\farmwise\start_scheduler.bat`
   - Start in: `c:\Users\Zarchy\farmwise`
6. Click Finish

**OR** use PowerShell:
   - Program: `powershell.exe`
   - Arguments: `-ExecutionPolicy Bypass -File c:\Users\Zarchy\farmwise\start_scheduler.ps1`

## What Gets Checked at Each Scheduled Run

✅ **Crops**
- Auto-update status based on planting/harvest dates
- Send reminders 1 day before

✅ **Livestock**
- Health record status updates (pending → overdue)
- Breeding/calving date reminders
- Send emails + in-app notifications

✅ **Insurance**
- Policy status updates (active → expiring_soon → expired)
- Renewal reminders (30, 14, 7, 1 day before)

✅ **Payroll**
- Mark unpaid invoices as pending
- Send payment overdue alerts

## Schedule Configuration
File: `core/scheduler.py`

Current schedule:
- **8:00 AM** - Full daily automation check
- **2:00 PM** - Afternoon check (catch urgent reminders)

To customize, edit the `CronTrigger()` in `add_scheduled_jobs()`:
```python
# Change to 6:00 AM
trigger=CronTrigger(hour=6, minute=0)

# Run every 4 hours 
trigger=CronTrigger(hour='*/4', minute=0)

# Run weekdays only at 9 AM
trigger=CronTrigger(hour=9, minute=0, day_of_week='mon-fri')
```

## Troubleshooting
- **Scheduler not starting?** → Check logs: `python manage.py check`
- **Jobs not running?** → Verify timezone: Check `settings.py` TIME_ZONE
- **Manual check works, scheduled doesn't?** → Restart Windows Task Scheduler
- **Need logs?** → Configure Django logging in `settings.py`

## Files
- `core/scheduler.py` - Scheduler service
- `core/management/commands/runscheduler.py` - CLI command
- `start_scheduler.bat` - Windows batch starter
- `start_scheduler.ps1` - PowerShell starter
- `SCHEDULER_SETUP.md` - Full setup documentation
