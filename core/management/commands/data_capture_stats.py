"""
Management command to check data capture statistics
Run: python manage.py data_capture_stats
"""

from django.core.management.base import BaseCommand
from django.db.models import Count
from core.models import User, Farm, CropSeason, Animal, Equipment, Cooperative

class Command(BaseCommand):
    help = 'Check current data capture statistics'

    def handle(self, *args, **options):
        self.stdout.write('=== DATA CAPTURE STATISTICS ===')
        self.stdout.write(f'Users: {User.objects.count()}')
        self.stdout.write(f'Farms: {Farm.objects.count()}')
        self.stdout.write(f'Cooperatives: {Cooperative.objects.count()}')
        self.stdout.write(f'Crop Seasons: {CropSeason.objects.count()}')
        self.stdout.write(f'Animals: {Animal.objects.count()}')
        self.stdout.write(f'Equipment: {Equipment.objects.count()}')
        
        self.stdout.write('\n=== USER TYPE BREAKDOWN ===')
        user_types = User.objects.values('user_type').annotate(count=Count('id')).order_by('-count')
        for item in user_types:
            self.stdout.write(f'{item["user_type"]}: {item["count"]}')
        
        self.stdout.write('\n=== FARM TYPE BREAKDOWN ===')
        farm_types = Farm.objects.values('farm_type').annotate(count=Count('id')).order_by('-count')
        for item in farm_types:
            self.stdout.write(f'{item["farm_type"]}: {item["count"]}')
        
        self.stdout.write('\n=== CROP STATUS BREAKDOWN ===')
        crop_statuses = CropSeason.objects.values('status').annotate(count=Count('id')).order_by('-count')
        for item in crop_statuses:
            self.stdout.write(f'{item["status"]}: {item["count"]}')
