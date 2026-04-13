"""
Payroll Automation Service - Handles payroll payment reminders and status updates.
"""
import logging
from datetime import timedelta
from django.utils import timezone
from core.models import Payroll, Notification

logger = logging.getLogger(__name__)


class PayrollAutomationService:
    """Service for automating payroll reminders and status updates"""
    
    @staticmethod
    def check_and_update_payment_status(user=None, farm=None):
        """Check and update payroll payment status based on period end dates"""
        try:
            if user:
                payrolls = Payroll.objects.filter(worker__farm__owner=user)
            elif farm:
                payrolls = Payroll.objects.filter(worker__farm=farm)
            else:
                payrolls = Payroll.objects.all()
            
            today = timezone.now().date()
            updated_count = 0
            
            for payroll in payrolls:
                if payroll.period_end and not payroll.payment_date:
                    # Mark as pending payment if period ended
                    if payroll.period_end <= today and payroll.status != 'paid':
                        if payroll.status != 'pending':
                            payroll.status = 'pending'
                            payroll.save()
                            updated_count += 1
            
            logger.info(f"Updated {updated_count} payroll records")
            return updated_count
        except Exception as e:
            logger.error(f"Error updating payroll statuses: {str(e)}")
            return 0
    
    @staticmethod
    def check_and_send_payment_reminders(user=None, farm=None):
        """Send reminders for upcoming or overdue payroll payments"""
        try:
            if user:
                payrolls = Payroll.objects.filter(worker__farm__owner=user)
            elif farm:
                payrolls = Payroll.objects.filter(worker__farm=farm)
            else:
                payrolls = Payroll.objects.all()
            
            today = timezone.now().date()
            week_from_now = today + timedelta(days=7)
            reminder_count = 0
            
            for payroll in payrolls:
                if not payroll.period_end or payroll.payment_date:
                    continue
                
                days_since_due = (today - payroll.period_end).days
                
                # Send reminder if due or within 7 days after period end
                if 0 <= days_since_due <= 7 and payroll.status != 'paid':
                    owner = payroll.worker.farm.owner
                    
                    if days_since_due == 0:
                        title = f"Payroll Due TODAY - {payroll.worker.name}"
                        message = f"Worker {payroll.worker.name} payroll is due today!\n\nPeriod: {payroll.period_start} to {payroll.period_end}\nAmount Due: ${payroll.total_pay:.2f}"
                    elif days_since_due <= 3:
                        title = f"URGENT: Overdue Payroll - {payroll.worker.name} ({days_since_due} days)"
                        message = f"Payroll for {payroll.worker.name} is {days_since_due} days overdue!\n\nPeriod: {payroll.period_start} to {payroll.period_end}\nAmount Due: ${payroll.total_pay:.2f}\n\nPay immediately to avoid disputes."
                    else:
                        title = f"Payroll Reminder: {payroll.worker.name} ({days_since_due} days overdue)"
                        message = f"Worker {payroll.worker.name} payment is {days_since_due} days overdue.\n\nPeriod: {payroll.period_start} to {payroll.period_end}\nAmount: ${payroll.total_pay:.2f}\n\nProcess payment soon."
                    
                    PayrollAutomationService._create_notification(
                        user=owner,
                        title=title,
                        message=message,
                        link=f"/labor/payroll/{payroll.id}/"
                    )
                    PayrollAutomationService._send_email_reminder(
                        user=owner,
                        subject=title,
                        message=message
                    )
                    reminder_count += 1
            
            logger.info(f"Sent {reminder_count} payroll reminders")
            return reminder_count
        except Exception as e:
            logger.error(f"Error sending payroll reminders: {str(e)}")
            return 0
    
    @staticmethod
    def _create_notification(user, title, message, link=None):
        """Create an in-app notification"""
        try:
            Notification.objects.create(
                user=user,
                title=title,
                message=message,
                notification_type='payroll',
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
        """Main entry point for payroll automation"""
        try:
            results = {
                'payroll_updated': PayrollAutomationService.check_and_update_payment_status(user=user),
                'payment_reminders': PayrollAutomationService.check_and_send_payment_reminders(user=user),
            }
            logger.info(f"Payroll automation checks completed: {results}")
            return results
        except Exception as e:
            logger.error(f"Error in payroll automation: {str(e)}")
            return {'error': str(e)}
