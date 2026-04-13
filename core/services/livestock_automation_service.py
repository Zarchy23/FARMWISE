"""
Livestock Automation Service - Handles automatic status updates and reminders for livestock health, breeding, and vaccinations.
"""
import logging
from datetime import timedelta
from django.utils import timezone
from core.models import HealthRecord, BreedingRecord, Notification

logger = logging.getLogger(__name__)


class LivestockAutomationService:
    """Service for automating livestock health and breeding task reminders"""
    
    @staticmethod
    def check_and_update_health_status(user=None, farm=None):
        """Check and update health record statuses based on next_due_date"""
        try:
            if user:
                health_records = HealthRecord.objects.filter(animal__farm__owner=user)
            elif farm:
                health_records = HealthRecord.objects.filter(animal__farm=farm)
            else:
                health_records = HealthRecord.objects.all()
            
            today = timezone.now().date()
            updated_count = 0
            
            for record in health_records:
                if record.next_due_date:
                    # Mark as overdue if past due date
                    if record.next_due_date <= today and record.status != 'completed':
                        if record.status != 'overdue':
                            record.status = 'overdue'
                            record.save()
                            updated_count += 1
                    
                    # Mark as pending if still upcoming
                    elif record.next_due_date > today and record.status == 'overdue':
                        record.status = 'pending'
                        record.save()
                        updated_count += 1
            
            logger.info(f"Updated {updated_count} health records")
            return updated_count
        except Exception as e:
            logger.error(f"Error updating health statuses: {str(e)}")
            return 0
    
    @staticmethod
    def check_and_update_breeding_status(user=None, farm=None):
        """Check breeding records and mark overdue calvings"""
        try:
            if user:
                breeding_records = BreedingRecord.objects.filter(animal__farm__owner=user)
            elif farm:
                breeding_records = BreedingRecord.objects.filter(animal__farm=farm)
            else:
                breeding_records = BreedingRecord.objects.all()
            
            today = timezone.now().date()
            updated_count = 0
            
            for record in breeding_records:
                if record.expected_calving_date and not record.actual_calving_date:
                    if record.expected_calving_date <= today and record.status != 'completed':
                        if record.status != 'overdue':
                            record.status = 'overdue'
                            record.save()
                            updated_count += 1
            
            logger.info(f"Updated {updated_count} breeding records")
            return updated_count
        except Exception as e:
            logger.error(f"Error updating breeding statuses: {str(e)}")
            return 0
    
    @staticmethod
    def check_and_send_health_reminders(user=None, farm=None):
        """Send reminders for upcoming health checks or overdue checks"""
        try:
            if user:
                health_records = HealthRecord.objects.filter(animal__farm__owner=user)
            elif farm:
                health_records = HealthRecord.objects.filter(animal__farm=farm)
            else:
                health_records = HealthRecord.objects.all()
            
            today = timezone.now().date()
            tomorrow = today + timedelta(days=1)
            reminder_count = 0
            
            for record in health_records:
                if not record.next_due_date:
                    continue
                
                # Check if due tomorrow (advance reminder)
                if record.next_due_date == tomorrow and record.status != 'completed':
                    LivestockAutomationService._create_notification(
                        user=record.animal.farm.owner,
                        title="Health Check Due Tomorrow",
                        message=f"Health check for {record.animal.tag_number} ({record.animal.animal_type.breed}) is due tomorrow - {record.check_type}",
                        link=f"/livestock/health/{record.id}/"
                    )
                    LivestockAutomationService._send_email_reminder(
                        user=record.animal.farm.owner,
                        subject="Health Check Reminder",
                        message=f"Health check for {record.animal.tag_number} is due tomorrow. Type: {record.check_type}"
                    )
                    reminder_count += 1
                
                # Check if overdue (critical reminder)
                elif record.next_due_date < today and record.status == 'overdue':
                    days_overdue = (today - record.next_due_date).days
                    LivestockAutomationService._create_notification(
                        user=record.animal.farm.owner,
                        title=f"OVERDUE: Health Check ({days_overdue} days late)",
                        message=f"{record.animal.tag_number} health check is {days_overdue} days overdue! Type: {record.check_type}",
                        link=f"/livestock/health/{record.id}/"
                    )
                    reminder_count += 1
            
            logger.info(f"Sent {reminder_count} health reminders")
            return reminder_count
        except Exception as e:
            logger.error(f"Error sending health reminders: {str(e)}")
            return 0
    
    @staticmethod
    def check_and_send_breeding_reminders(user=None, farm=None):
        """Send reminders for upcoming calvings"""
        try:
            if user:
                breeding_records = BreedingRecord.objects.filter(animal__farm__owner=user)
            elif farm:
                breeding_records = BreedingRecord.objects.filter(animal__farm=farm)
            else:
                breeding_records = BreedingRecord.objects.all()
            
            today = timezone.now().date()
            week_from_now = today + timedelta(days=7)
            reminder_count = 0
            
            for record in breeding_records:
                if not record.expected_calving_date or record.actual_calving_date:
                    continue
                
                # Send reminder 7 days before expected calving
                if record.expected_calving_date <= week_from_now and record.status != 'completed':
                    days_until = (record.expected_calving_date - today).days
                    
                    if days_until <= 7 and days_until >= -1:  # Within 7 days before or 1 day after
                        LivestockAutomationService._create_notification(
                            user=record.animal.farm.owner,
                            title=f"Calving Expected in {days_until} days" if days_until > 0 else "CALVING OVERDUE",
                            message=f"{record.animal.tag_number} expected calving on {record.expected_calving_date}. Expected date of birth: {record.expected_calving_date}",
                            link=f"/livestock/breeding/{record.id}/"
                        )
                        LivestockAutomationService._send_email_reminder(
                            user=record.animal.farm.owner,
                            subject=f"Calving Reminder - {record.animal.tag_number}",
                            message=f"Animal {record.animal.tag_number} is expected to calve on {record.expected_calving_date}. Prepare for delivery!"
                        )
                        reminder_count += 1
            
            logger.info(f"Sent {reminder_count} breeding reminders")
            return reminder_count
        except Exception as e:
            logger.error(f"Error sending breeding reminders: {str(e)}")
            return 0
    
    @staticmethod
    def _create_notification(user, title, message, link=None):
        """Create an in-app notification"""
        try:
            Notification.objects.create(
                user=user,
                title=title,
                message=message,
                notification_type='livestock',
                link=link or '/'
            )
        except Exception as e:
            logger.error(f"Error creating notification: {str(e)}")
    
    @staticmethod
    def _send_email_reminder(user, subject, message):
        """Send email reminder to user"""
        try:
            from django.core.mail import send_mail
            send_mail(
                subject=subject,
                message=message,
                from_email='noreply@farmwise.com',
                recipient_list=[user.email],
                fail_silently=True,
            )
        except Exception as e:
            logger.error(f"Error sending email: {str(e)}")
    
    @staticmethod
    def run_automation_checks(user=None):
        """Main entry point for all livestock automation checks"""
        try:
            results = {
                'health_updated': LivestockAutomationService.check_and_update_health_status(user=user),
                'breeding_updated': LivestockAutomationService.check_and_update_breeding_status(user=user),
                'health_reminders': LivestockAutomationService.check_and_send_health_reminders(user=user),
                'breeding_reminders': LivestockAutomationService.check_and_send_breeding_reminders(user=user),
            }
            logger.info(f"Livestock automation checks completed: {results}")
            return results
        except Exception as e:
            logger.error(f"Error in livestock automation: {str(e)}")
            return {'error': str(e)}
