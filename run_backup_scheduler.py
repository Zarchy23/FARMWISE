#!/usr/bin/env python
"""
run_backup_scheduler.py - Automatic backup scheduler for FarmWise
Runs in background and executes backups on schedule.
Does NOT require Windows Task Scheduler admin privileges.

Usage:
    python run_backup_scheduler.py
    (Keep this window open, or run as background service)
"""

import os
import sys
import time
import logging
from datetime import datetime, time as dt_time
from pathlib import Path

# Add project to path
sys.path.insert(0, str(Path(__file__).parent))

# Django setup
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'farmwise.settings')
import django
django.setup()

from django.core.management import call_command
from django.conf import settings


# Configure logging
log_dir = Path(settings.BASE_DIR) / 'logs'
log_dir.mkdir(parents=True, exist_ok=True)
log_file = log_dir / 'scheduler.log'

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler(str(log_file)),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


class BackupScheduler:
    """Simple scheduler for backup tasks"""
    
    def __init__(self):
        self.backup_time = dt_time(2, 0)  # 2:00 AM
        self.verify_time = dt_time(7, 0)  # 7:00 AM
        self.last_backup_date = None
        self.last_verify_date = None
        
    def should_run_backup(self):
        """Check if backup should run"""
        now = datetime.now()
        today = now.date()
        
        # Run if we haven't run today and it's past backup time
        if self.last_backup_date != today and now.time() >= self.backup_time:
            return True
        return False
    
    def should_run_verify(self):
        """Check if verification should run"""
        now = datetime.now()
        today = now.date()
        
        # Run if we haven't run today and it's past verify time
        if self.last_verify_date != today and now.time() >= self.verify_time:
            return True
        return False
    
    def run_backup(self):
        """Execute backup"""
        logger.info("=" * 60)
        logger.info("Starting scheduled backup...")
        logger.info("=" * 60)
        try:
            call_command('daily_backup')
            self.last_backup_date = datetime.now().date()
            logger.info("✓ Backup completed successfully")
        except Exception as e:
            logger.error(f"✗ Backup failed: {e}")
    
    def run_verify(self):
        """Execute backup verification"""
        logger.info("=" * 60)
        logger.info("Starting scheduled backup verification...")
        logger.info("=" * 60)
        try:
            call_command('daily_backup', verify=True)
            self.last_verify_date = datetime.now().date()
            logger.info("✓ Backup verification completed")
        except Exception as e:
            logger.error(f"✗ Backup verification failed: {e}")
    
    def run(self):
        """Main scheduler loop"""
        logger.info("")
        logger.info("╔════════════════════════════════════════╗")
        logger.info("║  FarmWise Backup Scheduler Started    ║")
        logger.info("║                                        ║")
        logger.info("║  Backup scheduled: Daily 2:00 AM      ║")
        logger.info("║  Verify scheduled: Daily 7:00 AM      ║")
        logger.info("║                                        ║")
        logger.info("║  Keep this window open!                ║")
        logger.info("╚════════════════════════════════════════╝")
        logger.info("")
        
        try:
            while True:
                now = datetime.now()
                
                # Check if backup should run
                if self.should_run_backup():
                    logger.info(f"[{now.strftime('%H:%M:%S')}] Backup time reached - executing...")
                    self.run_backup()
                
                # Check if verification should run
                if self.should_run_verify():
                    logger.info(f"[{now.strftime('%H:%M:%S')}] Verification time reached - executing...")
                    self.run_verify()
                
                # Sleep for 1 minute before checking again
                time.sleep(60)
                
        except KeyboardInterrupt:
            logger.info("Scheduler stopped by user")
        except Exception as e:
            logger.error(f"Scheduler error: {e}", exc_info=True)


if __name__ == '__main__':
    scheduler = BackupScheduler()
    scheduler.run()
