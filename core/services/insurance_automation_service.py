"""
Insurance Automation Service - Handles insurance renewal reminders and expiration alerts.
"""
import logging
from datetime import timedelta
from django.utils import timezone
from core.models import InsurancePolicy, Notification

logger = logging.getLogger(__name__)


class InsuranceAutomationService:
    """Service for automating insurance renewal reminders"""
    
    @staticmethod
    def check_and_update_policy_status(user=None, farm=None):
        """Check and update insurance policy status based on expiry dates"""
        try:
            if user:
                policies = InsurancePolicy.objects.filter(farm__owner=user)
            elif farm:
                policies = InsurancePolicy.objects.filter(farm=farm)
            else:
                policies = InsurancePolicy.objects.all()
            
            today = timezone.now().date()
            updated_count = 0
            
            for policy in policies:
                if policy.end_date:
                    # Mark as expiring soon
                    if policy.end_date <= today and policy.status != 'expired':
                        policy.status = 'expired'
                        policy.save()
                        updated_count += 1
                    
                    # Mark as expiring
                    elif policy.end_date - timedelta(days=30) <= today < policy.end_date and policy.status == 'active':
                        policy.status = 'expiring_soon'
                        policy.save()
                        updated_count += 1
            
            logger.info(f"Updated {updated_count} insurance policies")
            return updated_count
        except Exception as e:
            logger.error(f"Error updating policy statuses: {str(e)}")
            return 0
    
    @staticmethod
    def check_and_send_renewal_reminders(user=None, farm=None):
        """Send reminders for upcoming policy renewals"""
        try:
            if user:
                policies = InsurancePolicy.objects.filter(farm__owner=user)
            elif farm:
                policies = InsurancePolicy.objects.filter(farm=farm)
            else:
                policies = InsurancePolicy.objects.all()
            
            today = timezone.now().date()
            reminder_count = 0
            
            # Check for policies expiring in 30, 14, 7, and 1 day(s)
            reminder_days = [30, 14, 7, 1]
            
            for policy in policies:
                if not policy.end_date or policy.status == 'expired':
                    continue
                
                days_until = (policy.end_date - today).days
                
                if days_until in reminder_days and policy.status != 'expired':
                    owner = policy.farm.owner
                    
                    if days_until == 1:
                        title = f"URGENT: Insurance Policy Expires TOMORROW - {policy.policy_number}"
                        message = f"Your {policy.coverage_type} insurance policy ({policy.policy_number}) with {policy.provider} expires tomorrow: {policy.end_date}\n\nRenew immediately to avoid coverage gap!"
                    else:
                        title = f"Insurance Renewal Reminder: {policy.policy_number} ({days_until} days)"
                        message = f"Your {policy.coverage_type} insurance policy expires in {days_until} days:\n\nPolicy: {policy.policy_number}\nProvider: {policy.provider}\nExpiry: {policy.end_date}\nCoverage: {policy.coverage_type}\n\nPlease renew before the deadline."
                    
                    InsuranceAutomationService._create_notification(
                        user=owner,
                        title=title,
                        message=message,
                        link=f"/insurance/{policy.id}/"
                    )
                    InsuranceAutomationService._send_email_reminder(
                        user=owner,
                        subject=title,
                        message=message
                    )
                    reminder_count += 1
                
                # Also check for expired policies
                elif days_until < 0 and policy.status == 'expired':
                    owner = policy.farm.owner
                    days_expired = abs(days_until)
                    
                    title = f"EXPIRED: Insurance Policy - {policy.policy_number} ({days_expired} days)"
                    message = f"Your {policy.coverage_type} insurance policy ({policy.policy_number}) expired {days_expired} days ago!\n\nYour farm is currently uninsured. Renew immediately!"
                    
                    InsuranceAutomationService._create_notification(
                        user=owner,
                        title=title,
                        message=message,
                        link=f"/insurance/{policy.id}/"
                    )
                    reminder_count += 1
            
            logger.info(f"Sent {reminder_count} renewal reminders")
            return reminder_count
        except Exception as e:
            logger.error(f"Error sending renewal reminders: {str(e)}")
            return 0
    
    @staticmethod
    def _create_notification(user, title, message, link=None):
        """Create an in-app notification"""
        try:
            Notification.objects.create(
                user=user,
                title=title,
                message=message,
                notification_type='insurance',
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
        """Main entry point for insurance automation"""
        try:
            results = {
                'policies_updated': InsuranceAutomationService.check_and_update_policy_status(user=user),
                'renewal_reminders': InsuranceAutomationService.check_and_send_renewal_reminders(user=user),
            }
            logger.info(f"Insurance automation checks completed: {results}")
            return results
        except Exception as e:
            logger.error(f"Error in insurance automation: {str(e)}")
            return {'error': str(e)}
