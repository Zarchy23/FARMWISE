"""
Django management command to run livestock automation checks (health, breeding, vaccinations)
Usage: python manage.py check_livestock_dates [--user=<user_id>]
"""
from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.models import User
from core.services.livestock_automation_service import LivestockAutomationService


class Command(BaseCommand):
    help = "Check livestock health records, breeding dates, and send reminders"
    
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
                results = LivestockAutomationService.run_automation_checks(user=user)
            except User.DoesNotExist:
                raise CommandError(f"User with id {user_id} not found")
        else:
            self.stdout.write("Running checks for all users...")
            results = LivestockAutomationService.run_automation_checks()
        
        # Display results
        if 'error' in results:
            self.stdout.write(self.style.ERROR(f"Error: {results['error']}"))
        else:
            self.stdout.write(self.style.SUCCESS("\n✓ Livestock Automation Check Complete"))
            self.stdout.write(f"  - Health records updated: {results['health_updated']}")
            self.stdout.write(f"  - Health reminders sent: {results['health_reminders']}")
            self.stdout.write(f"  - Breeding records updated: {results['breeding_updated']}")
            self.stdout.write(f"  - Breeding reminders sent: {results['breeding_reminders']}")
