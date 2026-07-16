# core/management/commands/setup_location_service.py
# Management command to setup location service with sample data

from django.core.management.base import BaseCommand
from django.contrib.gis.geos import Point, Polygon
from core.models import Farm
from core.models_location import FarmLocation, Field, CropRotationPlan
from core.services.location_service import LocationService


class Command(BaseCommand):
    help = 'Setup location service with farm locations and field boundaries'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--sample',
            action='store_true',
            help='Create sample farm locations and fields'
        )
    
    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Setting up Location Service...\n'))
        
        # Check if PostGIS is enabled
        try:
            # Try to create a test point
            test_point = Point(0, 0)
            self.stdout.write(self.style.SUCCESS('✓ PostGIS is enabled and working'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'✗ PostGIS error: {str(e)}'))
            self.stdout.write(self.style.WARNING('Make sure PostGIS extension is installed in PostgreSQL'))
            return
        
        if options['sample']:
            self.create_sample_data()
        
        # Generate rotation plans for existing fields
        self.generate_rotation_plans()
        
        self.stdout.write(self.style.SUCCESS('\n✓ Location Service setup complete!'))
    
    def create_sample_data(self):
        """Create sample farm locations and fields"""
        self.stdout.write('Creating sample location data...\n')
        
        farms = Farm.objects.all()[:3]  # Get first 3 farms
        
        sample_data = [
            {
                'latitude': -1.2921,
                'longitude': 36.8219,
                'region': 'Nairobi',
                'district': 'Kiambu',
                'address': 'Sample Farm 1, Kiambu County'
            },
            {
                'latitude': -0.3522,
                'longitude': 36.6799,
                'region': 'Central',
                'district': 'Muranga',
                'address': 'Sample Farm 2, Muranga County'
            },
            {
                'latitude': 0.0236,
                'longitude': 37.9062,
                'region': 'Eastern',
                'district': 'Machakos',
                'address': 'Sample Farm 3, Machakos County'
            }
        ]
        
        for farm, data in zip(farms, sample_data):
            try:
                location = LocationService.create_farm_location(
                    farm=farm,
                    latitude=data['latitude'],
                    longitude=data['longitude'],
                    address=data['address'],
                    region=data['region'],
                    district=data['district']
                )
                self.stdout.write(self.style.SUCCESS(f'Created location for {farm.name}'))
            except Exception as e:
                self.stdout.write(self.style.WARNING(f'Could not create location for {farm.name}: {str(e)}'))
        
        # Create sample fields
        self.stdout.write('\nCreating sample fields...\n')
        
        for farm in farms:
            try:
                # Create a sample field boundary (square polygon)
                boundary_coords = [
                    (36.82, -1.29),
                    (36.83, -1.29),
                    (36.83, -1.30),
                    (36.82, -1.30),
                    (36.82, -1.29)
                ]
                
                field = LocationService.create_field(
                    farm=farm,
                    name=f'{farm.name} - Field 1',
                    field_type='arable',
                    boundary_coords=boundary_coords,
                    area_hectares=2.5,
                    soil_type='Loamy',
                    soil_fertility='good'
                )
                self.stdout.write(self.style.SUCCESS(f'Created field {field.name}'))
            except Exception as e:
                self.stdout.write(self.style.WARNING(f'Could not create field: {str(e)}'))
    
    def generate_rotation_plans(self):
        """Generate crop rotation plans for all fields"""
        self.stdout.write('\nGenerating crop rotation plans...\n')
        
        from core.models_location import Field
        
        fields = Field.objects.all()
        created_count = 0
        
        for field in fields:
            try:
                plan = LocationService.generate_crop_rotation_plan(field)
                if plan:
                    created_count += 1
                    self.stdout.write(self.style.SUCCESS(f'Generated rotation plan for {field.name}'))
            except Exception as e:
                self.stdout.write(self.style.WARNING(f'Could not generate rotation for {field.name}: {str(e)}'))
        
        self.stdout.write(self.style.SUCCESS(f'\n✓ Generated {created_count} rotation plans'))
