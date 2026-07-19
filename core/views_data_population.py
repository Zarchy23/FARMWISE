"""
Data Population Views
Web-based data population for environments without shell access
"""

from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.utils import timezone
from datetime import timedelta, date
from decimal import Decimal
import random
from core.models import User, Farm, CropSeason, Animal, Equipment, Cooperative, Asset, Field, CropType, AnimalType
import logging

logger = logging.getLogger(__name__)


@login_required
def data_population_dashboard(request):
    """Data population dashboard for admin use"""
    
    if not request.user.is_superuser and request.user.user_type != 'admin':
        return render(request, '404.html')
    
    # Get current data counts
    counts = {
        'users': User.objects.count(),
        'farms': Farm.objects.count(),
        'cooperatives': Cooperative.objects.count(),
        'crop_seasons': CropSeason.objects.count(),
        'animals': Animal.objects.count(),
        'equipment': Equipment.objects.count(),
        'assets': Asset.objects.count(),
    }
    
    return render(request, 'data_population/dashboard.html', {'counts': counts})


@login_required
def populate_sample_data(request):
    """Populate sample data for testing"""

    if not request.user.is_superuser and request.user.user_type != 'admin':
        return JsonResponse({'success': False, 'message': 'Unauthorized'}, status=403)

    try:
        created = {
            'users': 0,
            'farms': 0,
            'cooperatives': 0,
            'crop_seasons': 0,
            'animals': 0,
            'equipment': 0,
            'assets': 0,
        }

        # Create Cooperatives
        coop_names = ['Green Valley Cooperative', 'Sunrise Farmers Union', 'Harvest Alliance', 'AgriTech Collective']
        for name in coop_names:
            if not Cooperative.objects.filter(name=name).exists():
                Cooperative.objects.create(
                    name=name,
                    registration_number=f'COOP/{random.randint(1000, 9999)}',
                    address=random.choice(['Harare', 'Bulawayo', 'Mutare', 'Gweru', 'Masvingo']),
                    email=f'{name.lower().replace(" ", ".")}@coop.co.zw',
                    phone_number=f'+2637{random.randint(10000000, 99999999)}',
                    member_count=random.randint(10, 100),
                    total_farm_area=Decimal(str(random.uniform(50, 500))),
                    is_active=True
                )
                created['cooperatives'] += 1

        cooperatives = list(Cooperative.objects.all())

        # Skip user creation if users already exist
        users = list(User.objects.filter(user_type='farmer'))
        if not users:
            # Create Users only if no farmers exist
            user_types = ['farmer', 'cooperative_admin', 'agronomist', 'veterinarian', 'equipment_operator']
            first_names = ['Tawanda', 'Chipo', 'Farai', 'Rumbidzai', 'Tendai', 'Nyasha', 'Kudzai', 'Precious', 'Takudzwa', 'Nomatter']
            last_names = ['Moyo', 'Chikowore', 'Dube', 'Nkomo', 'Moyo', 'Sibanda', 'Ndlovu', 'Mujuru', 'Chiweshe', 'Mugabe']

            for i in range(20):
                first_name = random.choice(first_names)
                last_name = random.choice(last_names)
                username = f"{first_name.lower()}.{last_name.lower()}{random.randint(1, 99)}"

                if not User.objects.filter(username=username).exists():
                    user = User.objects.create_user(
                        username=username,
                        email=f'{username}@farmwise.co.zw',
                        password='password123',
                        first_name=first_name,
                        last_name=last_name,
                        phone_number=f'+2637{random.randint(10000000, 99999999)}',
                        user_type=random.choice(user_types),
                        location_lat=Decimal(str(random.uniform(-22.5, -15.5))),
                        location_lng=Decimal(str(random.uniform(25.0, 33.0))),
                        is_active=True
                    )
                    if cooperatives:
                        user.cooperative = random.choice(cooperatives)
                        user.save()
                    created['users'] += 1

            users = list(User.objects.filter(user_type='farmer'))
        
        # Create Farms
        farm_types = ['crop', 'livestock', 'mixed', 'poultry', 'dairy']
        crop_types = ['maize', 'wheat', 'rice', 'coffee', 'tea', 'sugarcane', 'vegetables', 'fruits']
        
        for i in range(30):
            if users:
                owner = random.choice(users)
                farm_name = f"{owner.first_name}'s Farm {random.randint(1, 5)}"
                
                if not Farm.objects.filter(name=farm_name, owner=owner).exists():
                    Farm.objects.create(
                        name=farm_name,
                        owner=owner,
                        location={"lat": float(random.uniform(-22.5, -15.5)), "lng": float(random.uniform(25.0, 33.0))},
                        address=random.choice(['Harare', 'Bulawayo', 'Mutare', 'Gweru', 'Masvingo']),
                        farm_type=random.choice(farm_types),
                        total_area_hectares=Decimal(str(random.uniform(1, 100))),
                        cooperative=random.choice(cooperatives) if cooperatives else None
                    )
                    created['farms'] += 1
        
        farms = list(Farm.objects.all())

        # Create Fields for farms
        for farm in farms:
            num_fields = random.randint(1, 3)
            for i in range(num_fields):
                field_name = f"{farm.name} - Field {i+1}"
                if not Field.objects.filter(farm=farm, name=field_name).exists():
                    # Calculate area using Decimal operations
                    field_area = farm.total_area_hectares / Decimal(num_fields)
                    Field.objects.create(
                        farm=farm,
                        name=field_name,
                        area_hectares=field_area,
                        soil_type=random.choice(['sandy', 'clay', 'loamy', 'silty', 'peaty']),
                        slope=random.choice(['flat', 'gentle', 'moderate', 'steep']),
                        drainage=random.choice(['excellent', 'good', 'moderate', 'poor']),
                        irrigation_type=random.choice(['none', 'drip', 'sprinkler', 'flood']),
                        irrigation_available=random.choice([True, False]),
                        is_active=True
                    )

        fields = list(Field.objects.all())

        # Create CropTypes if they don't exist
        for crop_name in crop_types:
            if not CropType.objects.filter(name=crop_name).exists():
                CropType.objects.create(
                    name=crop_name,
                    category=random.choice(['cereal', 'vegetable', 'fruit', 'legume', 'tuber']),
                    growing_days=random.randint(60, 180),
                    water_requirement_mm=random.randint(200, 800),
                    expected_yield_kg_per_ha=Decimal(str(random.uniform(1000, 5000))),
                    is_active=True
                )

        crop_type_objects = list(CropType.objects.all())

        # Create Crop Seasons
        season_choices = ['long_rain', 'short_rain', 'main', 'off']

        for field in fields:
            if field.farm.farm_type in ['crop', 'mixed']:
                for season in season_choices[:2]:  # Create 2 seasons per field
                    if not CropSeason.objects.filter(field=field, season=season).exists():
                        CropSeason.objects.create(
                            field=field,
                            crop_type=random.choice(crop_type_objects),
                            season=season,
                            variety=random.choice(['Standard', 'Improved', 'Hybrid', 'Local']),
                            planting_date=date(2024, random.randint(1, 12), random.randint(1, 28)),
                            expected_harvest_date=date(2024, random.randint(6, 12), random.randint(1, 28)),
                            status=random.choice(['planted', 'growing', 'harvested', 'failed']),
                            estimated_yield_kg=Decimal(str(random.uniform(1000, 5000))),
                            notes=f'{season} season for {field.name}'
                        )
                        created['crop_seasons'] += 1

        # Create AnimalTypes if they don't exist
        animal_species = ['cattle', 'goat', 'sheep', 'chicken', 'pig']
        for species in animal_species:
            if not AnimalType.objects.filter(species=species, breed='Standard').exists():
                AnimalType.objects.create(
                    species=species,
                    breed='Standard',
                    avg_lifespan_years=random.randint(5, 15),
                    gestation_days=random.randint(100, 300),
                    market_price=Decimal(str(random.uniform(100, 1000))),
                    is_active=True
                )

        animal_type_objects = list(AnimalType.objects.all())

        # Create Animals
        for farm in farms:
            if farm.farm_type in ['livestock', 'mixed', 'dairy', 'poultry']:
                num_animals = random.randint(5, 50)
                for i in range(num_animals):
                    tag_number = f'AN{random.randint(10000, 99999)}'
                    if not Animal.objects.filter(tag_number=tag_number).exists():
                        Animal.objects.create(
                            farm=farm,
                            animal_type=random.choice(animal_type_objects),
                            tag_number=tag_number,
                            gender=random.choice(['male', 'female']),
                            birth_date=date(2020 + random.randint(0, 4), random.randint(1, 12), random.randint(1, 28)),
                            weight_kg=Decimal(str(random.uniform(20, 500))),
                            status=random.choice(['alive', 'sold', 'dead'])
                        )
                        created['animals'] += 1
        
        # Create Equipment
        equipment_types = ['tractor', 'plow', 'harvester', 'irrigation_system', 'sprayer', 'truck']

        for farm in farms:
            num_equipment = random.randint(1, 5)
            for i in range(num_equipment):
                equipment_name = f'{random.choice(equipment_types).title()} {random.randint(1, 100)}'
                if not Equipment.objects.filter(farm=farm, name=equipment_name).exists():
                    Equipment.objects.create(
                        farm=farm,
                        equipment_type=random.choice(equipment_types),
                        name=equipment_name,
                        purchase_date=date(2018 + random.randint(0, 6), random.randint(1, 12), random.randint(1, 28)),
                        last_maintenance_date=date(2024, random.randint(1, 6), random.randint(1, 28)),
                        status=random.choice(['operational', 'maintenance', 'broken']),
                        purchase_price=Decimal(str(random.uniform(50000, 500000)))
                    )
                    created['equipment'] += 1

        # Create Assets (personal assets for users)
        asset_types = ['tractor', 'harvester', 'planter', 'sprayer', 'plow', 'cultivator', 'trailer', 'irrigation', 'vehicle', 'tool', 'machinery', 'other']
        asset_conditions = ['excellent', 'good', 'fair', 'poor', 'broken']
        asset_statuses = ['active', 'maintenance', 'repair', 'sale', 'retired', 'lost']

        all_users = list(User.objects.all())
        for user in all_users:
            num_assets = random.randint(1, 3)
            for i in range(num_assets):
                asset_name = f"{user.first_name}'s {random.choice(asset_types).title()} {random.randint(1, 50)}"
                serial_number = f'AS{random.randint(10000, 99999)}'
                if not Asset.objects.filter(owner=user, name=asset_name).exists():
                    Asset.objects.create(
                        owner=user,
                        name=asset_name,
                        asset_type=random.choice(asset_types),
                        description=f'Personal {random.choice(asset_types)} for {user.first_name}',
                        serial_number=serial_number,
                        purchase_date=date(2018 + random.randint(0, 6), random.randint(1, 12), random.randint(1, 28)),
                        purchase_price=Decimal(str(random.uniform(10000, 200000))),
                        current_value=Decimal(str(random.uniform(5000, 150000))),
                        condition=random.choice(asset_conditions),
                        status=random.choice(asset_statuses),
                        location=random.choice(['Harare', 'Bulawayo', 'Mutare', 'Gweru', 'Masvingo']),
                        last_maintenance_date=date(2024, random.randint(1, 6), random.randint(1, 28)),
                        next_maintenance_date=date(2024, random.randint(7, 12), random.randint(1, 28)),
                        maintenance_notes='Regular maintenance required'
                    )
                    created['assets'] += 1
        
        logger.info(f"Sample data populated: {created}")
        
        return JsonResponse({
            'success': True,
            'message': 'Sample data populated successfully',
            'created': created
        })
        
    except Exception as e:
        logger.error(f"Error populating sample data: {str(e)}")
        return JsonResponse({
            'success': False,
            'message': f'Error: {str(e)}'
        }, status=500)


@login_required
def clear_sample_data(request):
    """Clear all sample data (use with caution)"""
    
    if not request.user.is_superuser and request.user.user_type != 'admin':
        return JsonResponse({'success': False, 'message': 'Unauthorized'}, status=403)
    
    try:
        deleted = {
            'crop_seasons': CropSeason.objects.count(),
            'animals': Animal.objects.count(),
            'equipment': Equipment.objects.count(),
            'farms': Farm.objects.count(),
            'users': User.objects.filter(is_superuser=False).count(),
            'cooperatives': Cooperative.objects.count(),
        }
        
        CropSeason.objects.all().delete()
        Animal.objects.all().delete()
        Equipment.objects.all().delete()
        Farm.objects.all().delete()
        User.objects.filter(is_superuser=False).delete()
        Cooperative.objects.all().delete()
        
        logger.info(f"Sample data cleared: {deleted}")
        
        return JsonResponse({
            'success': True,
            'message': 'All sample data cleared',
            'deleted': deleted
        })
        
    except Exception as e:
        logger.error(f"Error clearing sample data: {str(e)}")
        return JsonResponse({
            'success': False,
            'message': f'Error: {str(e)}'
        }, status=500)
