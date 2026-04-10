"""
Management command to create default emission sources for all farms
"""
from django.core.management.base import BaseCommand
from decimal import Decimal
from core.models import Farm, EmissionSource

class Command(BaseCommand):
    help = 'Create default emission sources for all farms'

    def handle(self, *args, **options):
        # Default emission sources with realistic emission factors
        DEFAULT_SOURCES = [
            {
                'source_type': 'fuel_diesel',
                'name': 'Diesel Fuel',
                'emission_factor': Decimal('2.68'),
                'unit': 'liter',
                'description': 'Diesel for tractors, pumps, generators'
            },
            {
                'source_type': 'fuel_petrol',
                'name': 'Petrol/Gasoline',
                'emission_factor': Decimal('2.31'),
                'unit': 'liter',
                'description': 'Petrol for small equipment'
            },
            {
                'source_type': 'electricity',
                'name': 'Electricity',
                'emission_factor': Decimal('0.82'),
                'unit': 'kWh',
                'description': 'Grid electricity for pumps and equipment'
            },
            {
                'source_type': 'lpg',
                'name': 'LPG/Gas',
                'emission_factor': Decimal('3.04'),
                'unit': 'kg',
                'description': 'LPG/Gas for heating or cooking'
            },
            {
                'source_type': 'fertilizer',
                'name': 'Synthetic Fertilizer',
                'emission_factor': Decimal('4.89'),
                'unit': 'kg',
                'description': 'Synthetic nitrogen fertilizer application'
            },
            {
                'source_type': 'pesticide',
                'name': 'Pesticide Application',
                'emission_factor': Decimal('12.5'),
                'unit': 'kg',
                'description': 'Chemical pesticide or herbicide'
            },
            {
                'source_type': 'transport_input',
                'name': 'Transport of Inputs',
                'emission_factor': Decimal('0.12'),
                'unit': 'ton-km',
                'description': 'Transporting seeds, fertilizers, etc.'
            },
            {
                'source_type': 'transport_output',
                'name': 'Transport of Products',
                'emission_factor': Decimal('0.12'),
                'unit': 'ton-km',
                'description': 'Transporting harvested products'
            },
            {
                'source_type': 'livestock_enteric',
                'name': 'Livestock Enteric Fermentation',
                'emission_factor': Decimal('0.065'),
                'unit': 'head-day',
                'description': 'Methane from cattle digestion'
            },
            {
                'source_type': 'manure',
                'name': 'Manure Management',
                'emission_factor': Decimal('0.015'),
                'unit': 'head-day',
                'description': 'Methane and nitrous oxide from manure'
            },
            {
                'source_type': 'machinery',
                'name': 'Machinery/Equipment',
                'emission_factor': Decimal('5.0'),
                'unit': 'hour',
                'description': 'Operating farm equipment and machinery'
            },
            {
                'source_type': 'other',
                'name': 'Other Emissions',
                'emission_factor': Decimal('1.0'),
                'unit': 'unit',
                'description': 'Other unspecified farm activities'
            },
        ]

        created_count = 0
        existing_count = 0
        
        # Get all farms
        farms = Farm.objects.all()
        
        if not farms.exists():
            self.stdout.write(self.style.WARNING('No farms found. Please create a farm first.'))
            return
        
        for farm in farms:
            for source_data in DEFAULT_SOURCES:
                # Check if source already exists
                if EmissionSource.objects.filter(
                    farm=farm,
                    source_type=source_data['source_type'],
                    name=source_data['name']
                ).exists():
                    existing_count += 1
                else:
                    EmissionSource.objects.create(
                        farm=farm,
                        source_type=source_data['source_type'],
                        name=source_data['name'],
                        emission_factor=source_data['emission_factor'],
                        unit=source_data['unit'],
                        is_active=True
                    )
                    created_count += 1
        
        self.stdout.write(
            self.style.SUCCESS(
                f'✓ Created {created_count} emission sources across {farms.count()} farm(s). '
                f'{existing_count} already existed.'
            )
        )
