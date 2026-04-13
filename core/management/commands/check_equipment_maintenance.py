"""
Django management command to run equipment maintenance automation checks
Usage: python manage.py check_equipment_maintenance [--user=<user_id>]
"""
from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.models import User
from core.services.equipment_automation_service import EquipmentAutomationService


class Command(BaseCommand):
    help = "Check equipment maintenance schedules and send reminders"
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--user',
            type=int,
            help='Specific user ID to check (if not provided, checks all users)'
        )
    
    def handle(self, *args, **kwargs):
        user_id = kwargs.get('user')
        
        if user_id:
            try:
                user = User.objects.get(id=user_id)
                self.stdout.write(f"Running checks for user: {user.email}")
                results = EquipmentAutomationService.run_automation_checks(user=user)
            except User.DoesNotExist:
                raise CommandError(f"User with id {user_id} not found")
        else:
            self.stdout.write("Running checks for all users...")
            results = EquipmentAutomationService.run_automation_checks()
        
        # Display results
        if 'error' in results:
            self.stdout.write(self.style.ERROR(f"Error: {results['error']}"))
        else:
            self.stdout.write(self.style.SUCCESS("\n✓ Equipment Automation Check Complete"))
            self.stdout.write(f"  - Maintenance records updated: {results['maintenance_updated']}")
            self.stdout.write(f"  - Maintenance reminders sent: {results['maintenance_reminders']}")
