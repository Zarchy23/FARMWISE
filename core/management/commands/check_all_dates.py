"""
Django management command to run ALL automation checks
Usage: python manage.py check_all_dates [--user=<user_id>]
"""
from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.models import User
from core.services.crop_automation_service import CropAutomationService
from core.services.livestock_automation_service import LivestockAutomationService
from core.services.insurance_automation_service import InsuranceAutomationService
from core.services.payroll_automation_service import PayrollAutomationService


class Command(BaseCommand):
    help = "Run ALL FarmWise automation checks at once"
    
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
                self.stdout.write(self.style.SUCCESS(f"\n▸ Running automation check for user: {user.email}\n"))
            except User.DoesNotExist:
                raise CommandError(f"User with id {user_id} not found")
            
            # Run all automation checks
            self.stdout.write("  ⟳ Checking Crops...")
            crop_results = CropAutomationService.run_automation_checks(user=user)
            
            self.stdout.write("  ⟳ Checking Livestock...")
            livestock_results = LivestockAutomationService.run_automation_checks(user=user)
            
            self.stdout.write("  ⟳ Checking Insurance...")
            insurance_results = InsuranceAutomationService.run_automation_checks(user=user)
            
            self.stdout.write("  ⟳ Checking Payroll...")
            payroll_results = PayrollAutomationService.run_automation_checks(user=user)
        else:
            self.stdout.write(self.style.SUCCESS("\n▸ Running automation checks for ALL users...\n"))
            
            # Run all automation checks
            self.stdout.write("  ⟳ Checking Crops...")
            crop_results = CropAutomationService.run_automation_checks()
            
            self.stdout.write("  ⟳ Checking Livestock...")
            livestock_results = LivestockAutomationService.run_automation_checks()
            
            self.stdout.write("  ⟳ Checking Insurance...")
            insurance_results = InsuranceAutomationService.run_automation_checks()
            
            self.stdout.write("  ⟳ Checking Payroll...")
            payroll_results = PayrollAutomationService.run_automation_checks()
        
        # Display summary
        self.stdout.write("\n" + "=" * 60)
        self.stdout.write(self.style.SUCCESS("AUTOMATION CHECK SUMMARY"))
        self.stdout.write("=" * 60)
        
        if 'error' not in crop_results:
            self.stdout.write(self.style.WARNING(f"\n📌 CROPS"))
            self.stdout.write(f"   Updated: {crop_results.get('updated', 0)}")
            self.stdout.write(f"   Reminders: {crop_results.get('reminders', 0)}")
        
        if 'error' not in livestock_results:
            self.stdout.write(self.style.WARNING(f"\n🐄 LIVESTOCK"))
            self.stdout.write(f"   Health Updated: {livestock_results.get('health_updated', 0)}")
            self.stdout.write(f"   Health Reminders: {livestock_results.get('health_reminders', 0)}")
            self.stdout.write(f"   Breeding Updated: {livestock_results.get('breeding_updated', 0)}")
            self.stdout.write(f"   Breeding Reminders: {livestock_results.get('breeding_reminders', 0)}")
        
        if 'error' not in insurance_results:
            self.stdout.write(self.style.WARNING(f"\n📋 INSURANCE"))
            self.stdout.write(f"   Policies Updated: {insurance_results.get('policies_updated', 0)}")
            self.stdout.write(f"   Renewal Reminders: {insurance_results.get('renewal_reminders', 0)}")
        
        if 'error' not in payroll_results:
            self.stdout.write(self.style.WARNING(f"\n💰 PAYROLL"))
            self.stdout.write(f"   Payroll Updated: {payroll_results.get('payroll_updated', 0)}")
            self.stdout.write(f"   Payment Reminders: {payroll_results.get('payment_reminders', 0)}")
        
        self.stdout.write(self.style.SUCCESS("\n✓ All automation checks completed!\n"))
        self.stdout.write("=" * 60)
