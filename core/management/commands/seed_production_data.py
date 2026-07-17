"""
Management command to seed production database with sample data
Run: python manage.py seed_production_data
"""

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.db import transaction
from decimal import Decimal
import random
from datetime import datetime, timedelta

User = get_user_model()

from core.models import (
    Farm, Crop, Livestock, Equipment, Cooperative, 
    MarketplaceListing, SoilTest, WeatherData, IoTDevice, IoTReading
)

class Command(BaseCommand):
    help = 'Seed production database with sample data for ML training and testing'

    def handle(self, *args, **options):
        self.stdout.write('Starting to seed production database...')
        
        with transaction.atomic():
            self.create_sample_users()
            self.create_sample_farms()
            self.create_sample_crops()
            self.create_sample_livestock()
            self.create_sample_weather_data()
            self.create_sample_soil_tests()
            self.create_sample_marketplace_listings()
            self.create_sample_cooperatives()
            
        self.stdout.write(self.style.SUCCESS('Successfully seeded production database!'))

    def create_sample_users(self):
        """Create sample users for testing"""
        self.stdout.write('Creating sample users...')
        
        users_data = [
            {
                'username': 'farmer_john',
                'email': 'john@example.com',
                'password': 'Test123!',
                'user_type': 'farmer',
                'phone_number': '+254711111111',
                'farm_name': 'Green Valley Farm'
            },
            {
                'username': 'farmer_mary',
                'email': 'mary@example.com', 
                'password': 'Test123!',
                'user_type': 'farmer',
                'phone_number': '+254722222222',
                'farm_name': 'Sunrise Farm'
            },
            {
                'username': 'large_farm_co',
                'email': 'large@example.com',
                'password': 'Test123!',
                'user_type': 'large_farmer',
                'phone_number': '+254733333333',
                'farm_name': 'Commercial Farm Ltd'
            },
            {
                'username': 'agronomist_tom',
                'email': 'tom@example.com',
                'password': 'Test123!',
                'user_type': 'agronomist',
                'phone_number': '+254744444444',
            },
        ]
        
        for user_data in users_data:
            if not User.objects.filter(username=user_data['username']).exists():
                user = User.objects.create_user(**user_data)
                user.is_active = True
                user.save()
                self.stdout.write(f'Created user: {user.username}')

    def create_sample_farms(self):
        """Create sample farms with locations"""
        self.stdout.write('Creating sample farms...')
        
        users = User.objects.filter(user_type__in=['farmer', 'large_farmer'])
        
        farm_data = [
            {
                'name': 'Green Valley Farm',
                'location_lat': Decimal('-17.8292'),
                'location_lng': Decimal('31.0539'),
                'total_area_hectares': Decimal('50.5'),
                'soil_type': 'loamy',
                'agro_ecological_zone': 'natural_region_2a'
            },
            {
                'name': 'Sunrise Farm',
                'location_lat': Decimal('-18.1427'),
                'location_lng': Decimal('30.9156'),
                'total_area_hectares': Decimal('25.0'),
                'soil_type': 'sandy',
                'agro_ecological_zone': 'natural_region_3'
            },
            {
                'name': 'Commercial Farm Ltd',
                'location_lat': Decimal('-17.9439'),
                'location_lng': Decimal('30.1285'),
                'total_area_hectares': Decimal('200.0'),
                'soil_type': 'clay',
                'agro_ecological_zone': 'natural_region_2b'
            },
        ]
        
        for i, user in enumerate(users):
            if i < len(farm_data):
                farm_info = farm_data[i]
                if not Farm.objects.filter(owner=user, name=farm_info['name']).exists():
                    farm = Farm.objects.create(
                        owner=user,
                        name=farm_info['name'],
                        location_lat=farm_info['location_lat'],
                        location_lng=farm_info['location_lng'],
                        total_area_hectares=farm_info['total_area_hectares'],
                        soil_type=farm_info['soil_type'],
                        agro_ecological_zone=farm_info['agro_ecological_zone']
                    )
                    self.stdout.write(f'Created farm: {farm.name}')

    def create_sample_crops(self):
        """Create sample crops for ML training"""
        self.stdout.write('Creating sample crops...')
        
        farms = Farm.objects.all()
        crop_types = ['maize', 'wheat', 'soybeans', 'groundnuts', 'tobacco', 'cotton']
        
        for farm in farms:
            for crop_type in crop_types[:3]:  # 3 crops per farm
                planting_date = timezone.now() - timedelta(days=random.randint(30, 90))
                expected_harvest = planting_date + timedelta(days=random.randint(90, 120))
                
                crop = Crop.objects.create(
                    farm=farm,
                    crop_type=crop_type,
                    variety=random.choice(['hybrid', 'local', 'improved']),
                    planting_date=planting_date,
                    expected_harvest_date=expected_harvest,
                    area_hectares=Decimal(str(random.uniform(5.0, 20.0))),
                    current_growth_stage=random.choice(['seedling', 'vegetative', 'flowering', 'maturity']),
                    estimated_yield_tons_per_hectare=Decimal(str(random.uniform(2.0, 8.0))),
                    irrigation_method=random.choice(['rainfed', 'drip', 'sprinkler']),
                    fertilizer_used=random.choice(['npk', 'urea', 'organic', 'none']),
                    pest_status=random.choice(['none', 'low', 'medium', 'high']),
                    disease_status=random.choice(['none', 'low', 'medium', 'high'])
                )
                self.stdout.write(f'Created crop: {crop.crop_type} on {farm.name}')

    def create_sample_livestock(self):
        """Create sample livestock for ML training"""
        self.stdout.write('Creating sample livestock...')
        
        farms = Farm.objects.all()
        livestock_types = ['cattle', 'goats', 'sheep', 'poultry', 'pigs']
        
        for farm in farms:
            for livestock_type in livestock_types[:2]:  # 2 types per farm
                for _ in range(random.randint(5, 15)):  # Multiple animals per type
                    livestock = Livestock.objects.create(
                        farm=farm,
                        livestock_type=livestock_type,
                        breed=random.choice(['local', 'crossbreed', 'exotic']),
                        birth_date=timezone.now() - timedelta(days=random.randint(180, 1825)),
                        gender=random.choice(['male', 'female']),
                        weight_kg=Decimal(str(random.uniform(50.0, 500.0))),
                        health_status=random.choice(['healthy', 'sick', 'recovering']),
                        vaccination_status=random.choice(['up_to_date', 'overdue', 'none']),
                        feeding_method=random.choice(['grazing', 'feedlot', 'mixed']),
                        purpose=random.choice(['meat', 'milk', 'breeding', 'dual_purpose'])
                    )
                self.stdout.write(f'Created livestock: {livestock_type} on {farm.name}')

    def create_sample_weather_data(self):
        """Create sample weather data for ML training"""
        self.stdout.write('Creating sample weather data...')
        
        farms = Farm.objects.all()
        
        for farm in farms:
            # Create weather data for past 30 days
            for days_ago in range(30, 0, -1):
                date = timezone.now() - timedelta(days=days_ago)
                
                weather = WeatherData.objects.create(
                    farm=farm,
                    date=date,
                    temperature_celsius=Decimal(str(random.uniform(15.0, 35.0))),
                    humidity_percent=random.randint(30, 90),
                    rainfall_mm=Decimal(str(random.uniform(0.0, 50.0))),
                    wind_speed_kmh=Decimal(str(random.uniform(0.0, 30.0))),
                    soil_moisture_percent=random.randint(10, 80)
                )
            
            self.stdout.write(f'Created weather data for {farm.name}')

    def create_sample_soil_tests(self):
        """Create sample soil test data for ML training"""
        self.stdout.write('Creating sample soil tests...')
        
        farms = Farm.objects.all()
        
        for farm in farms:
            soil_test = SoilTest.objects.create(
                farm=farm,
                test_date=timezone.now() - timedelta(days=random.randint(10, 60)),
                ph_level=Decimal(str(random.uniform(5.0, 7.5))),
                nitrogen_level=random.choice(['low', 'medium', 'high']),
                phosphorus_level=random.choice(['low', 'medium', 'high']),
                potassium_level=random.choice(['low', 'medium', 'high']),
                organic_matter_percent=Decimal(str(random.uniform(1.0, 5.0))),
                texture=random.choice(['sandy', 'loamy', 'clay', 'silty']),
                recommendations=f"Apply {random.choice(['NPK', 'urea', 'organic'])} fertilizer. Consider {random.choice(['irrigation', 'drainage', 'liming'])}."
            )
            self.stdout.write(f'Created soil test for {farm.name}')

    def create_sample_marketplace_listings(self):
        """Create sample marketplace listings"""
        self.stdout.write('Creating sample marketplace listings...')
        
        users = User.objects.filter(user_type__in=['farmer', 'large_farmer'])
        products = ['maize', 'wheat', 'soybeans', 'groundnuts', 'cattle', 'goats']
        
        for user in users:
            for product in products[:2]:
                listing = MarketplaceListing.objects.create(
                    seller=user,
                    product_type=random.choice(['crop', 'livestock', 'equipment']),
                    product_name=product,
                    description=f"High quality {product} available for sale. Grown/raised using sustainable practices.",
                    quantity_available=Decimal(str(random.uniform(100.0, 1000.0))),
                    unit=random.choice(['kg', 'tons', 'heads']),
                    price_per_unit=Decimal(str(random.uniform(0.5, 50.0))),
                    location=random.choice(['Harare', 'Bulawayo', 'Gweru', 'Mutare']),
                    is_available=True
                )
                self.stdout.write(f'Created marketplace listing: {listing.product_name}')

    def create_sample_cooperatives(self):
        """Create sample cooperatives"""
        self.stdout.write('Creating sample cooperatives...')
        
        coop_data = [
            {
                'name': 'Zimbabwe Farmers Cooperative',
                'location': 'Harare',
                'registration_number': 'COOP001',
                'description': 'Supporting smallholder farmers across Zimbabwe'
            },
            {
                'name': 'Mashonaland Agricultural Union',
                'location': 'Mashonaland East',
                'registration_number': 'COOP002',
                'description': 'Promoting sustainable farming practices'
            }
        ]
        
        for coop_info in coop_data:
            if not Cooperative.objects.filter(name=coop_info['name']).exists():
                coop = Cooperative.objects.create(**coop_info)
                self.stdout.write(f'Created cooperative: {coop.name}')
