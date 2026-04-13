# 🔄 AUTOMATIC BACKUP SETUP - 3 OPTIONS

**Choose the option that works best for you:**

---

## 🎯 OPTION 1: Python Scheduler (Easiest, No Admin Needed)

This runs backups automatically without Task Scheduler. Just keep a window open.

### Setup (2 minutes):
```powershell
# Run this once
python run_backup_scheduler.py
```

A window will stay open showing:
- Backup running at 2:00 AM
- Verification running at 7:00 AM

### How to keep it running:
1. **While developing:** Keep terminal open
2. **In production:** Use Windows Service or `nssm` to run as background service

### Logs:
- View: `logs\scheduler.log`

**Pros:** No admin needed, simple, works immediately  
**Cons:** Window must stay open

---

## ⏰ OPTION 2: Windows Task Scheduler (Best for Production)

Automatic, runs without keeping window open.

### Setup (Admin Required - Run Once):

**Method A - Using Batch File:**
```powershell
# Right-click Command Prompt → "Run as Administrator"
cd C:\Users\Zarchy\farmwise
.\setup_backups.bat
```

**Method B - Manual via Task Scheduler:**

1. Open Task Scheduler (Start → Task Scheduler)
2. Click "Create Basic Task"
3. Name: `FarmWise-Backup`
4. Trigger: Daily @ 2:00 AM
5. Action: Start a program
   - Program: `C:\Users\Zarchy\farmwise\venv\Scripts\python.exe`
   - Arguments: `manage.py daily_backup`
   - Start in: `C:\Users\Zarchy\farmwise`

6. Repeat for verify:
   - Name: `FarmWise-Verify`
   - Trigger: Daily @ 7:00 AM
   - Arguments: `manage.py daily_backup --verify`

### Verify it worked:
```powershell
schtasks /query | findstr FarmWise
```

**Pros:** Professional, runs in background, no window  
**Cons:** Requires admin setup once

---

## 🔧 OPTION 3: Windows Service (Advanced)

Run scheduler as Windows Service (stays running after reboot).

### Setup (requires `nssm` tool):
```powershell
# Download nssm from: https://nssm.cc/download
# Extract to C:\nssm

# Then run as Administrator:
C:\nssm\nssm.exe install FarmWiseBackupService "C:\Users\Zarchy\farmwise\venv\Scripts\python.exe" "run_backup_scheduler.py"
```

### Start service:
```powershell
net start FarmWiseBackupService
```

**Pros:** Professional, auto-restart on reboot  
**Cons:** Most complex, requires NSSM tool

---

## 📋 QUICK COMPARISON

| Feature | Option 1 (Python) | Option 2 (Task Scheduler) | Option 3 (Service) |
|---------|------------------|--------------------------|-------------------|
| **Admin needed?** | No | Yes (once) | Yes (once) |
| **Runs automatically** | If window open | Yes | Yes |
| **Survives reboot** | No | Yes | Yes |
| **Setup time** | 1 min | 3 min | 5 min |
| **Complexity** | Easy | Medium | Advanced |
| **For development** | ✅ Best | - | - |
| **For production** | - | ✅ Best | ✅ Best |

---

## 🚀 RECOMMENDED

### For Development:
```bash
python run_backup_scheduler.py
```
Keep terminal open while working.

### For Production:
Ask IT to run setup once:
```powershell
.\setup_backups.bat
```
Then backups run automatically 24/7.

---

## 📊 What Gets Backed Up

Every backup run includes:
- ✅ **Database** (PostgreSQL) → gzip compressed
- ✅ **Media files** → ZIP archive
- ✅ **Configuration** → JSON file
- ✅ **Location:** `C:\Backups\farmwise\`
- ✅ **Retention:** Last 30 days (auto-cleanup)

---

## 🔍 Monitor Backups

### Check status anytime:
```bash
python manage.py daily_backup --status
```

### View all backups:
```powershell
dir C:\Backups\farmwise\
```

### Check logs:
```powershell
cat logs\backup.log        # Recent backups
cat logs\scheduler.log     # Scheduler activity
```

---

## ⚠️ Important Notes

### If using Python Scheduler:
- Keep terminal window open (or minimize it)
- Script checks every 60 seconds for scheduled time
- Logs everything to `logs\scheduler.log`

### If using Task Scheduler:
- Double-check paths in task properties
- Verify task runs with correct permissions
- Check Event Viewer if task doesn't run

### Always:
- Backup location must exist: `C:\Backups\farmwise\`
- Virtual environment must be activated
- Database must be running

---

## 🎯 NEXT STEPS

1. **Choose one option above**
2. **Run the setup**
3. **Test manually:** `python manage.py daily_backup`
4. **Check logs:** examine `logs\backup.log`
5. **Monitor for 24 hours** to see if automatic run happens

---

## 💡 MANUAL BACKUP (Anytime)

You can always run backups manually without scheduler:
```bash
python manage.py daily_backup
```

This works whether automatic scheduler is set up or not.

---

**Questions?** Check previous documentation:
- `BACKUP_AND_SECURITY_SETUP.md`
- `PHASE_1_COMPLETION_SUMMARY.md`
