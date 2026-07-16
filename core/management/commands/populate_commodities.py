# core/management/commands/populate_commodities.py
# Management command to populate initial commodity data

from django.core.management.base import BaseCommand
from core.models_market import Commodity

class Command(BaseCommand):
    help = 'Populate initial commodity data for FarmWise market'
    
    def handle(self, *args, **options):
        commodities = [
            # Cereals
            {'name': 'Maize', 'category': 'grain', 'unit': 'kg', 'description': 'Corn/Maize crop'},
            {'name': 'Wheat', 'category': 'grain', 'unit': 'kg', 'description': 'Wheat grain'},
            {'name': 'Rice', 'category': 'grain', 'unit': 'kg', 'description': 'Rice grain'},
            {'name': 'Sorghum', 'category': 'grain', 'unit': 'kg', 'description': 'Sorghum grain'},
            {'name': 'Millet', 'category': 'grain', 'unit': 'kg', 'description': 'Millet grain'},
            
            # Legumes
            {'name': 'Beans', 'category': 'legume', 'unit': 'kg', 'description': 'Dried beans'},
            {'name': 'Peas', 'category': 'legume', 'unit': 'kg', 'description': 'Dried peas'},
            {'name': 'Lentils', 'category': 'legume', 'unit': 'kg', 'description': 'Lentils'},
            {'name': 'Chickpeas', 'category': 'legume', 'unit': 'kg', 'description': 'Chickpeas'},
            
            # Vegetables
            {'name': 'Tomatoes', 'category': 'vegetable', 'unit': 'kg', 'description': 'Fresh tomatoes'},
            {'name': 'Onions', 'category': 'vegetable', 'unit': 'kg', 'description': 'Onion bulbs'},
            {'name': 'Potatoes', 'category': 'vegetable', 'unit': 'kg', 'description': 'Potato tubers'},
            {'name': 'Cabbage', 'category': 'vegetable', 'unit': 'kg', 'description': 'Cabbage heads'},
            {'name': 'Carrots', 'category': 'vegetable', 'unit': 'kg', 'description': 'Carrot roots'},
            {'name': 'Spinach', 'category': 'vegetable', 'unit': 'kg', 'description': 'Spinach leaves'},
            {'name': 'Kale', 'category': 'vegetable', 'unit': 'kg', 'description': 'Kale leaves'},
            {'name': 'Peppers', 'category': 'vegetable', 'unit': 'kg', 'description': 'Bell peppers'},
            
            # Fruits
            {'name': 'Bananas', 'category': 'fruit', 'unit': 'kg', 'description': 'Banana bunch'},
            {'name': 'Oranges', 'category': 'fruit', 'unit': 'kg', 'description': 'Orange fruits'},
            {'name': 'Mangoes', 'category': 'fruit', 'unit': 'kg', 'description': 'Mango fruits'},
            {'name': 'Avocados', 'category': 'fruit', 'unit': 'kg', 'description': 'Avocado fruits'},
            {'name': 'Pineapples', 'category': 'fruit', 'unit': 'bunch', 'description': 'Pineapple bunch'},
            {'name': 'Watermelon', 'category': 'fruit', 'unit': 'kg', 'description': 'Watermelon'},
            {'name': 'Papaya', 'category': 'fruit', 'unit': 'kg', 'description': 'Papaya fruit'},
            
            # Root & Tuber
            {'name': 'Cassava', 'category': 'root_tuber', 'unit': 'kg', 'description': 'Cassava roots'},
            {'name': 'Sweet Potatoes', 'category': 'root_tuber', 'unit': 'kg', 'description': 'Sweet potato tubers'},
            {'name': 'Yams', 'category': 'root_tuber', 'unit': 'kg', 'description': 'Yam tubers'},
            {'name': 'Taro', 'category': 'root_tuber', 'unit': 'kg', 'description': 'Taro roots'},
            
            # Oilseeds
            {'name': 'Sunflower', 'category': 'oilseed', 'unit': 'kg', 'description': 'Sunflower seeds'},
            {'name': 'Soybeans', 'category': 'oilseed', 'unit': 'kg', 'description': 'Soybean seeds'},
            {'name': 'Sesame', 'category': 'oilseed', 'unit': 'kg', 'description': 'Sesame seeds'},
            {'name': 'Groundnuts', 'category': 'oilseed', 'unit': 'kg', 'description': 'Peanuts/Groundnuts'},
            
            # Spices
            {'name': 'Chili Peppers', 'category': 'spice', 'unit': 'kg', 'description': 'Dried chili peppers'},
            {'name': 'Garlic', 'category': 'spice', 'unit': 'kg', 'description': 'Garlic bulbs'},
            {'name': 'Ginger', 'category': 'spice', 'unit': 'kg', 'description': 'Ginger root'},
            {'name': 'Turmeric', 'category': 'spice', 'unit': 'kg', 'description': 'Turmeric root'},
            
            # Fiber Crops
            {'name': 'Cotton', 'category': 'fiber', 'unit': 'kg', 'description': 'Cotton fiber'},
            {'name': 'Sisal', 'category': 'fiber', 'unit': 'kg', 'description': 'Sisal fiber'},
        ]
        
        created_count = 0
        for commodity_data in commodities:
            commodity, created = Commodity.objects.get_or_create(
                name=commodity_data['name'],
                defaults={
                    'category': commodity_data['category'],
                    'unit': commodity_data['unit'],
                    'description': commodity_data['description'],
                }
            )
            if created:
                created_count += 1
                self.stdout.write(self.style.SUCCESS(f'Created: {commodity.name}'))
            else:
                self.stdout.write(self.style.WARNING(f'Already exists: {commodity.name}'))
        
        self.stdout.write(
            self.style.SUCCESS(f'\n✓ Successfully created {created_count} commodities!')
        )
