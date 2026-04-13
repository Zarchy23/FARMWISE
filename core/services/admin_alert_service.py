# core/services/admin_alert_service.py
# Admin Alert Service for FarmWise

from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
from django.utils.html import strip_tags
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.db.models import Q
from datetime import timedelta
import logging

logger = logging.getLogger(__name__)

User = get_user_model()


class AdminAlertService:
    """Service for sending alerts to admins"""
    
    @staticmethod
    def send_critical_health_alert(animal, days_overdue):
        """Send alert to farm owner when animal has critical overdue health record"""
        subject = f'🚨 CRITICAL: {animal.name} has critical overdue health record'
        
        farm = animal.farm
        admins = User.objects.filter(
            Q(assigned_farms=farm, is_staff=True) | 
            Q(is_superuser=True)
        ).distinct()
        
        for admin in admins:
            try:
                html_content = render_to_string('emails/admin_critical_health_alert.html', {
                    'user': admin,
                    'animal': animal,
                    'farm': farm,
                    'days_overdue': days_overdue,
                    'action_link': f'{settings.APP_URL}/livestock/{animal.id}/health/',
                    'support_email': settings.DEFAULT_FROM_EMAIL,
                })
                
                text_content = strip_tags(html_content)
                
                AdminAlertService._send_email(
                    subject=subject,
                    message=text_content,
                    html_message=html_content,
                    recipient_list=[admin.email]
                )
                logger.info(f"Sent critical health alert to admin {admin.email}")
            except Exception as e:
                logger.error(f"Error sending critical health alert to {admin.email}: {str(e)}")
    
    @staticmethod
    def send_multiple_overdue_alert(farm, overdue_count):
        """Alert when multiple animals have overdue health records"""
        subject = f'⚠️ ALERT: {overdue_count} animals have overdue health records on {farm.name}'
        
        admins = User.objects.filter(
            Q(assigned_farms=farm, is_staff=True) | 
            Q(is_superuser=True)
        ).distinct()
        
        for admin in admins:
            try:
                html_content = render_to_string('emails/admin_multiple_overdue_alert.html', {
                    'user': admin,
                    'farm': farm,
                    'overdue_count': overdue_count,
                    'action_link': f'{settings.APP_URL}/livestock/?filter=overdue_health',
                    'support_email': settings.DEFAULT_FROM_EMAIL,
                })
                
                text_content = strip_tags(html_content)
                
                AdminAlertService._send_email(
                    subject=subject,
                    message=text_content,
                    html_message=html_content,
                    recipient_list=[admin.email]
                )
                logger.info(f"Sent multiple overdue alert to admin {admin.email}")
            except Exception as e:
                logger.error(f"Error sending multiple overdue alert to {admin.email}: {str(e)}")
    
    @staticmethod
    def send_email_failure_alert(farm, failed_count, error_summary):
        """Alert when email sending fails multiple times"""
        subject = f'⚠️ System Alert: {failed_count} health reminder emails failed to send'
        
        superusers = User.objects.filter(is_superuser=True)
        
        for admin in superusers:
            try:
                html_content = render_to_string('emails/admin_email_failure_alert.html', {
                    'user': admin,
                    'farm': farm,
                    'failed_count': failed_count,
                    'error_summary': error_summary,
                    'action_link': f'{settings.APP_URL}/admin/logs/',
                    'support_email': settings.DEFAULT_FROM_EMAIL,
                })
                
                text_content = strip_tags(html_content)
                
                AdminAlertService._send_email(
                    subject=subject,
                    message=text_content,
                    html_message=html_content,
                    recipient_list=[admin.email]
                )
                logger.info(f"Sent email failure alert to admin {admin.email}")
            except Exception as e:
                logger.error(f"Error sending email failure alert to {admin.email}: {str(e)}")
    
    @staticmethod
    def send_high_priority_animal_alert(animal, priority_reason):
        """Send high-priority alert about an animal"""
        subject = f'⚠️ High Priority: {animal.name} requires immediate attention'
        
        farm = animal.farm
        admins = User.objects.filter(
            Q(assigned_farms=farm, is_staff=True) | 
            Q(is_superuser=True)
        ).distinct()
        
        for admin in admins:
            try:
                html_content = render_to_string('emails/admin_high_priority_alert.html', {
                    'user': admin,
                    'animal': animal,
                    'farm': farm,
                    'priority_reason': priority_reason,
                    'action_link': f'{settings.APP_URL}/livestock/{animal.id}/',
                    'support_email': settings.DEFAULT_FROM_EMAIL,
                })
                
                text_content = strip_tags(html_content)
                
                AdminAlertService._send_email(
                    subject=subject,
                    message=text_content,
                    html_message=html_content,
                    recipient_list=[admin.email]
                )
                logger.info(f"Sent high priority alert to admin {admin.email}")
            except Exception as e:
                logger.error(f"Error sending high priority alert to {admin.email}: {str(e)}")
    
    @staticmethod
    def _send_email(subject, message, html_message, recipient_list):
        """Internal method to send admin alert email"""
        try:
            from django.core.mail import EmailMultiAlternatives
            
            email = EmailMultiAlternatives(
                subject=subject,
                body=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=recipient_list,
                reply_to=[settings.DEFAULT_FROM_EMAIL]
            )
            email.attach_alternative(html_message, "text/html")
            email.send(fail_silently=False)
            logger.info(f"Admin alert email sent to {recipient_list}: {subject}")
            return True
        except Exception as e:
            logger.error(f"Failed to send admin alert email to {recipient_list}: {e}")
            return False
