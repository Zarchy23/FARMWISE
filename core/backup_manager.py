#!/usr/bin/env python
"""
backup_manager.py - Comprehensive backup automation for FarmWise

Handles:
- PostgreSQL database backups
- Media files backups
- Backup verification
- S3 cloud storage
- Email notifications
"""

import os
import sys
import gzip
import json
import shutil
import subprocess
import logging
from datetime import datetime, timedelta
from pathlib import Path
import boto3
from decouple import config


# Configure logging
log_dir = Path(config('LOG_DIR', default='logs'))
log_dir.mkdir(parents=True, exist_ok=True)
log_file = log_dir / 'backup.log'

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler(str(log_file)),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


class BackupManager:
    """Manages database, media, and configuration backups"""
    
    def __init__(self):
        self.db_name = config('DB_NAME', default='farmwise_prod')
        self.db_user = config('DB_USER', default='farmwise_user')
        self.db_host = config('DB_HOST', default='localhost')
        self.db_port = config('DB_PORT', default='5432')
        self.backup_dir = Path(config('BACKUP_DIR', default='/backups/farmwise'))
        self.media_dir = Path(config('MEDIA_ROOT', default='/var/www/farmwise/media'))
        self.s3_bucket = config('S3_BACKUP_BUCKET', default='farmwise-backups')
        self.aws_region = config('AWS_REGION', default='us-east-1')
        
        # Create backup directories
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize S3
        self.s3_client = boto3.client('s3', region_name=self.aws_region) if self.s3_bucket else None
        
    def backup_database(self):
        """Backup PostgreSQL database"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_file = self.backup_dir / f'farmwise_db_{timestamp}.sql.gz'
        
        logger.info(f"Starting database backup to {backup_file}")
        
        try:
            # Create dump
            with open(backup_file, 'wb') as f:
                process = subprocess.Popen(
                    [
                        'pg_dump',
                        '-U', self.db_user,
                        '-h', self.db_host,
                        '-p', self.db_port,
                        self.db_name
                    ],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE
                )
                
                with gzip.GzipFile(fileobj=f, mode='wb') as gz:
                    gz.write(process.stdout.read())
                
                stderr = process.stderr.read().decode()
                if process.wait() != 0:
                    raise Exception(f"pg_dump failed: {stderr}")
            
            # Verify backup
            if not self._verify_backup(backup_file):
                raise Exception("Backup verification failed")
            
            file_size = backup_file.stat().st_size
            logger.info(f"✓ Database backup successful: {file_size:,} bytes")
            
            # Upload to S3
            if self.s3_client:
                self._upload_to_s3(backup_file, 'database/')
            
            # Cleanup old backups
            self._cleanup_old_backups('farmwise_db_*.sql.gz', retention_days=30)
            
            return str(backup_file)
            
        except Exception as e:
            logger.error(f"✗ Database backup failed: {e}")
            self._send_alert(f"Database backup failed: {e}")
            raise
    
    def backup_media(self):
        """Backup media files"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Use .zip for Windows, .tar.gz for Linux
        if sys.platform == 'win32':
            backup_file = self.backup_dir / f'farmwise_media_{timestamp}.zip'
            format_type = 'zip'
        else:
            backup_file = self.backup_dir / f'farmwise_media_{timestamp}.tar.gz'
            format_type = 'gztar'
        
        logger.info(f"Starting media backup to {backup_file}")
        
        try:
            if not self.media_dir.exists():
                logger.warning(f"Media directory not found: {self.media_dir}")
                return None
            
            # Create archive
            shutil.make_archive(
                str(backup_file.with_suffix('')),
                format_type,
                self.media_dir.parent,
                self.media_dir.name
            )
            
            file_size = backup_file.stat().st_size
            logger.info(f"✓ Media backup successful: {file_size:,} bytes")
            
            # Upload to S3
            if self.s3_client:
                self._upload_to_s3(backup_file, 'media/')
            
            # Cleanup old backups
            pattern = 'farmwise_media_*.zip' if sys.platform == 'win32' else 'farmwise_media_*.tar.gz'
            self._cleanup_old_backups(pattern, retention_days=14)
            
            return str(backup_file)
            
        except Exception as e:
            logger.error(f"✗ Media backup failed: {e}")
            self._send_alert(f"Media backup failed: {e}")
            raise
    
    def backup_configuration(self):
        """Backup environment and configuration"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_file = self.backup_dir / f'farmwise_config_{timestamp}.json'
        
        logger.info(f"Starting config backup to {backup_file}")
        
        try:
            config_data = {
                'timestamp': timestamp,
                'database': {
                    'name': self.db_name,
                    'user': self.db_user,
                    'host': self.db_host,
                },
                'backup_dir': str(self.backup_dir),
                'media_dir': str(self.media_dir),
                's3_bucket': self.s3_bucket,
            }
            
            with open(backup_file, 'w') as f:
                json.dump(config_data, f, indent=2)
            
            logger.info(f"✓ Config backup successful")
            
            if self.s3_client:
                self._upload_to_s3(backup_file, 'configuration/')
            
            return str(backup_file)
            
        except Exception as e:
            logger.error(f"✗ Config backup failed: {e}")
            raise
    
    def restore_database(self, backup_file, target_db=None):
        """Restore database from backup"""
        target_db = target_db or f"{self.db_name}_restore"
        
        logger.info(f"Restoring database from {backup_file}")
        
        try:
            # Create new database
            subprocess.run(
                ['createdb', '-U', self.db_user, '-h', self.db_host, target_db],
                check=False
            )
            
            # Restore from backup
            with gzip.open(backup_file, 'rb') as f:
                process = subprocess.Popen(
                    [
                        'psql',
                        '-U', self.db_user,
                        '-h', self.db_host,
                        '-d', target_db
                    ],
                    stdin=f,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE
                )
                
                stdout, stderr = process.communicate()
                if process.returncode != 0:
                    raise Exception(f"Restore failed: {stderr.decode()}")
            
            logger.info(f"✓ Database restored to {target_db}")
            return target_db
            
        except Exception as e:
            logger.error(f"✗ Database restore failed: {e}")
            raise
    
    def _verify_backup(self, backup_file):
        """Verify backup integrity"""
        try:
            with gzip.open(backup_file, 'rb') as f:
                f.read(1024)  # Read first 1KB to verify gzip
            return True
        except Exception as e:
            logger.error(f"Backup verification failed: {e}")
            return False
    
    def _upload_to_s3(self, file_path, s3_prefix):
        """Upload backup to S3"""
        try:
            file_size = Path(file_path).stat().st_size
            file_name = Path(file_path).name
            s3_key = f"{s3_prefix}{file_name}"
            
            logger.info(f"Uploading to S3: s3://{self.s3_bucket}/{s3_key}")
            
            self.s3_client.upload_file(
                str(file_path),
                self.s3_bucket,
                s3_key,
                ExtraArgs={'StorageClass': 'GLACIER_IR'}  # Cost-effective
            )
            
            logger.info(f"✓ S3 upload successful")
            
        except Exception as e:
            logger.error(f"✗ S3 upload failed: {e}")
            # Don't raise - local backup succeeded
    
    def _cleanup_old_backups(self, pattern, retention_days):
        """Remove old backup files"""
        cutoff_time = datetime.now() - timedelta(days=retention_days)
        
        for backup_file in self.backup_dir.glob(pattern):
            file_time = datetime.fromtimestamp(backup_file.stat().st_mtime)
            
            if file_time < cutoff_time:
                try:
                    backup_file.unlink()
                    logger.info(f"Deleted old backup: {backup_file.name}")
                except Exception as e:
                    logger.error(f"Failed to delete {backup_file.name}: {e}")
    
    def _send_alert(self, message):
        """Send email alert"""
        # TODO: Implement email alert via Celery task
        logger.warning(f"ALERT: {message}")
    
    def get_backup_status(self):
        """Get current backup status"""
        status = {
            'timestamp': datetime.now().isoformat(),
            'backups': [],
            'disk_usage': {},
        }
        
        for backup_file in sorted(self.backup_dir.glob('farmwise_*')):
            status['backups'].append({
                'file': backup_file.name,
                'size': backup_file.stat().st_size,
                'created': datetime.fromtimestamp(backup_file.stat().st_mtime).isoformat(),
                'type': backup_file.stem.split('_')[2] if len(backup_file.stem.split('_')) > 2 else 'unknown'
            })
        
        # Disk usage
        stat = shutil.disk_usage(self.backup_dir)
        status['disk_usage'] = {
            'total': stat.total,
            'used': stat.used,
            'free': stat.free,
            'percent': (stat.used / stat.total * 100) if stat.total > 0 else 0
        }
        
        return status


def main():
    """Execute backups"""
    manager = BackupManager()
    
    try:
        # Run all backups
        logger.info("=" * 60)
        logger.info("FarmWise Backup Manager Started")
        logger.info("=" * 60)
        
        db_backup = manager.backup_database()
        media_backup = manager.backup_media()
        config_backup = manager.backup_configuration()
        
        # Get status
        status = manager.get_backup_status()
        logger.info(f"Backup Status: {json.dumps(status, indent=2)}")
        
        # Alert if disk usage > 80%
        if status['disk_usage']['percent'] > 80:
            logger.warning(f"⚠️  Disk usage at {status['disk_usage']['percent']:.1f}%")
            manager._send_alert(f"Backup disk usage at {status['disk_usage']['percent']:.1f}%")
        
        logger.info("✓ All backups completed successfully")
        return 0
        
    except Exception as e:
        logger.error(f"✗ Backup failed: {e}")
        return 1


if __name__ == '__main__':
    sys.exit(main())
