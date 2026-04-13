# core/management/commands/test_health_reminder_emails.py
# Test Command for Health Reminder Email System

from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from django.contrib.auth import get_user_model
from datetime import timedelta
import sys

from core.models import Animal, Farm, HealthRecord
from core.services.email_service import EmailService
from core.services.admin_alert_service import AdminAlertService
from core.tasks import send_health_reminder_emails, send_overdue_health_emails

User = get_user_model()


class Command(BaseCommand):
    help = 'Test health reminder email system'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--test-type',
            choices=['full', 'reminders', 'overdue', 'admin-alerts', 'email-service'],
            default='full',
            help='Type of test to run'
        )
        parser.add_argument(
            '--farm-id',
            type=int,
            help='Test with specific farm ID'
        )
        parser.add_argument(
            '--animal-id',
            type=int,
            help='Test with specific animal ID'
        )
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Show detailed output'
        )
    
    def handle(self, *args, **options):
        test_type = options['test_type']
        verbose = options['verbose']
        
        self.stdout.write(self.style.SUCCESS('FarmWise Health Email System Test'))
        self.stdout.write('-' * 50)
        
        try:
            if test_type in ['full', 'email-service']:
                self.test_email_service(options, verbose)
            
            if test_type in ['full', 'reminders']:
                self.test_reminder_emails(options, verbose)
            
            if test_type in ['full', 'overdue']:
                self.test_overdue_emails(options, verbose)
            
            if test_type in ['full', 'admin-alerts']:
                self.test_admin_alerts(options, verbose)
            
            self.stdout.write(self.style.SUCCESS('All tests completed successfully!'))
        
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Test failed: {str(e)}'))
            sys.exit(1)
    
    def test_email_service(self, options, verbose):
        """Test email service methods"""
        self.stdout.write('\n' + self.style.HTTP_SUCCESS('Testing Email Service...'))
        
        try:
            # Get test user/farm/animal
            farm_id = options.get('farm_id')
            animal_id = options.get('animal_id')
            
            if farm_id:
                farm = Farm.objects.get(id=farm_id)
            else:
                farm = Farm.objects.first()
                if not farm:
                    self.stdout.write(self.style.WARNING('No farms found. Create a farm to test.'))
                    return
            
            if animal_id:
                animal = Animal.objects.get(id=animal_id, farm=farm)
            else:
                animal = Animal.objects.filter(farm=farm, status='alive').first()
                if not animal:
                    self.stdout.write(self.style.WARNING(f'No live animals on {farm.name}. Create an animal to test.'))
                    return
            
            user = farm.owner
            
            # Create test health record
            today = timezone.now().date()
            health_record = HealthRecord.objects.create(
                animal=animal,
                record_type='vaccination',
                medication_name='Test Vaccination',
                dosage='Test',
                record_date=today,
                next_due_date=today + timedelta(days=3)
            )
            
            self.stdout.write(f'  ✓ Created test health record: {health_record.id}')
            
            # Test each email type
            email_tests = [
                ('Vaccination', EmailService.send_vaccination_reminder_email),
                ('Feed Supplementation', EmailService.send_feed_supplementation_reminder_email),
                ('Health Checkup', EmailService.send_health_checkup_reminder_email),
                ('Parasite Control', EmailService.send_parasite_control_reminder_email),
                ('Medication', EmailService.send_medication_reminder_email),
            ]
            
            for email_name, email_func in email_tests:
                try:
                    result = email_func(user, animal, health_record)
                    status = '✓' if result else '✗'
                    self.stdout.write(f'  {status} {email_name} email test: {"PASSED" if result else "FAILED"}')
                    if verbose and not result:
                        self.stdout.write(f'    Details: Email send returned False')
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f'  ✗ {email_name} email test: FAILED - {str(e)}'))
            
            # Cleanup
            health_record.delete()
            self.stdout.write('  ✓ Cleaned up test data')
        
        except Exception as e:
            raise CommandError(f'Email service test failed: {str(e)}')
    
    def test_reminder_emails(self, options, verbose):
        """Test reminder email task"""
        self.stdout.write('\n' + self.style.HTTP_SUCCESS('Testing Reminder Email Task...'))
        
        try:
            # Run the task
            result = send_health_reminder_emails()
            self.stdout.write(f'  ✓ Task executed: {result}')
        
        except Exception as e:
            raise CommandError(f'Reminder email task failed: {str(e)}')
    
    def test_overdue_emails(self, options, verbose):
        """Test overdue email task"""
        self.stdout.write('\n' + self.style.HTTP_SUCCESS('Testing Overdue Email Task...'))
        
        try:
            # Run the task
            result = send_overdue_health_emails()
            self.stdout.write(f'  ✓ Task executed: {result}')
        
        except Exception as e:
            raise CommandError(f'Overdue email task failed: {str(e)}')
    
    def test_admin_alerts(self, options, verbose):
        """Test admin alert service"""
        self.stdout.write('\n' + self.style.HTTP_SUCCESS('Testing Admin Alert Service...'))
        
        try:
            # Get test data
            farm_id = options.get('farm_id')
            animal_id = options.get('animal_id')
            
            if farm_id:
                farm = Farm.objects.get(id=farm_id)
            else:
                farm = Farm.objects.first()
                if not farm:
                    self.stdout.write(self.style.WARNING('No farms found. Create a farm to test.'))
                    return
            
            if animal_id:
                animal = Animal.objects.get(id=animal_id, farm=farm)
            else:
                animal = Animal.objects.filter(farm=farm, status='alive').first()
                if not animal:
                    self.stdout.write(self.style.WARNING(f'No live animals on {farm.name}. Create an animal to test.'))
                    return
            
            # Test alert types
            alert_tests = [
                ('Critical Health Alert', lambda: AdminAlertService.send_critical_health_alert(animal, 20)),
                ('Multiple Overdue Alert', lambda: AdminAlertService.send_multiple_overdue_alert(farm, 5)),
            ]
            
            for alert_name, alert_func in alert_tests:
                try:
                    alert_func()
                    self.stdout.write(f'  ✓ {alert_name}: PASSED')
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f'  ✗ {alert_name}: FAILED - {str(e)}'))
        
        except Exception as e:
            raise CommandError(f'Admin alert test failed: {str(e)}')
