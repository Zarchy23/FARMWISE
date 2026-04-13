"""
Equipment Automation Service - Handles automatic maintenance reminders and status updates.
"""
import logging
from datetime import timedelta
from django.utils import timezone
from core.models import Maintenance, Notification

logger = logging.getLogger(__name__)


class EquipmentAutomationService:
    """Service for automating equipment maintenance reminders"""
    
    @staticmethod
    def check_and_update_maintenance_status(user=None, farm=None):
        """Check and update maintenance status based on scheduled dates"""
        try:
            if user:
                maintenances = Maintenance.objects.filter(equipment__owner=user)
            elif farm:
                maintenances = Maintenance.objects.filter(equipment__owner=farm.owner)
            else:
                maintenances = Maintenance.objects.all()
            
            today = timezone.now().date()
            updated_count = 0
            
            for maintenance in maintenances:
                if maintenance.scheduled_date and not maintenance.actual_date:
                    # Mark as overdue if past scheduled date
                    if maintenance.scheduled_date <= today and maintenance.status != 'completed':
                        if maintenance.status != 'overdue':
                            maintenance.status = 'overdue'
                            maintenance.save()
                            updated_count += 1
            
            logger.info(f"Updated {updated_count} maintenance records")
            return updated_count
        except Exception as e:
            logger.error(f"Error updating maintenance statuses: {str(e)}")
            return 0
    
    @staticmethod
    def check_and_send_maintenance_reminders(user=None, farm=None):
        """Send reminders for upcoming or overdue maintenance"""
        try:
            if user:
                maintenances = Maintenance.objects.filter(equipment__owner=user)
            elif farm:
                maintenances = Maintenance.objects.filter(equipment__owner=farm.owner)
            else:
                maintenances = Maintenance.objects.all()
            
            today = timezone.now().date()
            week_from_now = today + timedelta(days=7)
            reminder_count = 0
            
            for maintenance in maintenances:
                if not maintenance.scheduled_date or maintenance.actual_date:
                    continue
                
                # Reminder if due within 7 days or overdue
                days_until = (maintenance.scheduled_date - today).days
                
                if days_until <= 7 and days_until >= -1 and maintenance.status != 'completed':
                    owner = maintenance.equipment.owner
                    
                    if days_until <= 0:
                        title = f"OVERDUE: {maintenance.equipment.name} Maintenance ({abs(days_until)} days overdue)"
                    elif days_until == 1:
                        title = f"Maintenance Due Tomorrow: {maintenance.equipment.name}"
                    else:
                        title = f"{maintenance.equipment.name} Maintenance Due in {days_until} days"
                    
                    message = f"Equipment: {maintenance.equipment.name}\nType: {maintenance.maintenance_type}\nScheduled: {maintenance.scheduled_date}\nDescription: {maintenance.description or 'N/A'}"
                    
                    EquipmentAutomationService._create_notification(
                        user=owner,
                        title=title,
                        message=message,
                        link=f"/equipment/maintenance/{maintenance.id}/"
                    )
                    EquipmentAutomationService._send_email_reminder(
                        user=owner,
                        subject=title,
                        message=message
                    )
                    reminder_count += 1
            
            logger.info(f"Sent {reminder_count} maintenance reminders")
            return reminder_count
        except Exception as e:
            logger.error(f"Error sending maintenance reminders: {str(e)}")
            return 0
    
    @staticmethod
    def _create_notification(user, title, message, link=None):
        """Create an in-app notification"""
        try:
            Notification.objects.create(
                user=user,
                title=title,
                message=message,
                notification_type='equipment',
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
        """Main entry point for equipment automation"""
        try:
            results = {
                'maintenance_updated': EquipmentAutomationService.check_and_update_maintenance_status(user=user),
                'maintenance_reminders': EquipmentAutomationService.check_and_send_maintenance_reminders(user=user),
            }
            logger.info(f"Equipment automation checks completed: {results}")
            return results
        except Exception as e:
            logger.error(f"Error in equipment automation: {str(e)}")
            return {'error': str(e)}
