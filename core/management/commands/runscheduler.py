"""
Django management command to start the APScheduler background scheduler
Usage: python manage.py runscheduler
"""
from django.core.management.base import BaseCommand
from core.scheduler import start_scheduler, stop_scheduler, get_scheduled_jobs
import signal
import sys
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Start the APScheduler background scheduler for automated FarmWise tasks'
    
    def handle(self, *args, **options):
        # Start the scheduler
        scheduler = start_scheduler()
        
        if scheduler is None:
            self.stdout.write(self.style.ERROR("✗ Failed to start scheduler"))
            sys.exit(1)
        
        # Display scheduled jobs
        self.stdout.write(self.style.SUCCESS("\n" + "=" * 70))
        self.stdout.write(self.style.SUCCESS("FARMWISE AUTOMATION SCHEDULER STARTED"))
        self.stdout.write(self.style.SUCCESS("=" * 70))
        
        jobs = get_scheduled_jobs()
        if jobs:
            self.stdout.write(self.style.WARNING("\nScheduled Jobs:"))
            for job in jobs:
                self.stdout.write(f"\n  ID: {job['id']}")
                self.stdout.write(f"  Name: {job['name']}")
                self.stdout.write(f"  Next Run: {job['next_run_time']}")
                self.stdout.write(f"  Trigger: {job['trigger']}")
        
        self.stdout.write(self.style.SUCCESS("\n" + "=" * 70))
        self.stdout.write("\nScheduler is running. Press Ctrl+C to stop.\n")
        
        # Set up signal handlers to gracefully shutdown
        def signal_handler(signum, frame):
            self.stdout.write(self.style.WARNING("\n\nShutting down scheduler..."))
            stop_scheduler()
            self.stdout.write(self.style.SUCCESS("✓ Scheduler stopped"))
            sys.exit(0)
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        # Keep the command running
        while True:
            try:
                # Sleep to avoid busy waiting
                import time
                time.sleep(1)
            except KeyboardInterrupt:
                stop_scheduler()
                break
