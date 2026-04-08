# core/tasks.py
# FARMWISE - Celery Async Tasks for Background Processing

from celery import shared_task
from django.core.mail import send_mail
from django.utils import timezone
from django.conf import settings
from django.contrib.auth import get_user_model
from datetime import timedelta
import logging
from decimal import Decimal

from .models import *

logger = logging.getLogger(__name__)

User = get_user_model()


# ============================================================
# CROP MANAGEMENT TASKS
# ============================================================

@shared_task
def check_overdue_crops():
    """Check for crops past their expected harvest date"""
    today = timezone.now().date()
    overdue_crops = CropSeason.objects.filter(
        status='growing',
        expected_harvest_date__lt=today
    )
    
    count = 0
    for crop in overdue_crops:
        days_overdue = (today - crop.expected_harvest_date).days
        
        Notification.objects.create(
            user=crop.field.farm.owner,
            notification_type='warning',
            title='Crop Harvest Overdue',
            message=f'{crop.crop_type.name} in {crop.field.name} is {days_overdue} days overdue for harvest!',
            link=f'/crops/{crop.id}/'
        )
        count += 1
    
    logger.info(f"Checked overdue crops: {count} notifications sent")
    return f"Sent {count} overdue crop notifications"


@shared_task
def update_crop_statuses():
    """Auto-update crop statuses based on dates"""
    today = timezone.now().date()
    
    # Update planted to growing
    planted = CropSeason.objects.filter(
        status='planted',
        planting_date__lte=today - timedelta(days=14)
    )
    planted_count = planted.update(status='growing')
    
    # Update growing to harvested (if past expected date + 30 days)
    overdue = CropSeason.objects.filter(
        status='growing',
        expected_harvest_date__lt=today - timedelta(days=30)
    )
    overdue_count = overdue.update(status='harvested')
    
    logger.info(f"Updated {planted_count} crops to growing, {overdue_count} to harvested")
    return f"Updated {planted_count} to growing, {overdue_count} to harvested"


# ============================================================
# LIVESTOCK MANAGEMENT TASKS
# ============================================================

@shared_task
def check_upcoming_vaccinations():
    """Check for upcoming vaccinations and send reminders"""
    today = timezone.now().date()
    upcoming = HealthRecord.objects.filter(
        next_due_date__gte=today,
        next_due_date__lte=today + timedelta(days=7)
    )
    
    count = 0
    for record in upcoming:
        days_until = (record.next_due_date - today).days
        
        Notification.objects.create(
            user=record.animal.farm.owner,
            notification_type='reminder',
            title='Vaccination Due Soon',
            message=f'{record.animal.tag_number} is due for {record.get_record_type_display()} in {days_until} days',
            link=f'/livestock/{record.animal.id}/'
        )
        count += 1
    
    logger.info(f"Checked vaccinations: {count} reminders sent")
    return f"Sent {count} vaccination reminders"


@shared_task
def check_pregnant_animals():
    """Check for animals approaching calving date"""
    today = timezone.now().date()
    upcoming_calvings = BreedingRecord.objects.filter(
        result='success',
        expected_calving_date__gte=today,
        expected_calving_date__lte=today + timedelta(days=14),
        animal__status='alive'
    )
    
    count = 0
    for record in upcoming_calvings:
        days_until = (record.expected_calving_date - today).days
        
        Notification.objects.create(
            user=record.animal.farm.owner,
            notification_type='alert',
            title='Calving Approaching',
            message=f'{record.animal.tag_number} expected to calve in {days_until} days. Prepare calving area.',
            link=f'/livestock/{record.animal.id}/'
        )
        count += 1
    
    return f"Sent {count} calving reminders"


# ============================================================
# MARKETPLACE TASKS
# ============================================================

@shared_task
def check_expiring_listings():
    """Check for product listings expiring soon"""
    today = timezone.now().date()
    expiring = ProductListing.objects.filter(
        status='active',
        expiry_date__isnull=False,
        expiry_date__gte=today,
        expiry_date__lte=today + timedelta(days=3)
    )
    
    count = 0
    for listing in expiring:
        days_until = (listing.expiry_date - today).days
        
        Notification.objects.create(
            user=listing.seller.owner,
            notification_type='warning',
            title='Listing Expiring Soon',
            message=f'Your listing for {listing.product_name} expires in {days_until} days',
            link=f'/marketplace/{listing.id}/'
        )
        count += 1
    
    # Also check for expired listings to mark as expired
    expired = ProductListing.objects.filter(
        status='active',
        expiry_date__isnull=False,
        expiry_date__lt=today
    )
    expired_count = expired.update(status='expired')
    
    return f"Sent {count} expiry warnings, marked {expired_count} as expired"


@shared_task
def cleanup_abandoned_carts():
    """Delete abandoned orders older than 7 days"""
    cutoff_date = timezone.now() - timedelta(days=7)
    abandoned = Order.objects.filter(
        status='pending',
        created_at__lt=cutoff_date
    )
    count = abandoned.count()
    abandoned.delete()
    
    logger.info(f"Cleaned up {count} abandoned carts")
    return f"Deleted {count} abandoned carts"


# ============================================================
# WEATHER ALERT TASKS
# ============================================================

@shared_task
def fetch_weather_data():
    """Fetch weather data from external API for all farms"""
    import requests
    
    farms = Farm.objects.filter(is_active=True)
    count = 0
    
    for farm in farms:
        try:
            lat = farm.location.y if farm.location else None
            lng = farm.location.x if farm.location else None
            
            if lat and lng:
                # OpenWeatherMap API
                url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lng}&appid={settings.OPENWEATHER_API_KEY}&units=metric"
                response = requests.get(url, timeout=10)
                
                if response.status_code == 200:
                    data = response.json()
                    # Store weather data (implement WeatherHistory model if needed)
                    pass
        except Exception as e:
            logger.error(f"Weather fetch failed for farm {farm.id}: {e}")
            count += 1
    
    return f"Processed weather for {farms.count() - count} farms"


@shared_task
def send_weather_alerts():
    """Send weather alerts based on forecast"""
    farms = Farm.objects.filter(is_active=True)
    count = 0
    
    # This would integrate with a weather API to detect severe conditions
    # For now, create sample alerts
    
    for farm in farms:
        # Check for extreme conditions (simplified)
        # In production, this would use actual forecast data
        
        if farm.location:
            # Create flood warning for certain regions (example)
            pass
    
    return f"Sent {count} weather alerts"


# ============================================================
# INSURANCE TASKS
# ============================================================

@shared_task
def check_expiring_insurance():
    """Check for insurance policies expiring soon"""
    today = timezone.now().date()
    expiring = InsurancePolicy.objects.filter(
        status='active',
        end_date__gte=today,
        end_date__lte=today + timedelta(days=30)
    )
    
    count = 0
    for policy in expiring:
        days_until = (policy.end_date - today).days
        
        Notification.objects.create(
            user=policy.farmer,
            notification_type='reminder',
            title='Insurance Expiring Soon',
            message=f'Your {policy.get_policy_type_display()} insurance expires in {days_until} days. Renew now!',
            link=f'/insurance/{policy.id}/'
        )
        count += 1
    
    return f"Sent {count} insurance expiration reminders"


@shared_task
def auto_expire_insurance():
    """Auto-expire insurance policies past their end date"""
    today = timezone.now().date()
    expired = InsurancePolicy.objects.filter(
        status='active',
        end_date__lt=today
    )
    count = expired.update(status='expired')
    
    logger.info(f"Auto-expired {count} insurance policies")
    return f"Expired {count} policies"


# ============================================================
# EQUIPMENT RENTAL TASKS
# ============================================================

@shared_task
def check_overdue_equipment():
    """Check for equipment rentals that are overdue"""
    today = timezone.now().date()
    overdue = EquipmentBooking.objects.filter(
        status='active',
        end_date__lt=today
    )
    
    count = 0
    for booking in overdue:
        days_overdue = (today - booking.end_date).days
        
        # Notify renter
        Notification.objects.create(
            user=booking.renter,
            notification_type='warning',
            title='Equipment Rental Overdue',
            message=f'Your rental of {booking.equipment.name} is {days_overdue} days overdue. Please return immediately.',
            link=f'/equipment/my-bookings/'
        )
        
        # Notify owner
        Notification.objects.create(
            user=booking.equipment.owner,
            notification_type='warning',
            title='Equipment Not Returned',
            message=f'{booking.renter.get_full_name()} has not returned {booking.equipment.name}. {days_overdue} days overdue.',
            link=f'/equipment/bookings/'
        )
        count += 1
    
    return f"Processed {count} overdue equipment rentals"


@shared_task
def send_booking_reminders():
    """Send reminders for upcoming equipment bookings"""
    tomorrow = timezone.now().date() + timedelta(days=1)
    upcoming = EquipmentBooking.objects.filter(
        status='confirmed',
        start_date=tomorrow
    )
    
    count = 0
    for booking in upcoming:
        Notification.objects.create(
            user=booking.renter,
            notification_type='reminder',
            title='Equipment Booking Tomorrow',
            message=f'Your rental of {booking.equipment.name} starts tomorrow. Pickup at {booking.pickup_location}',
            link=f'/equipment/my-bookings/'
        )
        count += 1
    
    return f"Sent {count} booking reminders"


# ============================================================
# REPORT GENERATION TASKS
# ============================================================

@shared_task
def generate_daily_reports():
    """Generate daily summary reports for all farms"""
    from datetime import date
    from decimal import Decimal
    
    farms = Farm.objects.filter(is_active=True)
    report_count = 0
    
    for farm in farms:
        today = timezone.now().date()
        
        # Calculate daily stats
        daily_income = Transaction.objects.filter(
            farm=farm,
            transaction_type='income',
            date=today
        ).aggregate(total=models.Sum('amount'))['total'] or Decimal('0')
        
        daily_expenses = Transaction.objects.filter(
            farm=farm,
            transaction_type='expense',
            date=today
        ).aggregate(total=models.Sum('amount'))['total'] or Decimal('0')
        
        # Create notification with daily summary
        Notification.objects.create(
            user=farm.owner,
            notification_type='info',
            title=f'Daily Report - {today}',
            message=f'Daily Summary: Income: ${daily_income}, Expenses: ${daily_expenses}, Net: ${daily_income - daily_expenses}',
            link='/reports/'
        )
        report_count += 1
    
    logger.info(f"Generated daily reports for {report_count} farms")
    return f"Generated reports for {report_count} farms"


@shared_task
def generate_weekly_reports():
    """Generate weekly summary reports"""
    from datetime import timedelta, date
    
    end_date = timezone.now().date()
    start_date = end_date - timedelta(days=7)
    
    farms = Farm.objects.filter(is_active=True)
    report_count = 0
    
    for farm in farms:
        weekly_income = Transaction.objects.filter(
            farm=farm,
            transaction_type='income',
            date__gte=start_date,
            date__lte=end_date
        ).aggregate(total=models.Sum('amount'))['total'] or Decimal('0')
        
        weekly_expenses = Transaction.objects.filter(
            farm=farm,
            transaction_type='expense',
            date__gte=start_date,
            date__lte=end_date
        ).aggregate(total=models.Sum('amount'))['total'] or Decimal('0')
        
        Notification.objects.create(
            user=farm.owner,
            notification_type='info',
            title=f'Weekly Report - {start_date} to {end_date}',
            message=f'Weekly Summary: Income: ${weekly_income}, Expenses: ${weekly_expenses}, Net: ${weekly_income - weekly_expenses}',
            link='/reports/financial/'
        )
        report_count += 1
    
    return f"Generated weekly reports for {report_count} farms"


# ============================================================
# PEST DETECTION TASKS
# ============================================================

@shared_task
def analyze_pest_image(image_path, report_id):
    """Async analysis of pest image using AI"""
    import base64
    import requests
    
    try:
        # Read image and convert to base64
        with open(image_path, 'rb') as f:
            image_data = base64.b64encode(f.read()).decode('utf-8')
        
        # Call AI service (example using OpenAI Vision)
        headers = {
            'Authorization': f'Bearer {settings.OPENAI_API_KEY}',
            'Content-Type': 'application/json'
        }
        
        payload = {
            'model': 'gpt-4-vision-preview',
            'messages': [
                {
                    'role': 'user',
                    'content': [
                        {
                            'type': 'text',
                            'text': 'Identify the pest or disease in this crop image. Return: pest name, confidence percentage, severity, and treatment recommendation.'
                        },
                        {
                            'type': 'image_url',
                            'image_url': {
                                'url': f'data:image/jpeg;base64,{image_data}'
                            }
                        }
                    ]
                }
            ],
            'max_tokens': 500
        }
        
        response = requests.post('https://api.openai.com/v1/chat/completions', headers=headers, json=payload, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            # Parse and update pest report
            # This would extract the structured data from AI response
            
            report = PestReport.objects.get(id=report_id)
            # report.ai_diagnosis = extracted_pest_name
            # report.confidence = extracted_confidence
            report.save()
            
            return f"Analysis complete for report {report_id}"
        else:
            logger.error(f"AI analysis failed: {response.text}")
            return f"Analysis failed for report {report_id}"
            
    except Exception as e:
        logger.error(f"Pest analysis error: {e}")
        return f"Error processing report {report_id}: {str(e)}"


# ============================================================
# NOTIFICATION TASKS
# ============================================================

@shared_task
def send_bulk_notifications(notification_ids):
    """Send bulk notifications via SMS/Email"""
    notifications = Notification.objects.filter(id__in=notification_ids)
    
    sms_count = 0
    email_count = 0
    
    for notification in notifications:
        if notification.sent_via_sms and notification.user.phone_number:
            try:
                from twilio.rest import Client
                client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
                client.messages.create(
                    body=f"[FarmWise] {notification.title}: {notification.message[:140]}",
                    from_=settings.TWILIO_PHONE_NUMBER,
                    to=notification.user.phone_number
                )
                sms_count += 1
            except Exception as e:
                logger.error(f"SMS failed for user {notification.user.id}: {e}")
        
        if notification.sent_via_email and notification.user.email:
            try:
                send_mail(
                    subject=f'FarmWise: {notification.title}',
                    message=notification.message,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[notification.user.email],
                    fail_silently=False
                )
                email_count += 1
            except Exception as e:
                logger.error(f"Email failed for user {notification.user.id}: {e}")
    
    return f"Sent {sms_count} SMS and {email_count} emails"


@shared_task
def cleanup_old_notifications():
    """Delete notifications older than 30 days"""
    cutoff_date = timezone.now() - timedelta(days=30)
    old_notifications = Notification.objects.filter(created_at__lt=cutoff_date)
    count = old_notifications.count()
    old_notifications.delete()
    
    logger.info(f"Cleaned up {count} old notifications")
    return f"Deleted {count} old notifications"


# ============================================================
# DATA CLEANUP TASKS
# ============================================================

@shared_task
def cleanup_old_sessions():
    """Clean up expired user sessions"""
    from django.contrib.sessions.models import Session
    expired_sessions = Session.objects.filter(expire_date__lt=timezone.now())
    count = expired_sessions.count()
    expired_sessions.delete()
    
    logger.info(f"Cleaned up {count} expired sessions")
    return f"Deleted {count} expired sessions"


@shared_task
def cleanup_old_audit_logs():
    """Delete audit logs older than 90 days (compliance)"""
    cutoff_date = timezone.now() - timedelta(days=90)
    old_logs = AuditLog.objects.filter(created_at__lt=cutoff_date)
    count = old_logs.count()
    old_logs.delete()
    
    logger.info(f"Cleaned up {count} old audit logs")
    return f"Deleted {count} old audit logs"


@shared_task
def cleanup_temporary_files():
    """Delete temporary files older than 24 hours"""
    import os
    import tempfile
    
    temp_dir = tempfile.gettempdir()
    count = 0
    cutoff = timezone.now() - timedelta(hours=24)
    
    for filename in os.listdir(temp_dir):
        if filename.startswith('farmwise_'):
            filepath = os.path.join(temp_dir, filename)
            mod_time = timezone.datetime.fromtimestamp(os.path.getmtime(filepath))
            if mod_time < cutoff:
                os.remove(filepath)
                count += 1
    
    return f"Deleted {count} temporary files"


# ============================================================
# DATABASE MAINTENANCE TASKS
# ============================================================

@shared_task
def update_materialized_views():
    """Refresh database materialized views for reporting"""
    from django.db import connection
    
    with connection.cursor() as cursor:
        # Refresh materialized views if they exist
        cursor.execute("REFRESH MATERIALIZED VIEW CONCURRENTLY IF EXISTS crop_yield_summary;")
        cursor.execute("REFRESH MATERIALIZED VIEW CONCURRENTLY IF EXISTS livestock_production_summary;")
        cursor.execute("REFRESH MATERIALIZED VIEW CONCURRENTLY IF EXISTS financial_summary;")
    
    return "Materialized views refreshed"


@shared_task
def vacuum_analyze():
    """Run VACUUM ANALYZE on database (PostgreSQL maintenance)"""
    from django.db import connection
    
    with connection.cursor() as cursor:
        cursor.execute("VACUUM ANALYZE;")
    
    return "Database vacuum and analyze completed"


# ============================================================
# WEATHER DATA TASKS
# ============================================================

@shared_task(bind=True, max_retries=3)
def fetch_weather_data(self):
    """Fetch real-time weather data from OpenWeatherMap API every 30 minutes"""
    import requests
    from django.conf import settings
    
    api_key = settings.OPENWEATHER_API_KEY
    if not api_key:
        logger.error("OpenWeatherMap API key not configured")
        return "Weather API key missing"
    
    farms = Farm.objects.all()
    updated_count = 0
    errors = []
    
    for farm in farms:
        try:
            # Use farm latitude/longitude if available, otherwise skip
            if not (farm.latitude and farm.longitude):
                logger.warning(f"Farm {farm.name} missing coordinates")
                continue
            
            # Call OpenWeatherMap API
            url = f"https://api.openweathermap.org/data/2.5/forecast?lat={farm.latitude}&lon={farm.longitude}&appid={api_key}&units=metric"
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            # Parse current weather (first forecast entry is closest to current)
            if data.get('list') and len(data['list']) > 0:
                current = data['list'][0]
                main = current['main']
                weather = current['weather'][0]
                wind = current.get('wind', {})
                clouds = current.get('clouds', {})
                
                # Prepare forecast data (next 5 days)
                forecast_list = []
                for i in range(0, min(40, len(data['list'])), 8):  # Every 24 hours
                    forecast_entry = data['list'][i]
                    forecast_list.append({
                        'date': forecast_entry['dt'],
                        'temp_high': forecast_entry['main']['temp_max'],
                        'temp_low': forecast_entry['main']['temp_min'],
                        'condition': forecast_entry['weather'][0]['main'],
                        'description': forecast_entry['weather'][0]['description'],
                        'icon': forecast_entry['weather'][0]['icon'],
                        'humidity': forecast_entry['main']['humidity'],
                        'wind_speed': forecast_entry['wind'].get('speed', 0),
                    })
                
                # Update or create WeatherData
                weather_obj, created = WeatherData.objects.update_or_create(
                    farm=farm,
                    defaults={
                        'temperature': main['temp'],
                        'feels_like': main.get('feels_like'),
                        'humidity': main['humidity'],
                        'pressure': main.get('pressure'),
                        'wind_speed': wind.get('speed', 0),
                        'wind_direction': wind.get('deg'),
                        'cloudiness': clouds.get('all'),
                        'condition': weather['main'],
                        'description': weather['description'],
                        'icon': weather['icon'],
                        'forecast_data': {'forecast': forecast_list},
                        'location': f"{data['city']['name']}, {data['city']['country']}",
                    }
                )
                updated_count += 1
                
                # Generate alerts based on weather data
                generate_weather_alerts.delay(farm.id)
                
                logger.info(f"Updated weather for {farm.name}: {weather['main']}")
        
        except requests.exceptions.RequestException as e:
            error_msg = f"Failed to fetch weather for {farm.name}: {str(e)}"
            logger.error(error_msg)
            errors.append(error_msg)
            # Retry with exponential backoff
            raise self.retry(exc=e, countdown=60 * (2 ** self.request.retries))
        except Exception as e:
            error_msg = f"Error processing weather data for {farm.name}: {str(e)}"
            logger.error(error_msg)
            errors.append(error_msg)
    
    result = f"Updated weather for {updated_count} farms"
    if errors:
        result += f" (with {len(errors)} errors)"
    
    logger.info(result)
    return result


@shared_task
def generate_weather_alerts(farm_id):
    """Generate weather alerts based on current conditions"""
    from django.utils import timezone
    
    try:
        farm = Farm.objects.get(id=farm_id)
        weather_data = WeatherData.objects.filter(farm=farm).first()
        
        if not weather_data:
            return f"No weather data for farm {farm_id}"
        
        # Delete previous alerts from this farm (to avoid duplicates)
        WeatherAlert.objects.filter(
            farm=farm,
            created_at__gte=timezone.now() - timedelta(minutes=35)
        ).delete()
        
        now = timezone.now()
        alerts_created = 0
        
        # HIGH TEMPERATURE ALERT
        if weather_data.temperature > 35:
            WeatherAlert.objects.create(
                farm=farm,
                alert_type='heatwave',
                severity='alert',
                title='Extreme Heat Alert',
                message=f'Temperature reached {weather_data.temperature}°C. High risk of crop stress and animal heat stress. Ensure proper irrigation and shade for livestock.',
                start_date=now,
                end_date=now + timedelta(hours=6)
            )
            alerts_created += 1
        elif weather_data.temperature > 32:
            WeatherAlert.objects.create(
                farm=farm,
                alert_type='heatwave',
                severity='warning',
                title='High Temperature Warning',
                message=f'Temperature at {weather_data.temperature}°C. Monitor crops for water stress and provide adequate irrigation.',
                start_date=now,
                end_date=now + timedelta(hours=12)
            )
            alerts_created += 1
        
        # LOW TEMPERATURE ALERT (FROST)
        if weather_data.temperature < 0:
            WeatherAlert.objects.create(
                farm=farm,
                alert_type='frost',
                severity='emergency',
                title='Frost Warning - Crop Damage Risk',
                message=f'Temperature dropped to {weather_data.temperature}°C. Cover sensitive crops immediately to prevent frost damage.',
                start_date=now,
                end_date=now + timedelta(hours=8)
            )
            alerts_created += 1
        elif weather_data.temperature < 5:
            WeatherAlert.objects.create(
                farm=farm,
                alert_type='frost',
                severity='warning',
                title='Frost Alert',
                message=f'Low temperature of {weather_data.temperature}°C expected. Protect sensitive crops.',
                start_date=now,
                end_date=now + timedelta(hours=12)
            )
            alerts_created += 1
        
        # HIGH HUMIDITY ALERT (Fungal Diseases)
        if weather_data.humidity > 90:
            WeatherAlert.objects.create(
                farm=farm,
                alert_type='storm',
                severity='warning',
                title='Very High Humidity - Disease Risk',
                message=f'Humidity at {weather_data.humidity}%. Fungal diseases are likely. Apply fungicides and ensure proper crop ventilation.',
                start_date=now,
                end_date=now + timedelta(hours=12)
            )
            alerts_created += 1
        elif weather_data.humidity > 75:
            WeatherAlert.objects.create(
                farm=farm,
                alert_type='storm',
                severity='info',
                title='Humidity Advisory',
                message=f'Humidity at {weather_data.humidity}%. Monitor crops for fungal infections and ensure proper spacing.',
                start_date=now,
                end_date=now + timedelta(hours=24)
            )
            alerts_created += 1
        
        # HIGH WIND ALERT
        if weather_data.wind_speed > 15:
            WeatherAlert.objects.create(
                farm=farm,
                alert_type='high_wind',
                severity='alert',
                title='Strong Wind Alert',
                message=f'Wind speed at {weather_data.wind_speed:.1f} m/s. Secure loose structures and support taller crops.',
                start_date=now,
                end_date=now + timedelta(hours=8)
            )
            alerts_created += 1
        elif weather_data.wind_speed > 10:
            WeatherAlert.objects.create(
                farm=farm,
                alert_type='high_wind',
                severity='warning',
                title='Moderate Wind Advisory',
                message=f'Wind speed at {weather_data.wind_speed:.1f} m/s. Be cautious when applying pesticides.',
                start_date=now,
                end_date=now + timedelta(hours=12)
            )
            alerts_created += 1
        
        # RAINY CONDITIONS ALERT
        if 'rain' in weather_data.condition.lower() or 'thunderstorm' in weather_data.condition.lower():
            WeatherAlert.objects.create(
                farm=farm,
                alert_type='heavy_rain',
                severity='warning',
                title='Rainfall Expected - Operational Impact',
                message=f'{weather_data.condition} expected. Avoid spraying pesticides, harvesting may be delayed. Prepare drainage for waterlogged areas.',
                start_date=now,
                end_date=now + timedelta(hours=12)
            )
            alerts_created += 1
            
            if 'thunderstorm' in weather_data.condition.lower():
                WeatherAlert.objects.create(
                    farm=farm,
                    alert_type='storm',
                    severity='emergency',
                    title='Thunderstorm Warning',
                    message='Thunderstorm approaching. Secure livestock, move equipment to shelter, and avoid outdoor activities.',
                    start_date=now,
                    end_date=now + timedelta(hours=6)
                )
                alerts_created += 1
        
        # DRY CONDITIONS ALERT
        if weather_data.humidity < 30 and 'rain' not in weather_data.condition.lower():
            WeatherAlert.objects.create(
                farm=farm,
                alert_type='drought',
                severity='warning',
                title='Dry Conditions - Irrigation Recommended',
                message=f'Low humidity ({weather_data.humidity}%) and no rainfall expected. Plan irrigation to prevent drought stress.',
                start_date=now,
                end_date=now + timedelta(hours=24)
            )
            alerts_created += 1
        
        logger.info(f"Generated {alerts_created} weather alerts for farm {farm.name}")
        return f"Generated {alerts_created} alerts for {farm.name}"
    
    except Farm.DoesNotExist:
        logger.error(f"Farm {farm_id} not found")
        return f"Farm {farm_id} not found"
    except Exception as e:
        logger.error(f"Error generating weather alerts: {str(e)}")
        return f"Error generating alerts: {str(e)}"



# ============================================================
# EXPORT TASKS
# ============================================================

@shared_task
def generate_export_file(export_type, user_id, filters):
    """Generate export file asynchronously"""
    import csv
    import json
    from io import StringIO
    from django.core.files.base import ContentFile
    
    user = User.objects.get(id=user_id)
    timestamp = timezone.now().strftime('%Y%m%d_%H%M%S')
    filename = f"export_{export_type}_{timestamp}.csv"
    
    output = StringIO()
    writer = csv.writer(output)
    
    if export_type == 'crops':
        writer.writerow(['Crop', 'Field', 'Farm', 'Planting Date', 'Harvest Date', 'Yield (kg)', 'Revenue'])
        crops = CropSeason.objects.filter(field__farm__owner=user)
        for crop in crops:
            writer.writerow([
                crop.crop_type.name,
                crop.field.name,
                crop.field.farm.name,
                crop.planting_date,
                crop.actual_harvest_date or '',
                crop.actual_yield_kg or '',
                crop.actual_revenue or ''
            ])
    
    elif export_type == 'livestock':
        writer.writerow(['Tag', 'Species', 'Breed', 'Gender', 'Birth Date', 'Status', 'Weight (kg)'])
        animals = Animal.objects.filter(farm__owner=user)
        for animal in animals:
            writer.writerow([
                animal.tag_number,
                animal.animal_type.get_species_display(),
                animal.animal_type.breed,
                animal.get_gender_display(),
                animal.birth_date or '',
                animal.get_status_display(),
                animal.weight_kg or ''
            ])
    
    elif export_type == 'transactions':
        writer.writerow(['Date', 'Type', 'Category', 'Amount', 'Description'])
        transactions = Transaction.objects.filter(farm__owner=user)
        for t in transactions:
            writer.writerow([
                t.date,
                t.get_transaction_type_display(),
                t.get_category_display(),
                t.amount,
                t.description
            ])
    
    # Save file (implement file storage logic)
    # This would save to S3 or local storage
    
    # Create notification with download link
    Notification.objects.create(
        user=user,
        notification_type='success',
        title='Export Ready',
        message=f'Your {export_type} export is ready for download',
        link=f'/exports/{filename}'
    )
    
    return f"Export {filename} generated for user {user_id}"