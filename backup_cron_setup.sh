#!/bin/bash
# backup_cron_setup.sh - Set up automated backups on Unix/Linux systems
# Usage: sudo bash backup_cron_setup.sh

set -e

PROJECT_PATH="/var/www/farmwise"
BACKUP_DIR="/backups/farmwise"
LOG_FILE="/var/log/farmwise/backup_setup.log"

echo "[$(date)] Starting backup setup..." | tee -a $LOG_FILE

# Create backup directory
mkdir -p $BACKUP_DIR
mkdir -p /var/log/farmwise
chmod 700 $BACKUP_DIR

echo "[$(date)] Creating backup script..." | tee -a $LOG_FILE

# Create main backup script
cat > /usr/local/bin/farmwise_backup.sh << 'EOF'
#!/bin/bash
# FarmWise Automated Backup Script

PROJECT_PATH="/var/www/farmwise"
BACKUP_DIR="/backups/farmwise"
LOG_FILE="/var/log/farmwise/backup.log"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# Activate virtual environment and run backup
cd $PROJECT_PATH
source venv/bin/activate
python -m core.backup_manager >> $LOG_FILE 2>&1

# Check exit code
if [ $? -eq 0 ]; then
    echo "[$(date)] ✓ Backup successful" >> $LOG_FILE
else
    echo "[$(date)] ✗ Backup failed - sending alert" >> $LOG_FILE
    echo "FarmWise backup failed on $(hostname) at $(date)" | \
        mail -s "ALERT: FarmWise Backup Failed" admin@farmwise.com
fi
EOF

chmod +x /usr/local/bin/farmwise_backup.sh

echo "[$(date)] Creating backup verification script..." | tee -a $LOG_FILE

# Create verification script
cat > /usr/local/bin/farmwise_backup_verify.sh << 'EOF'
#!/bin/bash
# FarmWise Backup Verification Script

BACKUP_DIR="/backups/farmwise"
LOG_FILE="/var/log/farmwise/backup_verify.log"
ALERT_EMAIL="admin@farmwise.com"
THRESHOLD_SIZE=1000000  # 1MB minimum

echo "[$(date)] Starting backup verification..." >> $LOG_FILE

# Check database backups
DB_BACKUP=$(ls -t $BACKUP_DIR/farmwise_db_*.sql.gz 2>/dev/null | head -1)

if [ -z "$DB_BACKUP" ]; then
    echo "[$(date)] ✗ No database backup found!" >> $LOG_FILE
    echo "No database backup found on $(date)" | mail -s "ALERT: No Database Backup" $ALERT_EMAIL
else
    SIZE=$(stat -c%s "$DB_BACKUP" 2>/dev/null)
    AGE=$(($(date +%s) - $(stat -c%Y "$DB_BACKUP")))
    AGE_HOURS=$((AGE / 3600))
    
    if [ $SIZE -lt $THRESHOLD_SIZE ]; then
        echo "[$(date)] ✗ Database backup too small: $SIZE bytes" >> $LOG_FILE
        echo "Database backup is suspiciously small: $SIZE bytes" | \
            mail -s "ALERT: Suspect Database Backup" $ALERT_EMAIL
    fi
    
    if [ $AGE_HOURS -gt 25 ]; then
        echo "[$(date)] ✗ Database backup too old: $AGE_HOURS hours" >> $LOG_FILE
        echo "Database backup is older than 24 hours" | \
            mail -s "ALERT: Stale Database Backup" $ALERT_EMAIL
    fi
    
    # Verify gzip integrity
    if gunzip -t "$DB_BACKUP" >/dev/null 2>&1; then
        echo "[$(date)] ✓ Database backup verified: $SIZE bytes, $AGE_HOURS hours old" >> $LOG_FILE
    else
        echo "[$(date)] ✗ Database backup corrupted!" >> $LOG_FILE
        echo "Database backup appears corrupted at $DB_BACKUP" | \
            mail -s "ALERT: Corrupted Database Backup" $ALERT_EMAIL
    fi
fi

# Check disk space
DISK_USAGE=$(df $BACKUP_DIR | awk 'NR==2 {print $5}' | sed 's/%//')
if [ $DISK_USAGE -gt 80 ]; then
    echo "[$(date)] ✗ Disk usage critical: $DISK_USAGE%" >> $LOG_FILE
    echo "Backup disk usage at $DISK_USAGE%" | \
        mail -s "ALERT: Backup Disk Full" $ALERT_EMAIL
fi

echo "[$(date)] Verification complete" >> $LOG_FILE
EOF

chmod +x /usr/local/bin/farmwise_backup_verify.sh

echo "[$(date)] Setting up cron jobs..." | tee -a $LOG_FILE

# Create crontab entry (for root or www-data user)
CRON_FILE="/tmp/farmwise_crontab.txt"

cat > $CRON_FILE << 'EOF'
# FarmWise Automated Backups
# Database backup daily at 2 AM
0 2 * * * /usr/local/bin/farmwise_backup.sh

# Media backup daily at 3 AM
30 3 * * * /usr/local/bin/farmwise_backup.sh

# Verify backups every morning at 7 AM
0 7 * * * /usr/local/bin/farmwise_backup_verify.sh

# Weekly full test restore on Sunday 4 AM
0 4 * * 0 /usr/local/bin/farmwise_test_restore.sh

# Monthly cleanup of old backups
0 5 1 * * find /backups/farmwise -name "*.sql.gz" -mtime +30 -delete

EOF

# Install cron job
crontab -u www-data $CRON_FILE 2>/dev/null || crontab -u root $CRON_FILE

echo "[$(date)] ✓ Cron jobs installed" | tee -a $LOG_FILE

# Create test restore script
cat > /usr/local/bin/farmwise_test_restore.sh << 'EOF'
#!/bin/bash
# Test restore from latest backup

PROJECT_PATH="/var/www/farmwise"
BACKUP_DIR="/backups/farmwise"
LOG_FILE="/var/log/farmwise/restore_test.log"

echo "[$(date)] Starting restore test..." >> $LOG_FILE

# Get latest database backup
LATEST_BACKUP=$(ls -t $BACKUP_DIR/farmwise_db_*.sql.gz 2>/dev/null | head -1)

if [ -z "$LATEST_BACKUP" ]; then
    echo "[$(date)] ✗ No backup found for restore test" >> $LOG_FILE
    exit 1
fi

# Create test database
TEST_DB="farmwise_restore_test_$(date +%s)"

cd $PROJECT_PATH
source venv/bin/activate

# Attempt restore
createdb -U farmwise_user $TEST_DB 2>/dev/null || true

if gunzip -c $LATEST_BACKUP | psql -U farmwise_user -d $TEST_DB >/dev/null 2>&1; then
    echo "[$(date)] ✓ Restore test successful" >> $LOG_FILE
    # Cleanup test database
    dropdb -U farmwise_user $TEST_DB
else
    echo "[$(date)] ✗ Restore test failed!" >> $LOG_FILE
    dropdb -U farmwise_user $TEST_DB 2>/dev/null || true
    echo "Restore test failed on $(date)" | \
        mail -s "ALERT: Restore Test Failed" admin@farmwise.com
    exit 1
fi
EOF

chmod +x /usr/local/bin/farmwise_test_restore.sh

echo "[$(date)] ✓ Backup automation setup complete!" | tee -a $LOG_FILE
echo "" | tee -a $LOG_FILE
echo "Scheduled backups:" | tee -a $LOG_FILE
echo "  - 2:00 AM: Database backup" | tee -a $LOG_FILE
echo "  - 3:30 AM: Media backup" | tee -a $LOG_FILE
echo "  - 7:00 AM: Backup verification" | tee -a $LOG_FILE
echo "  - 4:00 AM (Sunday): Restore test" | tee -a $LOG_FILE
echo "" | tee -a $LOG_FILE
echo "View backup logs:" | tee -a $LOG_FILE
echo "  tail -f /var/log/farmwise/backup.log" | tee -a $LOG_FILE
echo "  tail -f /var/log/farmwise/backup_verify.log" | tee -a $LOG_FILE

# Verify cron installation
echo "" | tee -a $LOG_FILE
echo "Installed cron jobs:" | tee -a $LOG_FILE
crontab -l 2>/dev/null || echo "Note: Check crontab manually" | tee -a $LOG_FILE

echo "[$(date)] Setup complete!" | tee -a $LOG_FILE
