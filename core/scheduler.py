"""
Django APScheduler Integration - Automated Task Scheduling
Handles scheduled automation checks for all FarmWise features
"""
import logging
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from django.core.management import call_command
from django.conf import settings

logger = logging.getLogger(__name__)

# Global scheduler instance
scheduler = None


def start_scheduler():
    """Initialize and start the APScheduler background scheduler"""
    global scheduler
    
    if scheduler is not None and scheduler.running:
        logger.info("Scheduler is already running")
        return scheduler
    
    try:
        scheduler = BackgroundScheduler()
        
        # Add scheduled jobs
        add_scheduled_jobs()
        
        # Start the scheduler
        scheduler.start()
        logger.info("✓ APScheduler started successfully")
        return scheduler
    except Exception as e:
        logger.error(f"✗ Failed to start APScheduler: {str(e)}")
        return None


def add_scheduled_jobs():
    """Add all automation jobs to the scheduler"""
    
    # Daily automation check at 8 AM
    scheduler.add_job(
        func=run_all_automations,
        trigger=CronTrigger(hour=8, minute=0),
        id='daily_automations',
        name='Daily FarmWise Automations (8:00 AM)',
        replace_existing=True,
        timezone=settings.TIME_ZONE,
    )
    logger.info("Added job: Daily automations at 8:00 AM")
    
    # Optional: Additional checks at 2 PM for urgent reminders
    scheduler.add_job(
        func=run_all_automations,
        trigger=CronTrigger(hour=14, minute=0),
        id='afternoon_automations',
        name='Afternoon FarmWise Automations (2:00 PM)',
        replace_existing=True,
        timezone=settings.TIME_ZONE,
    )
    logger.info("Added job: Afternoon automations at 2:00 PM")


def run_all_automations():
    """Execute all automation checks"""
    try:
        logger.info("▸ Starting scheduled automation checks...")
        call_command('check_all_dates')
        logger.info("✓ Automation checks completed successfully")
    except Exception as e:
        logger.error(f"✗ Error during automation checks: {str(e)}")


def stop_scheduler():
    """Stop the background scheduler"""
    global scheduler
    
    if scheduler is not None and scheduler.running:
        scheduler.shutdown()
        logger.info("✓ APScheduler stopped")
        scheduler = None


def get_scheduled_jobs():
    """Return list of scheduled jobs for monitoring"""
    global scheduler
    
    if scheduler is None or not scheduler.running:
        return []
    
    jobs_info = []
    for job in scheduler.get_jobs():
        jobs_info.append({
            'id': job.id,
            'name': job.name,
            'next_run_time': str(job.next_run_time),
            'trigger': str(job.trigger),
        })
    return jobs_info
