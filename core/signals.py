# core/signals.py
# FARMWISE - Automated Signals for Business Logic

from django.db.models.signals import (
    post_save, pre_save, post_delete, pre_delete
)
from django.dispatch import receiver
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from decimal import Decimal
import logging

from .models import *

logger = logging.getLogger(__name__)


# ============================================================
# USER SIGNALS
# ============================================================

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """Create welcome notification when user registers"""
    if created:
        # Send welcome notification
        Notification.objects.create(
            user=instance,
            notification_type='success',
            title='Welcome to FarmWise!',
            message=f'Welcome {instance.get_full_name()}! Start by creating your first farm.',
            link='/farms/create/'
        )
        
        # Send welcome email
        if instance.email:
            try:
                send_mail(
                    subject='Welcome to FarmWise - Agriculture Management Platform',
                    message=f"""
                    Hello {instance.get_full_name()},
                    
                    Welcome to FarmWise! We're excited to help you manage your farm more efficiently.
                    
                    Here's what you can do:
                    • Add your farms and fields
                    • Track crops and livestock
                    • Monitor weather and pests
                    • Connect with buyers and equipment owners
                    
                    Get started: https://farmwise.com/dashboard/
                    
                    Best regards,
                    FarmWise Team
                    """,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[instance.email],
                    fail_silently=True,
                )
            except Exception as e:
                logger.error(f"Failed to send welcome email: {e}")


# ============================================================
# FARM SIGNALS
# ============================================================

@receiver(pre_save, sender=Farm)
def generate_farm_registration_number(sender, instance, **kwargs):
    """Auto-generate farm registration number if not provided"""
    if not instance.registration_number:
        import uuid
        instance.registration_number = f"FARM-{uuid.uuid4().hex[:8].upper()}"


@receiver(post_save, sender=Farm)
def notify_farm_creation(sender, instance, created, **kwargs):
    """Notify user when farm is created"""
    if created:
        Notification.objects.create(
            user=instance.owner,
            notification_type='success',
            title='Farm Created',
            message=f'Your farm "{instance.name}" has been created successfully!',
            link=f'/farms/{instance.id}/'
        )


# ============================================================
# CROP SEASON SIGNALS
# ============================================================

@receiver(pre_save, sender=CropSeason)
def calculate_expected_harvest_date(sender, instance, **kwargs):
    """Auto-calculate expected harvest date based on crop type"""
    if instance.planting_date and instance.crop_type and not instance.expected_harvest_date:
        from datetime import timedelta
        instance.expected_harvest_date = instance.planting_date + timedelta(
            days=instance.crop_type.growing_days
        )


@receiver(post_save, sender=CropSeason)
def check_harvest_reminder(sender, instance, created, **kwargs):
    """Create reminder for upcoming harvest"""
    if not created and instance.status == 'growing':
        from datetime import timedelta
        today = timezone.now().date()
        
        # 7 days before harvest
        if instance.expected_harvest_date and (instance.expected_harvest_date - today).days == 7:
            Notification.objects.create(
                user=instance.field.farm.owner,
                notification_type='reminder',
                title='Harvest Approaching',
                message=f'Your {instance.crop_type.name} in {instance.field.name} is ready for harvest in 7 days!',
                link=f'/crops/{instance.id}/harvest/'
            )


@receiver(post_save, sender=Harvest)
def update_crop_status_on_harvest(sender, instance, created, **kwargs):
    """Update crop season status when harvest is recorded"""
    if created:
        crop = instance.crop_season
        total_harvested = Harvest.objects.filter(crop_season=crop).aggregate(
            total=models.Sum('quantity_kg')
        )['total'] or 0
        
        if total_harvested >= (crop.estimated_yield_kg or 0):
            crop.status = 'harvested'
            crop.actual_harvest_date = timezone.now().date()
            crop.save()


# ============================================================
# LIVESTOCK SIGNALS
# ============================================================

@receiver(pre_save, sender=Animal)
def generate_animal_tag(sender, instance, **kwargs):
    """Auto-generate tag number if not provided"""
    if not instance.tag_number:
        import uuid
        instance.tag_number = f"ANI-{uuid.uuid4().hex[:6].upper()}"


@receiver(post_save, sender=HealthRecord)
def notify_health_record(sender, instance, created, **kwargs):
    """Notify farmer about health record and upcoming due dates"""
    if created:
        Notification.objects.create(
            user=instance.animal.farm.owner,
            notification_type='info',
            title='Health Record Added',
            message=f'Health record added for {instance.animal.tag_number}: {instance.get_record_type_display()}',
            link=f'/livestock/{instance.animal.id}/'
        )
        
        # Reminder for next due date
        if instance.next_due_date:
            Notification.objects.create(
                user=instance.animal.farm.owner,
                notification_type='reminder',
                title='Upcoming Treatment Due',
                message=f'{instance.animal.tag_number} is due for {instance.get_record_type_display()} on {instance.next_due_date}',
                link=f'/livestock/{instance.animal.id}/'
            )


@receiver(post_save, sender=BreedingRecord)
def update_expected_calving_date(sender, instance, created, **kwargs):
    """Calculate expected calving date based on animal type"""
    if created and instance.result == 'success' and not instance.expected_calving_date:
        if instance.animal.animal_type.gestation_days:
            from datetime import timedelta
            instance.expected_calving_date = instance.breeding_date + timedelta(
                days=instance.animal.animal_type.gestation_days
            )
            instance.save(update_fields=['expected_calving_date'])


# ============================================================
# EQUIPMENT BOOKING SIGNALS
# ============================================================

@receiver(post_save, sender=EquipmentBooking)
def update_equipment_status_on_booking(sender, instance, created, **kwargs):
    """Update equipment status when booking is confirmed"""
    if instance.status == 'confirmed':
        instance.equipment.status = 'rented'
        instance.equipment.save(update_fields=['status'])
    
    elif instance.status in ['completed', 'cancelled']:
        # Check if equipment has any active bookings
        has_active = EquipmentBooking.objects.filter(
            equipment=instance.equipment,
            status__in=['confirmed', 'active']
        ).exists()
        
        if not has_active:
            instance.equipment.status = 'available'
            instance.equipment.save(update_fields=['status'])


@receiver(pre_save, sender=EquipmentBooking)
def calculate_booking_totals(sender, instance, **kwargs):
    """Calculate booking totals before saving"""
    if instance.start_date and instance.end_date:
        instance.total_days = (instance.end_date - instance.start_date).days
        instance.total_cost = instance.total_days * instance.equipment.daily_rate


# ============================================================
# ORDER SIGNALS
# ============================================================

@receiver(post_save, sender=Order)
def update_listing_quantity(sender, instance, created, **kwargs):
    """Update product listing quantity when order is placed"""
    if created and instance.status == 'pending':
        listing = instance.listing
        listing.quantity -= instance.quantity
        if listing.quantity <= 0:
            listing.status = 'sold'
        listing.save()
        
        # Notify seller
        Notification.objects.create(
            user=listing.seller.owner,
            notification_type='info',
            title='New Order Received',
            message=f'New order for {instance.quantity} {listing.unit} of {listing.product_name}',
            link=f'/marketplace/orders/'
        )


@receiver(post_save, sender=Order)
def create_transaction_on_completion(sender, instance, created, **kwargs):
    """Create financial transaction when order is completed"""
    if instance.status == 'completed' and not created:
        # Check if transaction already exists
        existing = Transaction.objects.filter(
            farm=instance.listing.seller,
            description__icontains=f"Order #{instance.id}"
        ).exists()
        
        if not existing:
            Transaction.objects.create(
                farm=instance.listing.seller,
                transaction_type='income',
                category='crop_sales',
                amount=instance.total_amount,
                date=timezone.now().date(),
                description=f"Order #{instance.id} - {instance.listing.product_name}"
            )


# ============================================================
# PEST REPORT SIGNALS
# ============================================================

@receiver(post_save, sender=PestReport)
def notify_agronomist_on_high_severity(sender, instance, created, **kwargs):
    """Notify agronomist when high severity pest is detected"""
    if created and instance.severity in ['high', 'severe']:
        # Find agronomists in the area
        agronomists = User.objects.filter(user_type='agronomist', is_active=True)
        
        for agronomist in agronomists:
            Notification.objects.create(
                user=agronomist,
                notification_type='alert',
                title='High Severity Pest Alert',
                message=f'{instance.ai_diagnosis} detected on {instance.farm.name} with {instance.confidence}% confidence',
                link=f'/pest-detection/{instance.id}/'
            )


# ============================================================
# WEATHER ALERT SIGNALS
# ============================================================

@receiver(post_save, sender=WeatherAlert)
def send_weather_alert_sms(sender, instance, created, **kwargs):
    """Send SMS for critical weather alerts"""
    if created and instance.severity in ['alert', 'emergency']:
        if instance.farm.owner.accepts_sms and instance.farm.owner.phone_number:
            try:
                from twilio.rest import Client
                client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
                client.messages.create(
                    body=f"[FarmWise Alert] {instance.title}: {instance.message[:150]}",
                    from_=settings.TWILIO_PHONE_NUMBER,
                    to=instance.farm.owner.phone_number
                )
            except Exception as e:
                logger.error(f"Failed to send SMS: {e}")


# ============================================================
# INSURANCE CLAIM SIGNALS
# ============================================================

@receiver(post_save, sender=InsuranceClaim)
def process_claim_approval(sender, instance, created, **kwargs):
    """Process claim when approved"""
    if not created and instance.status == 'approved' and instance.approved_amount:
        # Create notification for farmer
        Notification.objects.create(
            user=instance.policy.farmer,
            notification_type='success',
            title='Insurance Claim Approved',
            message=f'Your claim for ${instance.approved_amount} has been approved!',
            link=f'/insurance/claims/'
        )


@receiver(post_save, sender=InsuranceClaim)
def create_payout_transaction(sender, instance, created, **kwargs):
    """Create transaction when claim is paid"""
    if instance.status == 'paid' and instance.payout_amount:
        Transaction.objects.create(
            farm=instance.policy.farm,
            transaction_type='income',
            category='insurance',
            amount=instance.payout_amount,
            date=timezone.now().date(),
            description=f"Insurance payout - Claim #{instance.id}"
        )


# ============================================================
# WORK SHIFT SIGNALS
# ============================================================

@receiver(pre_save, sender=WorkShift)
def calculate_shift_pay(sender, instance, **kwargs):
    """Calculate total pay for work shift"""
    if instance.hours_worked and instance.wage_rate:
        instance.total_pay = instance.hours_worked * instance.wage_rate


@receiver(post_save, sender=WorkShift)
def update_worker_total_hours(sender, instance, created, **kwargs):
    """Update worker's total hours for payroll"""
    if created:
        # This could trigger payroll recalculation
        pass


# ============================================================
# IRRIGATION SCHEDULE SIGNALS
# ============================================================

@receiver(pre_save, sender=IrrigationSchedule)
def calculate_water_volume(sender, instance, **kwargs):
    """Calculate estimated water volume based on duration"""
    if instance.duration_hours:
        # Assuming 1000 liters per hour per hectare
        area = instance.field.area_hectares
        instance.water_volume_liters = instance.duration_hours * area * 1000


# ============================================================
# TRANSACTION SIGNALS
# ============================================================

@receiver(post_save, sender=Transaction)
def update_crop_revenue(sender, instance, created, **kwargs):
    """Update crop season revenue when crop-related transaction is added"""
    if created and instance.related_crop and instance.transaction_type == 'income':
        crop = instance.related_crop
        total_revenue = Transaction.objects.filter(
            related_crop=crop,
            transaction_type='income'
        ).aggregate(total=models.Sum('amount'))['total'] or 0
        
        crop.actual_revenue = total_revenue
        crop.save(update_fields=['actual_revenue'])


# ============================================================
# CLEANUP SIGNALS
# ============================================================

@receiver(post_delete, sender=Harvest)
def update_crop_status_after_harvest_delete(sender, instance, **kwargs):
    """Update crop status when harvest is deleted"""
    crop = instance.crop_season
    total_harvested = Harvest.objects.filter(crop_season=crop).aggregate(
        total=models.Sum('quantity_kg')
    )['total'] or 0
    
    if total_harvested < (crop.estimated_yield_kg or 0):
        crop.status = 'growing'
        crop.actual_harvest_date = None
        crop.save()


@receiver(post_delete, sender=Animal)
def cleanup_related_records(sender, instance, **kwargs):
    """Log when animal is deleted"""
    logger.info(f"Animal {instance.tag_number} deleted from farm {instance.farm.name}")


# ============================================================
# SCHEDULED TASKS (Called by Celery)
# ============================================================

def check_overdue_crops():
    """Check for overdue crops and create notifications"""
    today = timezone.now().date()
    overdue_crops = CropSeason.objects.filter(
        status='growing',
        expected_harvest_date__lt=today
    )
    
    for crop in overdue_crops:
        Notification.objects.create(
            user=crop.field.farm.owner,
            notification_type='warning',
            title='Crop Harvest Overdue',
            message=f'{crop.crop_type.name} in {crop.field.name} is { (today - crop.expected_harvest_date).days } days overdue for harvest!',
            link=f'/crops/{crop.id}/'
        )


def check_upcoming_vaccinations():
    """Check for upcoming animal vaccinations"""
    today = timezone.now().date()
    from datetime import timedelta
    
    upcoming = HealthRecord.objects.filter(
        next_due_date__gte=today,
        next_due_date__lte=today + timedelta(days=7)
    )
    
    for record in upcoming:
        Notification.objects.create(
            user=record.animal.farm.owner,
            notification_type='reminder',
            title='Vaccination Due',
            message=f'{record.animal.tag_number} is due for {record.get_record_type_display()} on {record.next_due_date}',
            link=f'/livestock/{record.animal.id}/health/'
        )


def check_expiring_listings():
    """Check for expiring product listings"""
    today = timezone.now().date()
    expiring = ProductListing.objects.filter(
        status='active',
        expiry_date__lte=today + timezone.timedelta(days=3)
    )
    
    for listing in expiring:
        Notification.objects.create(
            user=listing.seller.owner,
            notification_type='warning',
            title='Listing Expiring Soon',
            message=f'Your listing for {listing.product_name} expires on {listing.expiry_date}',
            link=f'/marketplace/{listing.id}/'
        )