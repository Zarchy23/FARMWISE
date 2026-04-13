# core/management/commands/check_crop_dates.py
"""
Management command to check crop dates and update statuses, send reminders
Usage: python manage.py check_crop_dates
"""

from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from core.services.crop_automation_service import CropAutomationService
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Check all crop dates and update statuses, send reminders'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--user',
            type=int,
            help='Run checks for specific user ID'
        )
    
    def handle(self, *args, **options):
        try:
            user_id = options.get('user')
            
            if user_id:
                try:
                    user = User.objects.get(id=user_id)
                    self.stdout.write(f'Running checks for user: {user.username}')
                    result = CropAutomationService.run_automation_checks(user=user)
                except User.DoesNotExist:
                    self.stdout.write(self.style.ERROR(f'User with ID {user_id} not found'))
                    return
            else:
                self.stdout.write('Running checks for all farmers...')
                result = CropAutomationService.run_automation_checks()
            
            self.stdout.write(self.style.SUCCESS(
                f'✓ Automation complete!\n'
                f'  - Updated crops: {result["updated_crops"]}\n'
                f'  - Reminders sent: {result["reminders_sent"]}'
            ))
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error: {str(e)}'))
            logger.error(f'Error in check_crop_dates command: {str(e)}')
