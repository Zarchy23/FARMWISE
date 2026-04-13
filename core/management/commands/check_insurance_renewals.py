"""
Django management command to run insurance renewal automation checks
Usage: python manage.py check_insurance_renewals [--user=<user_id>]
"""
from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.models import User
from core.services.insurance_automation_service import InsuranceAutomationService


class Command(BaseCommand):
    help = "Check insurance policies and send renewal reminders"
    
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
                results = InsuranceAutomationService.run_automation_checks(user=user)
            except User.DoesNotExist:
                raise CommandError(f"User with id {user_id} not found")
        else:
            self.stdout.write("Running checks for all users...")
            results = InsuranceAutomationService.run_automation_checks()
        
        # Display results
        if 'error' in results:
            self.stdout.write(self.style.ERROR(f"Error: {results['error']}"))
        else:
            self.stdout.write(self.style.SUCCESS("\n✓ Insurance Automation Check Complete"))
            self.stdout.write(f"  - Insurance policies updated: {results['policies_updated']}")
            self.stdout.write(f"  - Renewal reminders sent: {results['renewal_reminders']}")
