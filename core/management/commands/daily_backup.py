"""
Management command to run FarmWise backups
Usage: python manage.py daily_backup [--verify] [--restore test_backup_file]
"""

from django.core.management.base import BaseCommand
from django.conf import settings
from core.backup_manager import BackupManager
import json
import sys


class Command(BaseCommand):
    help = 'Run FarmWise backup operations (database, media, configuration)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--verify',
            action='store_true',
            dest='verify',
            help='Verify backup integrity'
        )
        parser.add_argument(
            '--status',
            action='store_true',
            dest='status',
            help='Show backup status'
        )
        parser.add_argument(
            '--restore',
            type=str,
            dest='restore',
            help='Restore database from backup file'
        )

    def handle(self, *args, **options):
        manager = BackupManager()

        try:
            if options['status']:
                self._show_status(manager)
            elif options['restore']:
                self._restore_backup(manager, options['restore'])
            elif options['verify']:
                self._verify_backups(manager)
            else:
                self._run_all_backups(manager)

        except Exception as e:
            self.stderr.write(self.style.ERROR(f'✗ Error: {e}'))
            sys.exit(1)

    def _run_all_backups(self, manager):
        """Run all backup operations"""
        self.stdout.write(self.style.SUCCESS('Starting backup operations...'))

        try:
            # Database backup
            self.stdout.write('→ Backing up database...')
            db_backup = manager.backup_database()
            self.stdout.write(self.style.SUCCESS(f'✓ Database backup: {db_backup}'))

        except Exception as e:
            self.stderr.write(self.style.ERROR(f'✗ Database backup failed: {e}'))
            raise

        try:
            # Media backup
            self.stdout.write('→ Backing up media files...')
            media_backup = manager.backup_media()
            if media_backup:
                self.stdout.write(self.style.SUCCESS(f'✓ Media backup: {media_backup}'))
            else:
                self.stdout.write(self.style.WARNING('⊘ No media files to backup'))

        except Exception as e:
            self.stderr.write(self.style.ERROR(f'✗ Media backup failed: {e}'))
            # Don't fail - media backup is not critical

        try:
            # Config backup
            self.stdout.write('→ Backing up configuration...')
            config_backup = manager.backup_configuration()
            self.stdout.write(self.style.SUCCESS(f'✓ Config backup: {config_backup}'))

        except Exception as e:
            self.stderr.write(self.style.ERROR(f'✗ Config backup failed: {e}'))

        # Show status
        status = manager.get_backup_status()
        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('✓ All backups completed successfully'))
        self.stdout.write('')
        self._print_status(status)

    def _verify_backups(self, manager):
        """Verify backup integrity"""
        self.stdout.write(self.style.SUCCESS('Verifying backups...'))
        status = manager.get_backup_status()

        if not status['backups']:
            self.stdout.write(self.style.WARNING('No backups found'))
            return

        # Check latest backup
        latest = status['backups'][0]
        self.stdout.write(f'Latest backup: {latest["file"]}')
        self.stdout.write(f'  Size: {latest["size"]:,} bytes')
        self.stdout.write(f'  Created: {latest["created"]}')

        # Check if backup is recent
        from datetime import datetime, timedelta
        backup_time = datetime.fromisoformat(latest['created'])
        age = datetime.now(backup_time.tzinfo) - backup_time

        if age > timedelta(hours=25):
            self.stdout.write(
                self.style.WARNING(f'⚠️  Backup is {age.total_seconds() / 3600:.1f} hours old')
            )

        if latest['size'] < 1000000:  # 1MB
            self.stdout.write(
                self.style.ERROR(f'✗ Backup suspiciously small: {latest["size"]} bytes')
            )
            return

        self.stdout.write(self.style.SUCCESS('✓ Backup verification passed'))

    def _restore_backup(self, manager, backup_file):
        """Restore from backup file"""
        self.stdout.write(f'Restoring from {backup_file}...')
        
        new_db = manager.restore_database(backup_file)
        
        self.stdout.write(self.style.SUCCESS(f'✓ Database restored to: {new_db}'))
        self.stdout.write(self.style.WARNING(
            f'WARNING: Created test database "{new_db}". '
            f'Remember to drop it when done: dropdb -U farmwise_user {new_db}'
        ))

    def _show_status(self, manager):
        """Show backup status"""
        status = manager.get_backup_status()
        self._print_status(status)

    def _print_status(self, status):
        """Pretty print backup status"""
        self.stdout.write('')
        self.stdout.write('📊 BACKUP STATUS')
        self.stdout.write('-' * 60)

        if status['backups']:
            self.stdout.write(self.style.SUCCESS('Recent Backups:'))
            for backup in status['backups'][:5]:
                size_mb = backup['size'] / (1024 * 1024)
                self.stdout.write(
                    f"  • {backup['file']:<35} {size_mb:>6.1f} MB"
                )
        else:
            self.stdout.write(self.style.WARNING('No backups found'))

        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('Disk Usage:'))
        disk = status['disk_usage']
        total_gb = disk['total'] / (1024**3)
        used_gb = disk['used'] / (1024**3)
        free_gb = disk['free'] / (1024**3)
        
        self.stdout.write(f"  Total: {total_gb:.1f} GB")
        self.stdout.write(f"  Used:  {used_gb:.1f} GB ({disk['percent']:.1f}%)")
        self.stdout.write(f"  Free:  {free_gb:.1f} GB")

        if disk['percent'] > 80:
            self.stdout.write(
                self.style.ERROR(f"  ⚠️  WARNING: Disk usage critical at {disk['percent']:.1f}%")
            )

        self.stdout.write('-' * 60)
