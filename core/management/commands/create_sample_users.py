"""
Management command to create sample users for all user types
Run: python manage.py create_sample_users
"""

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone

User = get_user_model()

class Command(BaseCommand):
    help = 'Create sample users for all user types'

    def handle(self, *args, **options):
        self.stdout.write('Creating sample users for all user types...')
        
        users_data = [
            # Farmers
            {
                'username': 'farmer_john',
                'email': 'john.smith@example.com',
                'password': 'Sample123!',
                'user_type': 'farmer',
                'first_name': 'John',
                'last_name': 'Smith',
                'phone_number': '+254711111111',
                'farm_name': 'Green Valley Farm'
            },
            {
                'username': 'farmer_mary',
                'email': 'mary.johnson@example.com',
                'password': 'Sample123!',
                'user_type': 'farmer',
                'first_name': 'Mary',
                'last_name': 'Johnson',
                'phone_number': '+254722222222',
                'farm_name': 'Sunrise Farm'
            },
            {
                'username': 'farmer_robert',
                'email': 'robert.williams@example.com',
                'password': 'Sample123!',
                'user_type': 'farmer',
                'first_name': 'Robert',
                'last_name': 'Williams',
                'phone_number': '+254733333333',
                'farm_name': 'Mountain View Farm'
            },
            {
                'username': 'farmer_sarah',
                'email': 'sarah.brown@example.com',
                'password': 'Sample123!',
                'user_type': 'farmer',
                'first_name': 'Sarah',
                'last_name': 'Brown',
                'phone_number': '+254744444444',
                'farm_name': 'Valley Farm'
            },
            # Large Farmers
            {
                'username': 'large_farm_co',
                'email': 'commercial@largefarm.co.zw',
                'password': 'Sample123!',
                'user_type': 'large_farmer',
                'first_name': 'Commercial',
                'last_name': 'Farms Ltd',
                'phone_number': '+254755555555',
                'farm_name': 'Commercial Farm Ltd'
            },
            {
                'username': 'agri_corp',
                'email': 'info@agricorp.co.zw',
                'password': 'Sample123!',
                'user_type': 'large_farmer',
                'first_name': 'Agri',
                'last_name': 'Corporation',
                'phone_number': '+254766666666',
                'farm_name': 'Agri Corporation'
            },
            # Cooperative Admins
            {
                'username': 'coop_admin_james',
                'email': 'james@zfu.co.zw',
                'password': 'Sample123!',
                'user_type': 'cooperative_admin',
                'first_name': 'James',
                'last_name': 'Moyo',
                'phone_number': '+254777777777',
                'farm_name': 'Zimbabwe Farmers Union'
            },
            {
                'username': 'coop_admin_grace',
                'email': 'grace@mashcoop.co.zw',
                'password': 'Sample123!',
                'user_type': 'cooperative_admin',
                'first_name': 'Grace',
                'last_name': 'Chikwinya',
                'phone_number': '+254788888888',
                'farm_name': 'Mashonaland Agricultural Cooperative'
            },
            # Agronomists
            {
                'username': 'agronomist_tom',
                'email': 'tom.murphy@example.com',
                'password': 'Sample123!',
                'user_type': 'agronomist',
                'first_name': 'Tom',
                'last_name': 'Murphy',
                'phone_number': '+254799999999',
            },
            {
                'username': 'agronomist_lisa',
                'email': 'lisa.davis@example.com',
                'password': 'Sample123!',
                'user_type': 'agronomist',
                'first_name': 'Lisa',
                'last_name': 'Davis',
                'phone_number': '+254710101010',
            },
            # Equipment Owners
            {
                'username': 'equipment_mike',
                'email': 'mike.taylor@example.com',
                'password': 'Sample123!',
                'user_type': 'equipment_owner',
                'first_name': 'Mike',
                'last_name': 'Taylor',
                'phone_number': '+254711212121',
                'farm_name': 'Taylor Equipment Services'
            },
            # Insurance Agents
            {
                'username': 'insurance_emma',
                'email': 'emma.wilson@example.com',
                'password': 'Sample123!',
                'user_type': 'insurance_agent',
                'first_name': 'Emma',
                'last_name': 'Wilson',
                'phone_number': '+254712323232',
            },
            # Market Traders
            {
                'username': 'trader_david',
                'email': 'david.martinez@example.com',
                'password': 'Sample123!',
                'user_type': 'market_trader',
                'first_name': 'David',
                'last_name': 'Martinez',
                'phone_number': '+254713434343',
            },
            # Veterinarians
            {
                'username': 'vet_jennifer',
                'email': 'jennifer.garcia@example.com',
                'password': 'Sample123!',
                'user_type': 'veterinarian',
                'first_name': 'Jennifer',
                'last_name': 'Garcia',
                'phone_number': '+254714545454',
            },
            # Lab Technicians
            {
                'username': 'lab_tech_kevin',
                'email': 'kevin.rodriguez@example.com',
                'password': 'Sample123!',
                'user_type': 'lab_technician',
                'first_name': 'Kevin',
                'last_name': 'Rodriguez',
                'phone_number': '+254715656565',
            },
            # Supermarkets
            {
                'username': 'supermarket_fresh',
                'email': 'orders@freshmart.co.zw',
                'password': 'Sample123!',
                'user_type': 'supermarket',
                'first_name': 'Fresh',
                'last_name': 'Mart',
                'phone_number': '+254716767676',
                'farm_name': 'Fresh Mart Supermarket'
            },
        ]
        
        created_count = 0
        for user_data in users_data:
            username = user_data['username']
            if not User.objects.filter(username=username).exists():
                user = User.objects.create_user(
                    username=username,
                    email=user_data['email'],
                    password=user_data['password'],
                    user_type=user_data['user_type'],
                    first_name=user_data.get('first_name', ''),
                    last_name=user_data.get('last_name', ''),
                    phone_number=user_data.get('phone_number', ''),
                    farm_name=user_data.get('farm_name', ''),
                    is_active=True,
                    is_verified=True
                )
                self.stdout.write(f'Created user: {user.username} ({user.get_user_type_display()})')
                created_count += 1
            else:
                self.stdout.write(f'User already exists: {username}')
        
        self.stdout.write(self.style.SUCCESS(f'Successfully created {created_count} sample users!'))
        self.stdout.write('All users have password: Sample123!')
