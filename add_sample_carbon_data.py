"""
Script to add sample carbon footprint data for testing
Run with: python manage.py shell < add_sample_carbon_data.py
Or: python add_sample_carbon_data.py
"""

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'farmwise.settings')
django.setup()

from datetime import datetime, timedelta
from decimal import Decimal
from core.models import Farm, EmissionSource, EmissionRecord, CarbonSequestration

def add_sample_carbon_data():
    """Add sample emission and sequestration data for testing"""
    
    # Get user's farms
    try:
        from django.contrib.auth import get_user_model
        User = get_user_model()
        user = User.objects.first()
        
        if not user:
            print("No users found in database")
            return
            
        farms = Farm.objects.filter(owner=user)
        if not farms.exists():
            print("No farms found for user")
            return
            
        print(f"Found {farms.count()} farms for user {user.username}")
        
        # Add emission sources
        emission_sources = []
        source_types = [
            ('fuel_diesel', 'Diesel Fuel', 2.68, 'liters'),
            ('electricity', 'Electricity', 0.45, 'kWh'),
            ('fertilizer', 'Fertilizer', 1.5, 'kg'),
            ('machinery', 'Machinery', 0.8, 'hours'),
        ]
        
        for farm in farms:
            for source_type, name, factor, unit in source_types:
                source, created = EmissionSource.objects.get_or_create(
                    farm=farm,
                    source_type=source_type,
                    name=name,
                    defaults={
                        'emission_factor': Decimal(str(factor)),
                        'unit': unit,
                        'is_active': True
                    }
                )
                if created:
                    emission_sources.append(source)
                    print(f"Created emission source: {name} for farm {farm.name}")
        
        # Add emission records for current year
        current_year = datetime.now().year
        current_month = datetime.now().month
        
        for farm in farms:
            for source in emission_sources:
                if source.farm != farm:
                    continue
                    
                # Add monthly records for the last 6 months
                for month in range(max(1, current_month - 5), current_month + 1):
                    record_date = datetime(current_year, month, 1).date()
                    
                    # Vary quantities based on source type
                    if source.source_type == 'fuel_diesel':
                        quantity = Decimal(str(100 + month * 10))  # 100-150 liters
                    elif source.source_type == 'electricity':
                        quantity = Decimal(str(500 + month * 50))  # 500-750 kWh
                    elif source.source_type == 'fertilizer':
                        quantity = Decimal(str(50 + month * 5))  # 50-75 kg
                    else:
                        quantity = Decimal(str(20 + month * 2))  # 20-30 hours
                    
                    # Calculate emissions
                    calculated_emissions = quantity * source.emission_factor
                    
                    record, created = EmissionRecord.objects.get_or_create(
                        farm=farm,
                        source=source,
                        record_date=record_date,
                        defaults={
                            'quantity_used': quantity,
                            'calculated_emissions_kg_co2e': calculated_emissions,
                            'description': f'Sample {source.name} usage for {record_date.strftime("%B %Y")}'
                        }
                    )
                    if created:
                        print(f"Created emission record: {source.name} for {record_date.strftime("%B %Y")}")
        
        # Add carbon sequestration data
        sequestration_types = [
            ('trees', 'Tree Planting', 20, 50),  # 20 kg per tree, 50 trees
            ('soil', 'Soil Management', 5, 10),  # 5 kg per hectare, 10 hectares
            ('cover_crops', 'Cover Crops', 3, 8),  # 3 kg per hectare, 8 hectares
        ]
        
        for farm in farms:
            for activity_type, name, sequestration_rate, quantity in sequestration_types:
                start_date = datetime(current_year, 1, 1).date()
                end_date = datetime(current_year, 12, 31).date()
                
                annual_sequestration = Decimal(str(sequestration_rate * quantity))
                
                sequestration, created = CarbonSequestration.objects.get_or_create(
                    farm=farm,
                    activity_type=activity_type,
                    name=name,
                    start_date=start_date,
                    defaults={
                        'end_date': end_date,
                        'annual_sequestration_kg_co2e': annual_sequestration,
                        'area_hectares': Decimal(str(quantity)),
                        'tree_count': quantity if activity_type == 'trees' else 0,
                        'description': f'Sample {name} activity for {current_year}'
                    }
                )
                if created:
                    print(f"Created carbon sequestration: {name} - {annual_sequestration} kg CO₂e/year")
        
        print("\n✅ Sample carbon footprint data added successfully!")
        print(f"Added emission sources: {len(emission_sources)}")
        print(f"Added emission records for current year")
        print(f"Added carbon sequestration activities")
        print("\nYou can now generate carbon footprint reports from the carbon report page.")
        
    except Exception as e:
        print(f"Error adding sample data: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    add_sample_carbon_data()
