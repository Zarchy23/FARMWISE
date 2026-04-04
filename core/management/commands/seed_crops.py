from django.core.management.base import BaseCommand
from core.models import CropType


class Command(BaseCommand):
    help = 'Seed initial crop types into the database'

    def handle(self, *args, **options):
        crops = [
            # Cereals
            {
                'name': 'Maize',
                'scientific_name': 'Zea mays',
                'category': 'cereal',
                'growing_days': 120,
                'water_requirement_mm': 500,
                'optimal_temp_min': 20,
                'optimal_temp_max': 30,
                'planting_distance_cm': 75,
                'seed_rate_kg_per_ha': 15,
                'expected_yield_kg_per_ha': 5000,
                'description': 'Major grain crop, versatile for food and animal feed'
            },
            {
                'name': 'Wheat',
                'scientific_name': 'Triticum aestivum',
                'category': 'cereal',
                'growing_days': 140,
                'water_requirement_mm': 450,
                'optimal_temp_min': 15,
                'optimal_temp_max': 25,
                'planting_distance_cm': 20,
                'seed_rate_kg_per_ha': 80,
                'expected_yield_kg_per_ha': 4000,
                'description': 'Winter cereal crop, staple grain worldwide'
            },
            {
                'name': 'Rice',
                'scientific_name': 'Oryza sativa',
                'category': 'cereal',
                'growing_days': 130,
                'water_requirement_mm': 1200,
                'optimal_temp_min': 25,
                'optimal_temp_max': 35,
                'planting_distance_cm': 20,
                'seed_rate_kg_per_ha': 40,
                'expected_yield_kg_per_ha': 6000,
                'description': 'Primary staple crop, requires flooded paddies'
            },
            # Legumes
            {
                'name': 'Soybean',
                'scientific_name': 'Glycine max',
                'category': 'legume',
                'growing_days': 110,
                'water_requirement_mm': 450,
                'optimal_temp_min': 20,
                'optimal_temp_max': 30,
                'planting_distance_cm': 45,
                'seed_rate_kg_per_ha': 50,
                'expected_yield_kg_per_ha': 2000,
                'description': 'Protein-rich legume, rotational crop for soil improvement'
            },
            {
                'name': 'Beans',
                'scientific_name': 'Phaseolus vulgaris',
                'category': 'legume',
                'growing_days': 90,
                'water_requirement_mm': 400,
                'optimal_temp_min': 18,
                'optimal_temp_max': 28,
                'planting_distance_cm': 30,
                'seed_rate_kg_per_ha': 60,
                'expected_yield_kg_per_ha': 1500,
                'description': 'Common bean, nutritious legume'
            },
            {
                'name': 'Groundnut',
                'scientific_name': 'Arachis hypogaea',
                'category': 'legume',
                'growing_days': 120,
                'water_requirement_mm': 450,
                'optimal_temp_min': 20,
                'optimal_temp_max': 30,
                'planting_distance_cm': 30,
                'seed_rate_kg_per_ha': 80,
                'expected_yield_kg_per_ha': 1800,
                'description': 'Oil and protein crop, nitrogen-fixing legume'
            },
            # Vegetables
            {
                'name': 'Tomato',
                'scientific_name': 'Solanum lycopersicum',
                'category': 'vegetable',
                'growing_days': 75,
                'water_requirement_mm': 400,
                'optimal_temp_min': 22,
                'optimal_temp_max': 28,
                'planting_distance_cm': 60,
                'seed_rate_kg_per_ha': 0.3,
                'expected_yield_kg_per_ha': 25000,
                'description': 'High-value vegetable crop, market demand'
            },
            {
                'name': 'Cabbage',
                'scientific_name': 'Brassica oleracea',
                'category': 'vegetable',
                'growing_days': 90,
                'water_requirement_mm': 450,
                'optimal_temp_min': 15,
                'optimal_temp_max': 25,
                'planting_distance_cm': 45,
                'seed_rate_kg_per_ha': 0.3,
                'expected_yield_kg_per_ha': 30000,
                'description': 'Leafy vegetable, long storage life'
            },
            {
                'name': 'Onion',
                'scientific_name': 'Allium cepa',
                'category': 'vegetable',
                'growing_days': 120,
                'water_requirement_mm': 350,
                'optimal_temp_min': 15,
                'optimal_temp_max': 25,
                'planting_distance_cm': 15,
                'seed_rate_kg_per_ha': 4,
                'expected_yield_kg_per_ha': 20000,
                'description': 'Bulb crop, long shelf life, year-round demand'
            },
            {
                'name': 'Lettuce',
                'scientific_name': 'Lactuca sativa',
                'category': 'vegetable',
                'growing_days': 60,
                'water_requirement_mm': 350,
                'optimal_temp_min': 15,
                'optimal_temp_max': 20,
                'planting_distance_cm': 25,
                'seed_rate_kg_per_ha': 5,
                'expected_yield_kg_per_ha': 15000,
                'description': 'Leafy green, cool season crop'
            },
            {
                'name': 'Pepper',
                'scientific_name': 'Capsicum annuum',
                'category': 'vegetable',
                'growing_days': 90,
                'water_requirement_mm': 550,
                'optimal_temp_min': 22,
                'optimal_temp_max': 28,
                'planting_distance_cm': 50,
                'seed_rate_kg_per_ha': 0.2,
                'expected_yield_kg_per_ha': 15000,
                'description': 'Spice and vegetable crop, high market value'
            },
            # Tubers
            {
                'name': 'Potato',
                'scientific_name': 'Solanum tuberosum',
                'category': 'tuber',
                'growing_days': 90,
                'water_requirement_mm': 500,
                'optimal_temp_min': 15,
                'optimal_temp_max': 20,
                'planting_distance_cm': 30,
                'seed_rate_kg_per_ha': 1500,
                'expected_yield_kg_per_ha': 20000,
                'description': 'Staple tuber crop, short growing cycle'
            },
            {
                'name': 'Cassava',
                'scientific_name': 'Manihot esculenta',
                'category': 'tuber',
                'growing_days': 300,
                'water_requirement_mm': 800,
                'optimal_temp_min': 20,
                'optimal_temp_max': 30,
                'planting_distance_cm': 100,
                'seed_rate_kg_per_ha': 10,
                'expected_yield_kg_per_ha': 12000,
                'description': 'Root crop, drought tolerant, staple carbohydrate'
            },
            {
                'name': 'Sweet Potato',
                'scientific_name': 'Ipomoea batatas',
                'category': 'tuber',
                'growing_days': 120,
                'water_requirement_mm': 700,
                'optimal_temp_min': 20,
                'optimal_temp_max': 30,
                'planting_distance_cm': 30,
                'seed_rate_kg_per_ha': 8,
                'expected_yield_kg_per_ha': 15000,
                'description': 'Nutritious tuber, drought tolerant'
            },
            # Fruits
            {
                'name': 'Mango',
                'scientific_name': 'Mangifera indica',
                'category': 'fruit',
                'growing_days': 0,
                'water_requirement_mm': 900,
                'optimal_temp_min': 24,
                'optimal_temp_max': 30,
                'planting_distance_cm': 800,
                'seed_rate_kg_per_ha': None,
                'expected_yield_kg_per_ha': 3000,
                'description': 'Perennial fruit tree, high commercial value'
            },
            {
                'name': 'Banana',
                'scientific_name': 'Musa spp.',
                'category': 'fruit',
                'growing_days': 270,
                'water_requirement_mm': 1200,
                'optimal_temp_min': 22,
                'optimal_temp_max': 32,
                'planting_distance_cm': 300,
                'seed_rate_kg_per_ha': None,
                'expected_yield_kg_per_ha': 8000,
                'description': 'High-yielding fruit, year-round supply'
            },
            {
                'name': 'Citrus',
                'scientific_name': 'Citrus spp.',
                'category': 'fruit',
                'growing_days': 0,
                'water_requirement_mm': 800,
                'optimal_temp_min': 15,
                'optimal_temp_max': 25,
                'planting_distance_cm': 600,
                'seed_rate_kg_per_ha': None,
                'expected_yield_kg_per_ha': 2000,
                'description': 'Perennial citrus trees, nutritious fruit'
            },
            # Cash Crops
            {
                'name': 'Cotton',
                'scientific_name': 'Gossypium hirsutum',
                'category': 'cash',
                'growing_days': 180,
                'water_requirement_mm': 700,
                'optimal_temp_min': 20,
                'optimal_temp_max': 30,
                'planting_distance_cm': 90,
                'seed_rate_kg_per_ha': 15,
                'expected_yield_kg_per_ha': 1500,
                'description': 'Major cash crop, fiber production'
            },
            {
                'name': 'Coffee',
                'scientific_name': 'Coffea arabica',
                'category': 'cash',
                'growing_days': 0,
                'water_requirement_mm': 1500,
                'optimal_temp_min': 18,
                'optimal_temp_max': 24,
                'planting_distance_cm': 300,
                'seed_rate_kg_per_ha': None,
                'expected_yield_kg_per_ha': 1000,
                'description': 'Perennial cash crop, specialty beverage'
            },
            {
                'name': 'Tea',
                'scientific_name': 'Camellia sinensis',
                'category': 'cash',
                'growing_days': 0,
                'water_requirement_mm': 2000,
                'optimal_temp_min': 15,
                'optimal_temp_max': 25,
                'planting_distance_cm': 150,
                'seed_rate_kg_per_ha': None,
                'expected_yield_kg_per_ha': 2000,
                'description': 'Perennial plantation crop, global demand'
            },
            {
                'name': 'Sugarcane',
                'scientific_name': 'Saccharum officinarum',
                'category': 'cash',
                'growing_days': 360,
                'water_requirement_mm': 1500,
                'optimal_temp_min': 21,
                'optimal_temp_max': 30,
                'planting_distance_cm': 100,
                'seed_rate_kg_per_ha': 60,
                'expected_yield_kg_per_ha': 50000,
                'description': 'Industrial crop, sugar and biofuel production'
            },
            # Fodder
            {
                'name': 'Alfalfa',
                'scientific_name': 'Medicago sativa',
                'category': 'fodder',
                'growing_days': 0,
                'water_requirement_mm': 600,
                'optimal_temp_min': 15,
                'optimal_temp_max': 25,
                'planting_distance_cm': 15,
                'seed_rate_kg_per_ha': 15,
                'expected_yield_kg_per_ha': 8000,
                'description': 'Perennial forage, livestock feed'
            },
            {
                'name': 'Maize Fodder',
                'scientific_name': 'Zea mays',
                'category': 'fodder',
                'growing_days': 60,
                'water_requirement_mm': 400,
                'optimal_temp_min': 20,
                'optimal_temp_max': 30,
                'planting_distance_cm': 30,
                'seed_rate_kg_per_ha': 30,
                'expected_yield_kg_per_ha': 30000,
                'description': 'Green fodder for livestock, nutritious feed'
            },
        ]

        created_count = 0
        for crop_data in crops:
            crop, created = CropType.objects.get_or_create(
                name=crop_data['name'],
                defaults=crop_data
            )
            if created:
                created_count += 1

        self.stdout.write(
            self.style.SUCCESS(f'Successfully seeded {created_count} crop types')
        )
