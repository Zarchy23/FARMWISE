# core/services/crop_automation_service.py
"""
Automatic Crop Status Updates & Reminder Service
Handles automatic status changes and sending reminders based on crop dates
"""

import logging
from datetime import datetime, timedelta
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings
from ..models import CropSeason, Notification, Farm, User

logger = logging.getLogger(__name__)


class CropAutomationService:
    """Service for automatically managing crop status updates and reminders"""
    
    @staticmethod
    def check_and_update_crop_statuses(user: User = None, farm: Farm = None):
        """
        Check all crops and update their status based on dates.
        If user or farm is provided, only check those crops.
        """
        try:
            # Get crops to check
            if user:
                crops = CropSeason.objects.filter(field__farm__owner=user)
            elif farm:
                crops = CropSeason.objects.filter(field__farm=farm)
            else:
                crops = CropSeason.objects.all()
            
            today = timezone.now().date()
            updated_count = 0
            
            for crop in crops:
                updated = False
                
                # Check planting date - auto-update to "planted" if date passed
                if crop.planting_date and crop.planting_date <= today and crop.status not in ['planted', 'growing', 'harvested', 'failed']:
                    crop.status = 'planted'
                    updated = True
                    logger.info(f"Updated crop {crop.id} status to 'planted'")
                
                # Check harvest date - auto-update to "ready_for_harvest" if date passed
                if crop.expected_harvest_date and crop.expected_harvest_date <= today and crop.status not in ['harvested', 'failed', 'ready_for_harvest']:
                    # Only update if already planted
                    if crop.status in ['planted', 'growing']:
                        crop.status = 'ready_for_harvest'
                        updated = True
                        logger.info(f"Updated crop {crop.id} status to 'ready_for_harvest'")
                
                if updated:
                    crop.save()
                    updated_count += 1
            
            logger.info(f"Updated {updated_count} crops automatically")
            return updated_count
            
        except Exception as e:
            logger.error(f"Error in check_and_update_crop_statuses: {str(e)}")
            return 0
    
    @staticmethod
    def check_and_send_reminders(user: User = None, farm: Farm = None):
        """
        Check for upcoming dates and send reminders.
        Sends reminders 1 day before the date.
        """
        try:
            # Get crops to check
            if user:
                crops = CropSeason.objects.filter(field__farm__owner=user)
            elif farm:
                crops = CropSeason.objects.filter(field__farm=farm)
            else:
                crops = CropSeason.objects.all()
            
            today = timezone.now().date()
            reminder_date = today + timedelta(days=1)  # Tomorrow
            reminders_sent = 0
            
            for crop in crops:
                # Check planting date reminders
                if crop.planting_date == reminder_date and crop.status in ['planned', 'planted']:
                    farmer = crop.field.farm.owner
                    
                    # Create in-app notification
                    CropAutomationService._create_notification(
                        user=farmer,
                        crop=crop,
                        reminder_type='planting',
                        days_until=1
                    )
                    
                    # Send email
                    CropAutomationService._send_email_reminder(
                        user=farmer,
                        crop=crop,
                        reminder_type='planting',
                        days_until=1
                    )
                    
                    # Send SMS if available
                    CropAutomationService._send_sms_reminder(
                        user=farmer,
                        crop=crop,
                        reminder_type='planting',
                        days_until=1
                    )
                    
                    reminders_sent += 1
                    logger.info(f"Sent planting reminder for crop {crop.id}")
                
                # Check harvest date reminders
                if crop.expected_harvest_date == reminder_date and crop.status not in ['harvested', 'failed']:
                    farmer = crop.field.farm.owner
                    
                    # Create in-app notification
                    CropAutomationService._create_notification(
                        user=farmer,
                        crop=crop,
                        reminder_type='harvest',
                        days_until=1
                    )
                    
                    # Send email
                    CropAutomationService._send_email_reminder(
                        user=farmer,
                        crop=crop,
                        reminder_type='harvest',
                        days_until=1
                    )
                    
                    # Send SMS if available
                    CropAutomationService._send_sms_reminder(
                        user=farmer,
                        crop=crop,
                        reminder_type='harvest',
                        days_until=1
                    )
                    
                    reminders_sent += 1
                    logger.info(f"Sent harvest reminder for crop {crop.id}")
            
            logger.info(f"Sent {reminders_sent} reminders")
            return reminders_sent
            
        except Exception as e:
            logger.error(f"Error in check_and_send_reminders: {str(e)}")
            return 0
    
    @staticmethod
    def _create_notification(user: User, crop: CropSeason, reminder_type: str, days_until: int):
        """Create in-app notification for the farmer"""
        try:
            if reminder_type == 'planting':
                title = f"🌱 Time to Plant {crop.crop_type.name}"
                message = f"{crop.crop_type.name} in {crop.field.name} is ready to be planted on {crop.planting_date}!"
                icon = 'ri-seedling-line'
            else:  # harvest
                title = f"🌾 Ready to Harvest {crop.crop_type.name}"
                message = f"{crop.crop_type.name} in {crop.field.name} is ready for harvest on {crop.expected_harvest_date}!"
                icon = 'ri-leaf-line'
            
            notification = Notification.objects.create(
                user=user,
                notification_type='reminder',
                title=title,
                message=message,
                link=f'/crops/{crop.id}/'
            )
            logger.info(f"Created notification {notification.id}")
            return notification
            
        except Exception as e:
            logger.error(f"Error creating notification: {str(e)}")
    
    @staticmethod
    def _send_email_reminder(user: User, crop: CropSeason, reminder_type: str, days_until: int):
        """Send email reminder to the farmer"""
        try:
            if not user.email:
                logger.warning(f"User {user.id} has no email address")
                return
            
            if reminder_type == 'planting':
                subject = f"Reminder: Time to Plant {crop.crop_type.name}"
                message = f"""
Hello {user.first_name or user.username},

This is a reminder that your {crop.crop_type.name} planting is scheduled for {crop.planting_date}.

Field: {crop.field.name}
Farm: {crop.field.farm.name}
Status: {crop.get_status_display()}

Please ensure you are ready for planting on the scheduled date.

Best regards,
FarmWise Team
                """
            else:  # harvest
                subject = f"Reminder: Ready to Harvest {crop.crop_type.name}"
                message = f"""
Hello {user.first_name or user.username},

This is a reminder that your {crop.crop_type.name} is ready for harvest on {crop.expected_harvest_date}.

Field: {crop.field.name}
Farm: {crop.field.farm.name}
Estimated Yield: {crop.estimated_yield_kg} kg
Expected Revenue: ${crop.estimated_revenue}

Please arrange your harvest on the scheduled date.

Best regards,
FarmWise Team
                """
            
            send_mail(
                subject=subject,
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                fail_silently=True
            )
            logger.info(f"Sent email reminder to {user.email}")
            
        except Exception as e:
            logger.error(f"Error sending email reminder: {str(e)}")
    
    @staticmethod
    def _send_sms_reminder(user: User, crop: CropSeason, reminder_type: str, days_until: int):
        """Send SMS reminder to the farmer (if available)"""
        try:
            # Check if SMS service is configured
            if not hasattr(settings, 'SMS_PROVIDER') or not settings.SMS_PROVIDER:
                logger.info("SMS provider not configured, skipping SMS reminder")
                return
            
            # Get user phone number (assuming it's stored in profile)
            if not hasattr(user, 'profile') or not user.profile.phone_number:
                logger.warning(f"User {user.id} has no phone number")
                return
            
            if reminder_type == 'planting':
                sms_message = f"🌱 Reminder: Time to plant {crop.crop_type.name} in {crop.field.name} on {crop.planting_date}. - FarmWise"
            else:  # harvest
                sms_message = f"🌾 Reminder: Your {crop.crop_type.name} is ready to harvest on {crop.expected_harvest_date}. - FarmWise"
            
            # Send SMS via Twilio or other provider
            # This is a placeholder - implement based on your SMS provider
            logger.info(f"SMS reminder would be sent to {user.profile.phone_number}: {sms_message}")
            
        except Exception as e:
            logger.error(f"Error sending SMS reminder: {str(e)}")
    
    @staticmethod
    def run_automation_checks(user: User = None):
        """
        Main method to run all automation checks.
        Call this when a farmer loads the app/page.
        """
        try:
            logger.info(f"Running automation checks for user: {user}")
            
            # Update statuses
            updated = CropAutomationService.check_and_update_crop_statuses(user=user)
            
            # Send reminders
            reminders = CropAutomationService.check_and_send_reminders(user=user)
            
            logger.info(f"Automation complete - Updated: {updated}, Reminders: {reminders}")
            return {
                'updated_crops': updated,
                'reminders_sent': reminders
            }
            
        except Exception as e:
            logger.error(f"Error in run_automation_checks: {str(e)}")
            return {'updated_crops': 0, 'reminders_sent': 0}
