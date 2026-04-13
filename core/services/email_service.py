# core/services/email_service.py
# Complete email service for FarmWise

from django.core.mail import send_mail, EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings
from django.utils.html import strip_tags
from django.utils import timezone
import logging

logger = logging.getLogger(__name__)


class EmailService:
    """Complete email service for FarmWise"""
    
    @staticmethod
    def send_welcome_email(user):
        """Send welcome email to new user"""
        subject = f'Welcome to FarmWise, {user.get_full_name() or user.username}!'
        
        html_content = render_to_string('emails/welcome.html', {
            'user': user,
            'app_name': 'FarmWise',
            'app_url': settings.APP_URL,
            'support_email': settings.DEFAULT_FROM_EMAIL,
        })
        
        text_content = strip_tags(html_content)
        
        return EmailService._send_email(
            subject=subject,
            message=text_content,
            html_message=html_content,
            recipient_list=[user.email]
        )
    
    @staticmethod
    def send_password_reset_email(user, reset_link):
        """Send password reset email"""
        subject = 'Reset Your FarmWise Password'
        
        html_content = render_to_string('emails/password_reset.html', {
            'user': user,
            'reset_link': reset_link,
            'valid_hours': 24,
            'app_name': 'FarmWise',
            'support_email': settings.DEFAULT_FROM_EMAIL,
        })
        
        text_content = strip_tags(html_content)
        
        return EmailService._send_email(
            subject=subject,
            message=text_content,
            html_message=html_content,
            recipient_list=[user.email]
        )
    
    @staticmethod
    def send_pest_alert_email(user, pest_report):
        """Send pest detection alert"""
        subject = f'🚨 Pest Alert: {pest_report.ai_diagnosis} detected on your farm'
        
        html_content = render_to_string('emails/pest_alert.html', {
            'user': user,
            'report': pest_report,
            'severity_class': 'high' if pest_report.severity == 'high' else 'medium',
            'action_link': f'{settings.APP_URL}/pest-detection/{pest_report.id}/',
            'support_email': settings.DEFAULT_FROM_EMAIL,
        })
        
        text_content = strip_tags(html_content)
        
        return EmailService._send_email(
            subject=subject,
            message=text_content,
            html_message=html_content,
            recipient_list=[user.email]
        )
    
    @staticmethod
    def send_weather_alert_email(user, alert):
        """Send weather alert email"""
        subject = f'🌤️ Weather Alert: {alert.title}'
        
        html_content = render_to_string('emails/weather_alert.html', {
            'user': user,
            'alert': alert,
            'action_link': f'{settings.APP_URL}/weather/',
            'support_email': settings.DEFAULT_FROM_EMAIL,
        })
        
        text_content = strip_tags(html_content)
        
        return EmailService._send_email(
            subject=subject,
            message=text_content,
            html_message=html_content,
            recipient_list=[user.email]
        )
    
    @staticmethod
    def send_geofence_alert_email(user, alert):
        """Send geofence breach alert"""
        subject = f'⚠️ Geofence Alert: {alert.livestock.name} has left the safe zone'
        
        html_content = render_to_string('emails/geofence_alert.html', {
            'user': user,
            'alert': alert,
            'action_link': f'{settings.APP_URL}/mapping/livestock-tracking/',
            'support_email': settings.DEFAULT_FROM_EMAIL,
        })
        
        text_content = strip_tags(html_content)
        
        return EmailService._send_email(
            subject=subject,
            message=text_content,
            html_message=html_content,
            recipient_list=[user.email]
        )
    
    @staticmethod
    def send_harvest_reminder_email(user, crop):
        """Send harvest reminder"""
        subject = f'🌾 Harvest Reminder: {crop.crop_type.name} is ready for harvest!'
        
        html_content = render_to_string('emails/harvest_reminder.html', {
            'user': user,
            'crop': crop,
            'field': crop.field,
            'action_link': f'{settings.APP_URL}/crops/{crop.id}/harvest/',
            'support_email': settings.DEFAULT_FROM_EMAIL,
        })
        
        text_content = strip_tags(html_content)
        
        return EmailService._send_email(
            subject=subject,
            message=text_content,
            html_message=html_content,
            recipient_list=[user.email]
        )
    
    @staticmethod
    def send_vaccination_reminder_email(user, animal, health_record):
        """Send vaccination reminder"""
        subject = f'💉 Vaccination Due: {animal.name} needs vaccination'
        
        days_until = (health_record.next_due_date - timezone.now().date()).days if health_record.next_due_date else 0
        
        html_content = render_to_string('emails/vaccination_reminder.html', {
            'user': user,
            'animal': animal,
            'health_record': health_record,
            'days_until': days_until,
            'action_link': f'{settings.APP_URL}/livestock/{animal.id}/health/',
            'support_email': settings.DEFAULT_FROM_EMAIL,
        })
        
        text_content = strip_tags(html_content)
        
        return EmailService._send_email(
            subject=subject,
            message=text_content,
            html_message=html_content,
            recipient_list=[user.email]
        )
    
    @staticmethod
    def send_feed_supplementation_reminder_email(user, animal, health_record):
        """Send feed supplementation reminder"""
        subject = f'🌾 Feed Supplementation Due: {animal.name} needs supplementation'
        
        days_until = (health_record.next_due_date - timezone.now().date()).days if health_record.next_due_date else 0
        
        html_content = render_to_string('emails/feed_supplementation_reminder.html', {
            'user': user,
            'animal': animal,
            'health_record': health_record,
            'days_until': days_until,
            'action_link': f'{settings.APP_URL}/livestock/{animal.id}/health/',
            'support_email': settings.DEFAULT_FROM_EMAIL,
        })
        
        text_content = strip_tags(html_content)
        
        return EmailService._send_email(
            subject=subject,
            message=text_content,
            html_message=html_content,
            recipient_list=[user.email]
        )
    
    @staticmethod
    def send_health_checkup_reminder_email(user, animal, health_record):
        """Send health checkup reminder"""
        subject = f'🏥 Health Checkup Due: {animal.name} needs a health checkup'
        
        days_until = (health_record.next_due_date - timezone.now().date()).days if health_record.next_due_date else 0
        
        html_content = render_to_string('emails/health_checkup_reminder.html', {
            'user': user,
            'animal': animal,
            'health_record': health_record,
            'days_until': days_until,
            'action_link': f'{settings.APP_URL}/livestock/{animal.id}/health/',
            'support_email': settings.DEFAULT_FROM_EMAIL,
        })
        
        text_content = strip_tags(html_content)
        
        return EmailService._send_email(
            subject=subject,
            message=text_content,
            html_message=html_content,
            recipient_list=[user.email]
        )
    
    @staticmethod
    def send_parasite_control_reminder_email(user, animal, health_record):
        """Send parasite control reminder"""
        subject = f'🛡️ Parasite Control Due: {animal.name} needs parasite treatment'
        
        days_until = (health_record.next_due_date - timezone.now().date()).days if health_record.next_due_date else 0
        
        html_content = render_to_string('emails/parasite_control_reminder.html', {
            'user': user,
            'animal': animal,
            'health_record': health_record,
            'days_until': days_until,
            'action_link': f'{settings.APP_URL}/livestock/{animal.id}/health/',
            'support_email': settings.DEFAULT_FROM_EMAIL,
        })
        
        text_content = strip_tags(html_content)
        
        return EmailService._send_email(
            subject=subject,
            message=text_content,
            html_message=html_content,
            recipient_list=[user.email]
        )
    
    @staticmethod
    def send_medication_reminder_email(user, animal, health_record):
        """Send general medication reminder"""
        subject = f'💊 Medication Due: {animal.name} needs medication'
        
        days_until = (health_record.next_due_date - timezone.now().date()).days if health_record.next_due_date else 0
        
        html_content = render_to_string('emails/medication_reminder.html', {
            'user': user,
            'animal': animal,
            'health_record': health_record,
            'days_until': days_until,
            'action_link': f'{settings.APP_URL}/livestock/{animal.id}/health/',
            'support_email': settings.DEFAULT_FROM_EMAIL,
        })
        
        text_content = strip_tags(html_content)
        
        return EmailService._send_email(
            subject=subject,
            message=text_content,
            html_message=html_content,
            recipient_list=[user.email]
        )
    
    @staticmethod
    def send_daily_summary_email(user, summary_data):
        """Send daily farm summary"""
        subject = f'📊 FarmWise Daily Summary - {summary_data["date"]}'
        
        html_content = render_to_string('emails/daily_summary.html', {
            'user': user,
            'summary': summary_data,
            'action_link': f'{settings.APP_URL}/dashboard/',
            'support_email': settings.DEFAULT_FROM_EMAIL,
        })
        
        text_content = strip_tags(html_content)
        
        return EmailService._send_email(
            subject=subject,
            message=text_content,
            html_message=html_content,
            recipient_list=[user.email]
        )
    
    @staticmethod
    def send_order_confirmation_email(user, order):
        """Send order confirmation for marketplace purchase"""
        subject = f'✅ Order Confirmation #{order.id} - FarmWise Marketplace'
        
        html_content = render_to_string('emails/order_confirmation.html', {
            'user': user,
            'order': order,
            'items': order.order_items.all() if hasattr(order, 'order_items') else [],
            'action_link': f'{settings.APP_URL}/marketplace/orders/{order.id}/',
            'support_email': settings.DEFAULT_FROM_EMAIL,
        })
        
        text_content = strip_tags(html_content)
        
        return EmailService._send_email(
            subject=subject,
            message=text_content,
            html_message=html_content,
            recipient_list=[user.email]
        )
    
    @staticmethod
    def send_low_stock_alert_email(user, product):
        """Send low stock alert for marketplace listings"""
        subject = f'⚠️ Low Stock Alert: {product.product_name} is running low'
        
        html_content = render_to_string('emails/low_stock_alert.html', {
            'user': user,
            'product': product,
            'action_link': f'{settings.APP_URL}/marketplace/listings/{product.id}/edit/',
            'support_email': settings.DEFAULT_FROM_EMAIL,
        })
        
        text_content = strip_tags(html_content)
        
        return EmailService._send_email(
            subject=subject,
            message=text_content,
            html_message=html_content,
            recipient_list=[user.email]
        )
    
    @staticmethod
    def send_equipment_booking_confirmation(user, booking):
        """Send equipment booking confirmation"""
        subject = f'🚜 Equipment Booking Confirmation - {booking.equipment.name}'
        
        html_content = render_to_string('emails/equipment_booking_confirmation.html', {
            'user': user,
            'booking': booking,
            'is_owner': user == booking.equipment.owner,
            'action_link': f'{settings.APP_URL}/equipment/bookings/{booking.id}/',
            'support_email': settings.DEFAULT_FROM_EMAIL,
        })
        
        text_content = strip_tags(html_content)
        
        return EmailService._send_email(
            subject=subject,
            message=text_content,
            html_message=html_content,
            recipient_list=[user.email]
        )
    
    @staticmethod
    def send_insurance_claim_update(user, claim):
        """Send insurance claim status update"""
        subject = f'📄 Insurance Claim Update - {claim.get_status_display()}'
        
        html_content = render_to_string('emails/insurance_claim_update.html', {
            'user': user,
            'claim': claim,
            'action_link': f'{settings.APP_URL}/insurance/claims/{claim.id}/',
            'support_email': settings.DEFAULT_FROM_EMAIL,
        })
        
        text_content = strip_tags(html_content)
        
        return EmailService._send_email(
            subject=subject,
            message=text_content,
            html_message=html_content,
            recipient_list=[user.email]
        )
    
    @staticmethod
    def send_report_ready_email(user, report_name, download_link):
        """Send notification when a report is ready"""
        subject = f'📈 Your {report_name} is ready for download'
        
        html_content = render_to_string('emails/report_ready.html', {
            'user': user,
            'report_name': report_name,
            'download_link': download_link,
            'expiry_days': 7,
            'support_email': settings.DEFAULT_FROM_EMAIL,
        })
        
        text_content = strip_tags(html_content)
        
        return EmailService._send_email(
            subject=subject,
            message=text_content,
            html_message=html_content,
            recipient_list=[user.email]
        )
    
    @staticmethod
    def send_invitation_email(inviter, invitee_email, farm_name, invite_link):
        """Send farm invitation email"""
        subject = f'🌾 Join {inviter.get_full_name()} on FarmWise'
        
        html_content = render_to_string('emails/invitation.html', {
            'inviter': inviter,
            'farm_name': farm_name,
            'invite_link': invite_link,
            'app_name': 'FarmWise',
            'support_email': settings.DEFAULT_FROM_EMAIL,
        })
        
        text_content = strip_tags(html_content)
        
        return EmailService._send_email(
            subject=subject,
            message=text_content,
            html_message=html_content,
            recipient_list=[invitee_email]
        )
    
    @staticmethod
    def send_bulk_email(recipients, subject, template_name, context):
        """Send bulk email to multiple recipients"""
        successes = 0
        failures = 0
        
        for recipient in recipients:
            try:
                html_content = render_to_string(template_name, {**context, 'user': recipient, 'support_email': settings.DEFAULT_FROM_EMAIL})
                text_content = strip_tags(html_content)
                
                EmailService._send_email(
                    subject=subject,
                    message=text_content,
                    html_message=html_content,
                    recipient_list=[recipient.email]
                )
                successes += 1
            except Exception as e:
                logger.error(f"Failed to send bulk email to {recipient.email}: {e}")
                failures += 1
        
        return {'success': successes, 'failure': failures}
    
    @staticmethod
    def _send_email(subject, message, html_message, recipient_list):
        """Internal method to send email with error handling"""
        try:
            email = EmailMultiAlternatives(
                subject=subject,
                body=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=recipient_list,
                reply_to=[settings.DEFAULT_FROM_EMAIL]
            )
            email.attach_alternative(html_message, "text/html")
            email.send(fail_silently=False)
            logger.info(f"Email sent to {recipient_list}: {subject}")
            return True
        except Exception as e:
            logger.error(f"Failed to send email to {recipient_list}: {e}")
            return False
