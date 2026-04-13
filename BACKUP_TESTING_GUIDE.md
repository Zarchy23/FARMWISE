# 🧪 BACKUP TESTING & VERIFICATION GUIDE

Run these commands to verify everything works correctly.

---

## ✅ STEP 1: Test Manual Backup

Run a backup right now to verify the system works:

```powershell
python manage.py daily_backup
```

**Expected Output:**
```
✓ Starting backup process...
✓ Backing up database... [46.7 KB]
✓ Backing up media files... [3.7 MB]
✓ Backing up configuration... [255 B]

✓ All backups completed successfully!
Backup time: 45 seconds
Total size: 3.7 MB

Backups saved to: C:\Backups\farmwise\
```

---

## 📋 STEP 2: Check Backup Status

See what backups exist and when they ran:

```powershell
python manage.py daily_backup --status
```

**Expected Output:**
```
=== FarmWise Backup Status ===

📁 Backup Directory: c:\Users\Zarchy\farmwise\.\backup_files
💿 Disk Usage: 47.6% (232.6 GB free)

Database Backups:
  - farmwise_db_20250121_140532.sql.gz (46.7 KB) - 2025-01-21 14:05:32

Media Backups:
  - farmwise_media_20250121_140533.zip (3.7 MB) - 2025-01-21 14:05:33

Config Backups:
  - farmwise_config_20250121_140534.json (255 B) - 2025-01-21 14:05:34

✓ All backup types present and recent
✓ Verification: All backup files are valid
```

---

## 🔐 STEP 3: Verify Backup Integrity

Make sure backup files aren't corrupted:

```powershell
python manage.py daily_backup --verify
```

**Expected Output:**
```
✓ Verifying backup integrity...

Checking database backup... ✓ Valid (46.7 KB)
Checking media backup... ✓ Valid (3.7 MB)
Checking config backup... ✓ Valid (255 B)

✓ All backups verified successfully!
```

---

## 📂 STEP 4: View All Backup Files

See the actual backup files on disk:

```powershell
dir C:\Backups\farmwise\
```

**Expected Output:**
```
Directory: C:\Backups\farmwise

Mode  LastWriteTime        Length  Name
----  ---------------        ------  ----
-a--- 2025-01-21 14:05:32   46752  farmwise_db_20250121_140532.sql.gz
-a--- 2025-01-21 14:05:33  3897654 farmwise_media_20250121_140533.zip
-a--- 2025-01-21 14:05:34     255  farmwise_config_20250121_140534.json
```

---

## 🔄 STEP 5: Test Restore Process

**⚠️ IMPORTANT:** This creates a TEST database, not overwrites production!

```powershell
python manage.py daily_backup --restore [backup_file]
```

**Example - Restore the most recent backup:**
```powershell
$ ls C:\Backups\farmwise\*.sql.gz | Sort-Object -Descending | Select-Object -First 1 | ForEach-Object {
    python manage.py daily_backup --restore $_.Name
}
```

**Expected Output:**
```
✓ Starting restore test...
✓ Loading backup: farmwise_db_20250121_140532.sql.gz
✓ Creating test restore connection...
✓ Restoring database to: test_farmwise_restore_20250121_140532
✓ Executing restore query... (this may take a minute)
✓ Testing data integrity...
  - 150 users found
  - 45 farms found
  - 1,234 sensor readings found
✓ Restore test successful! (test database will auto-delete)

✓ Restore verified successfully!
```

---

## 📊 STEP 6: Check Backup Logs

View detailed backup history:

```powershell
cat logs\backup.log
```

**Should show entries like:**
```
2025-01-21 14:05:30 - Starting backup process
2025-01-21 14:05:31 - Backup database: 46.7 KB
2025-01-21 14:05:33 - Backup media: 3.7 MB
2025-01-21 14:05:34 - Backup complete
```

---

## 🔄 STEP 7: Test Scheduler (If Using Option 1)

If you choose to use the Python scheduler, test it:

```powershell
# Start scheduler
python run_backup_scheduler.py
```

**Expected Output:**
```
🔄 Starting FarmWise Backup Scheduler...
⏰ Backup time: 02:00 AM
♻️  Verification time: 07:00 AM
📝 Logs: logs\scheduler.log

Waiting for scheduled times... (press Ctrl+C to stop)
```

Then check it's logging (keep running for ~2 hours to see it work):
```powershell
tail -f logs\scheduler.log
```

---

## 🎯 COMPLETE TEST SEQUENCE

Run these in order to fully test the backup system:

```powershell
# 1. Manual backup
python manage.py daily_backup

# 2. Check status
python manage.py daily_backup --status

# 3. Verify integrity
python manage.py daily_backup --verify

# 4. List files
dir C:\Backups\farmwise\

# 5. View logs
cat logs\backup.log

# 6. (Optional) Test restore
python manage.py daily_backup --restore [filename]
```

---

## ✅ SUCCESS CHECKLIST

After running tests, verify:

- [ ] Manual backup runs successfully
- [ ] Backups appear in `C:\Backups\farmwise\`
- [ ] Three backup types exist: .sql.gz, .zip, .json
- [ ] Status command shows all backups
- [ ] Verify command passes all files
- [ ] Logs show backup history
- [ ] Restore test shows data integrity
- [ ] `logs\backup.log` contains entries

---

## ⚠️ TROUBLESHOOTING

### Backup fails with database error:
```powershell
# Check PostgreSQL is running
pg_isready -h localhost -p 5432
```

### Backup fails with permission error:
```powershell
# Check backup directory exists
test-path C:\Backups\farmwise\
# If not:
mkdir C:\Backups\farmwise
```

### Backup files are too large:
```powershell
# Check media directory
dir media\ -Recurse -File | Measure-Object -Sum Length
```

### Old backups not deleting:
```powershell
# Check log for cleanup
cat logs\backup.log | grep -i "cleanup"
```

---

## 📞 EXPECTED BEHAVIOR

✅ **First backup:** Will be larger (full dump)  
✅ **Subsequent backups:** Similar size (incremental changes)  
✅ **Backup frequency:** Daily at configured time  
✅ **Verification:** Runs automatically after backup  
✅ **Old backups:** Auto-delete after 30 days (configurable)  
✅ **Restore test:** Creates test DB, auto-deletes after test  

---

**Your backups are working when you see:** ✅ All 3 backup types in `C:\Backups\farmwise\`
