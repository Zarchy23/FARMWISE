# core/management/commands/setup_offline_service.py
# Setup offline AI service with initial data

from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta
from core.services.offline_service import OfflineService
from core.models_offline import OfflinePreference
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Setup offline AI service for users'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--user',
            type=str,
            help='Specific user to setup (optional)',
        )
        parser.add_argument(
            '--cache-initial-data',
            action='store_true',
            help='Cache initial market and weather data'
        )
        parser.add_argument(
            '--enable-all',
            action='store_true',
            help='Enable all offline features for all users'
        )
    
    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Setting up Offline AI Service...\n'))
        
        if options['user']:
            users = User.objects.filter(username=options['user'])
            if not users.exists():
                self.stdout.write(self.style.ERROR(f'User {options["user"]} not found'))
                return
        else:
            users = User.objects.all()
        
        for user in users:
            try:
                self.setup_user_offline(user, options)
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'Error setting up {user.username}: {str(e)}'))
        
        self.stdout.write(self.style.SUCCESS('\n✓ Offline Service setup complete!'))
    
    def setup_user_offline(self, user: User, options: dict):
        """Setup offline service for a specific user"""
        
        # Create or update preference
        pref = OfflineService.get_or_create_preference(user)
        
        if options['enable_all']:
            pref.enable_offline_mode = True
            pref.enable_data_caching = True
            pref.enable_voice_offline = True
            pref.enable_chat_offline = True
            pref.enable_market_data_offline = True
            pref.background_sync_enabled = True
            pref.save()
            
            self.stdout.write(self.style.SUCCESS(f'✓ Enabled all offline features for {user.username}'))
        else:
            self.stdout.write(self.style.SUCCESS(f'✓ Initialized offline preferences for {user.username}'))
        
        # Display settings
        self.stdout.write(self.style.WARNING(f'\n  Offline Mode Enabled: {pref.enable_offline_mode}'))
        self.stdout.write(self.style.WARNING(f'  Cache Size: {pref.cache_size_mb}MB'))
        self.stdout.write(self.style.WARNING(f'  Sync Mode: {pref.get_sync_mode_display()}'))
        self.stdout.write(self.style.WARNING(f'  Cache Expiry: {pref.cache_expiry_hours}h'))
        self.stdout.write(self.style.WARNING(f'  Voice Offline: {pref.enable_voice_offline}'))
        self.stdout.write(self.style.WARNING(f'  Chat Offline: {pref.enable_chat_offline}'))
        self.stdout.write(self.style.WARNING(f'  Market Data Offline: {pref.enable_market_data_offline}'))
        
        if options['cache_initial_data']:
            self.cache_initial_data(user, pref)
    
    def cache_initial_data(self, user: User, pref: OfflinePreference):
        """Cache initial market and weather data"""
        self.stdout.write('\nCaching initial data...')
        
        try:
            # Cache sample commodity data
            sample_commodities = [
                {'commodity_name': 'Maize', 'category': 'Grains', 'price': 25, 'unit': 'kg'},
                {'commodity_name': 'Beans', 'category': 'Legumes', 'price': 45, 'unit': 'kg'},
                {'commodity_name': 'Tomatoes', 'category': 'Vegetables', 'price': 30, 'unit': 'kg'},
                {'commodity_name': 'Bananas', 'category': 'Fruits', 'price': 20, 'unit': 'bunch'},
                {'commodity_name': 'Onions', 'category': 'Vegetables', 'price': 35, 'unit': 'kg'},
            ]
            
            OfflineService.cache_market_prices(user, sample_commodities)
            self.stdout.write(self.style.SUCCESS(f'  ✓ Cached {len(sample_commodities)} commodities'))
            
            # Cache sample weather data
            from core.models import Farm
            farms = Farm.objects.filter(owner=user)[:3]
            
            if farms:
                for farm in farms:
                    for day in range(7):
                        weather_data = {
                            'date': (timezone.now() + timedelta(days=day)).date(),
                            'temperature': 20 + (day % 3),
                            'humidity': 60,
                            'rainfall': 0,
                            'wind_speed': 5,
                            'condition': ['sunny', 'cloudy', 'rainy'][day % 3]
                        }
                        OfflineService.cache_weather_data(user, weather_data, farm)
                
                self.stdout.write(self.style.SUCCESS(f'  ✓ Cached weather data for {len(farms)} farms'))
            
            # Display cache statistics
            stats = OfflineService.get_cache_statistics(user)
            self.stdout.write(self.style.WARNING(f'\nCache Statistics:'))
            self.stdout.write(self.style.WARNING(f'  Total Items: {stats["total_cached_items"]}'))
            self.stdout.write(self.style.WARNING(f'  Total Size: {stats["total_cache_size_mb"]}MB'))
            self.stdout.write(self.style.WARNING(f'  Pending Syncs: {stats["pending_syncs"]}'))
        
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error caching initial data: {str(e)}'))
