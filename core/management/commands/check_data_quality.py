"""
Management command to check data quality and generate alerts
Run: python manage.py check_data_quality
"""

from django.core.management.base import BaseCommand
from django.db.models import Count, Q
from django.utils import timezone
from datetime import timedelta
from core.models import User, Farm, CropSeason, Animal, Equipment
from core.models_analytics import AlertTrigger
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Check data quality and generate alerts for issues'

    def handle(self, *args, **options):
        self.stdout.write('Checking data quality...')
        
        alerts_created = 0
        
        # Check farms without location data
        farms_without_location = Farm.objects.filter(location__isnull=True)
        if farms_without_location.exists():
            for farm in farms_without_location:
                self.create_alert(
                    farm.owner,
                    farm,
                    'data_quality',
                    'high',
                    'Missing Location Data',
                    f'Farm "{farm.name}" is missing location coordinates. This affects weather forecasting and geofencing features.',
                    ['Add farm location coordinates in the farm settings', 'Use GPS to get accurate coordinates']
                )
                alerts_created += 1
            self.stdout.write(f'✓ Created {farms_without_location.count()} alerts for farms without location')
        
        # Check animals without tag numbers
        animals_without_tags = Animal.objects.filter(tag_number='')
        if animals_without_tags.exists():
            for animal in animals_without_tags[:10]:  # Limit to 10 to avoid spam
                self.create_alert(
                    animal.farm.owner,
                    animal.farm,
                    'data_quality',
                    'medium',
                    'Missing Animal Tag',
                    f'Animal without tag number detected. This affects tracking and health monitoring.',
                    ['Assign tag numbers to all animals', 'Use consistent tagging system']
                )
                alerts_created += 1
            self.stdout.write(f'✓ Created alerts for {min(animals_without_tags.count(), 10)} animals without tags')
        
        # Check crop seasons without harvest data
        old_seasons = CropSeason.objects.filter(
            status='growing',
            expected_harvest_date__lt=timezone.now().date() - timedelta(days=30)
        )
        if old_seasons.exists():
            for season in old_seasons:
                self.create_alert(
                    season.field.farm.owner,
                    season.field.farm,
                    'data_quality',
                    'medium',
                    'Missing Harvest Data',
                    f'Crop season "{season.crop_type.name if season.crop_type else "Unknown"}" was expected to be harvested but has no harvest data.',
                    ['Record actual harvest data', 'Update crop season status to harvested']
                )
                alerts_created += 1
            self.stdout.write(f'✓ Created {old_seasons.count()} alerts for missing harvest data')
        
        # Check users without profile completion
        incomplete_profiles = User.objects.filter(
            Q(phone_number='') | Q(profile_picture='') | Q(farm_name='')
        )
        if incomplete_profiles.exists():
            for user in incomplete_profiles[:5]:  # Limit to 5
                self.create_alert(
                    user,
                    None,
                    'data_quality',
                    'low',
                    'Incomplete Profile',
                    'Your profile is missing important information. Complete your profile for better system experience.',
                    ['Add phone number', 'Upload profile picture', 'Add farm name']
                )
                alerts_created += 1
            self.stdout.write(f'✓ Created alerts for {min(incomplete_profiles.count(), 5)} incomplete profiles')
        
        # Check equipment without maintenance records
        equipment_needing_maintenance = Equipment.objects.filter(
            last_maintenance_date__lt=timezone.now().date() - timedelta(days=180)
        )
        if equipment_needing_maintenance.exists():
            for equipment in equipment_needing_maintenance:
                self.create_alert(
                    equipment.owner,
                    None,
                    'equipment_maintenance',
                    'high',
                    'Equipment Maintenance Due',
                    f'Equipment "{equipment.name}" is due for maintenance. Last maintenance was over 6 months ago.',
                    ['Schedule maintenance', 'Check equipment condition', 'Update maintenance records']
                )
                alerts_created += 1
            self.stdout.write(f'✓ Created {equipment_needing_maintenance.count()} equipment maintenance alerts')
        
        self.stdout.write(f'\n✓ Data quality check complete. Created {alerts_created} alerts.')
        
    def create_alert(self, user, farm, alert_type, importance, title, description, recommended_actions):
        """Create an alert trigger"""
        try:
            AlertTrigger.objects.create(
                user=user,
                farm=farm,
                alert_type=alert_type,
                importance=importance,
                title=title,
                description=description,
                recommended_actions=recommended_actions,
                is_resolved=False
            )
        except Exception as e:
            logger.error(f"Error creating alert: {str(e)}")
